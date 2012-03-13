"""
This file contains the implementations for all transaction server commands.
"""
from sps.database.session import get_session
from sps.database.models import User, Money, Transaction, StockPurchase, SetTransaction
from sps.quotes.client import get_quote_client
from sps.transactions import xml
from sps.config import config
from datetime import datetime
from os import path

class CommandError(Exception):
    """
    An exception that holds both a message for the user and the original cause
    """
    user_message = 'System error'

    @property
    def message(self):
        return self.user_message

class InsufficientFundsError(CommandError):
    user_message = 'Insufficient funds'

class InsufficientStockError(CommandError):
    user_message = 'Insufficient stock quantity'

class UnknownCommandError(CommandError):
    user_message = 'Unknown command'

class UserNotFoundError(CommandError):
    user_message = 'Unknown user'

class InvalidInputError(CommandError):
    user_message = 'Invalid input'

class NoBuyTransactionError(CommandError):
    user_message = 'No BUY transaction is pending'

class NoSellTransactionError(CommandError):
    user_message = 'No SELL transaction is pending'

class ExpiredBuyTransactionError(CommandError):
    user_message = 'BUY transaction has expired'

class ExpiredSellTransactionError(CommandError):
    user_message = 'SELL transaction has expired'

class BuyTransactionActiveError(CommandError):
    user_message = 'A BUY transaction is already active'

class SellTransactionActiveError(CommandError):
    user_message = 'A SELL transaction is already active'

class CommandHandler(object):
    # Associates command labels (e.g. BUY) to subclasses of CommandHandler
    commands = {}

    @classmethod
    def get_handler(cls, label):
        """ Finds the CommandHandler associated with label """
        if label not in cls.commands:
            raise UnknownCommandError(label)

        return cls.commands[label]()

    @classmethod
    def register_command(cls, label, command):
        """
        Registers command with CommandHandler so it can be looked up by label
        """
        cls.commands[label] = command


###############################################################################

# Command Classes

###############################################################################

class EchoCommand(CommandHandler):
    """
     Echoes a single argument back to the client
    """
    def run(self, message):
        return message

CommandHandler.register_command('ECHO', EchoCommand)


class UppercaseCommand(CommandHandler):
    """
     Like ECHO, but returns the message in uppercase
    """
    def run(self, message):
        return message.upper()

CommandHandler.register_command('UPPER', UppercaseCommand)


class ADDCommand(CommandHandler):
    """
    Add the given amount of money to the user's account
    """
    def run(self, username, amount):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)
        amount = Money.from_string(amount)
        user.account_balance += amount
        session.commit()
        return xml.ResultResponse('success')


class QUOTECommand(CommandHandler):
    """
    Get the current quote for the stock for the specified user
    """
    def run(self, username, stock_symbol):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)
        if len(stock_symbol) > 4:
            raise InvalidInputError('stock symbol too long: %d' % \
                    len(stock_symbol))
        quote_client = get_quote_client()
        quote = quote_client.get_quote(stock_symbol, username)
        return str(quote)


class BUYCommand(CommandHandler):
    """
    Buy the dollar amount of the stock for the specified user at the current
    price.
    """
    def run(self, username, stock_symbol, amount):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        # Check for existing uncommitted transaction
        if session.query(Transaction).filter_by(
                user=user, operation='BUY', committed=False).count() > 0:
            raise BuyTransactionActiveError()

        # Getting stock quote
        quote_client = get_quote_client()
        quote = quote_client.get_quote(stock_symbol, username)

        # Work out quantity of stock to buy, fail if not enough for one stock
        amount = Money.from_string(amount)
        quantity = self.quantity(quote, amount)
        if quantity == 0:
            raise InsufficientFundsError()

        price = quote * quantity
        if user.account_balance < price:
            raise InsufficientFundsError()

        transaction = Transaction(user=user, quantity=quantity, operation='BUY', 
                stock_symbol=stock_symbol, stock_value=quote, committed=False)
        session.add(transaction)
        session.commit()

        return xml.QuoteResponse(quantity=quantity, price=price)

    def quantity(self, price, amount):
        q = 0
        while(True):
            amount = amount - price
            if (amount.dollars < 0) or (amount.cents < 0):
                break
            else:
                q += 1

        return q


class COMMIT_BUYCommand(CommandHandler):
    """
    Commits the most recently executed BUY command
    """
    def run(self, username):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)
        transaction = session.query(Transaction).filter_by(
            username=user.username, operation='BUY', committed=False
        ).first()
        if not transaction:
            raise NoBuyTransactionError(username)

        if (datetime.now() - transaction.creation_time) > config.TRANSACTION_TIMEOUT:
            session.delete(transaction)
            session.commit()
            raise ExpiredBuyTransactionError(username)

        price = transaction.stock_value * transaction.quantity

        user.account_balance -= price
        transaction.committed = True

        # create or update the StockPurchase for this stock symbol
        stock = session.query(StockPurchase).filter_by(
            user=user, stock_symbol=transaction.stock_symbol
        ).first()
        if not stock:
            stock = StockPurchase(user=user,
                    stock_symbol=transaction.stock_symbol,
                    quantity=transaction.quantity)
        else:
            stock.quantity = stock.quantity + transaction.quantity

        session.commit()

        return xml.ResultResponse('success')


class CANCEL_BUYCommand(CommandHandler):
    """
    Cancels the most recently executed BUY Command
    """
    def run(self, username):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)
        transaction = session.query(Transaction).filter_by(
            username=user.username, operation='BUY', committed=False
        ).first()
        if not transaction:
            raise NoBuyTransactionError(username)

        session.delete(transaction)
        session.commit()

        return xml.ResultResponse('success')


class SELLCommand(CommandHandler):
    """
    Sell the specified dollar amount of the stock currently held by the
    specified user at the current price.
    """
    def run(self, username, stock_symbol, amount):
        amount = int(amount)

        # see if user exists
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        # Check for existing uncommitted transaction
        if session.query(Transaction).filter_by(
                user=user, operation='SELL', committed=False).count() > 0:
            raise SellTransactionActiveError()

        # see if the user owns the requested stock and has enough for request
        records = session.query(StockPurchase).filter_by(
                username=user.username, stock_symbol=stock_symbol).all()

        if(len(records) > 1):
            raise UnknownCommandError('Multiple StockPurchase for user %s: %d', 
                    username, len(records))
        if len(records) != 1 or records[0].quantity < amount:
            raise InsufficientStockError()

        #set up client to get quote
        quote_client = get_quote_client()
        quoted_stock_value = quote_client.get_quote(stock_symbol, username) 
        price = quoted_stock_value * amount

        # make transaction
        self.trans = Transaction(username=user.username, 
                stock_symbol=stock_symbol, operation='SELL', committed=False, 
                quantity=amount, stock_value=quoted_stock_value)

        # commit transaction after all actions for atomicity
        session.add(self.trans)
        session.commit()

        return xml.QuoteResponse(quantity=amount, price=price)


class COMMIT_SELLCommand(CommandHandler):
    """
    Commits the most recently executed SELL command
    """
    def run(self, username):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)
        transaction = session.query(Transaction).filter_by(
            username=user.username, operation='SELL', committed=False
        ).first()
        if not transaction:
            raise NoSellTransactionError(username)

        if (datetime.now() - transaction.creation_time) > config.TRANSACTION_TIMEOUT:
            session.delete(transaction)
            session.commit()
            raise ExpiredSellTransactionError(username)

        price = transaction.stock_value * transaction.quantity

        user.account_balance += price

        # update the StockPurchase for this stock symbol
        stock = session.query(StockPurchase).filter_by(
            user=user, stock_symbol=transaction.stock_symbol
        ).one()
        stock.quantity = stock.quantity - transaction.quantity

        transaction.committed = True
        session.commit()

        return xml.ResultResponse('success')


class CANCEL_SELLCommand(CommandHandler):
    """
    Cancels the most recently executed SELL Command
    """
    def run(self, username):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        transaction = session.query(Transaction).filter_by(
            username=user.username, operation='SELL', committed=False
        ).first()
        if not transaction:
            raise NoSellTransactionError(username)

        session.delete(transaction)
        session.commit()

        return xml.ResultResponse('success')


class SET_BUY_AMOUNTCommand(CommandHandler):
    """
    Sets a defined amount of the given stock to buy when the current stock
    price is less than or equal to the BUY_TRIGGER
    """
    def run(self, username, stock_symbol, amount):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        # Work out quantity of stock to buy, fail if user has insufficient funds
        amount = Money.from_string(amount)
        if user.account_balance < amount:
            raise InsufficientFundsError()

        # Create inactive SetTransaction
        set_transaction = SetTransaction(user=user, amount=amount,
                operation='BUY', stock_symbol=stock_symbol, active=False)
        session.add(set_transaction)

        user.account_balance = user.account_balance - amount
        user.reserve_balance += amount

        session.commit()

        return xml.ResultResponse('success')



class SET_SELL_AMOUNTCommand(CommandHandler):
    """
    Sets a defined amount of the specified stock to sell when the current stock
    price is equal or greater than the sell trigger point
    """
    def run(self, username, stock_symbol, quantity):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        quantity = int(quantity)

        # see if the user owns the requested stock and has enough for request
        records = session.query(StockPurchase).filter_by(
                username=user.username, stock_symbol=stock_symbol).all()

        if(len(records) > 1):
            raise UnknownCommandError('Multiple StockPurchase for user %s: %d', 
                    username, len(records))
        if len(records) == 0 or records[0].quantity < quantity:
            raise InsufficientStockError()

        # Create inactive SetTransaction
        set_transaction = SetTransaction(user=user, quantity=quantity,
                operation='SELL', stock_symbol=stock_symbol, active=False)
        session.add(set_transaction)

        session.commit()

        return xml.ResultResponse('success')


class CANCEL_SET_BUYCommand(CommandHandler):
    """
    Cancels a SET_BUY command issued for the given stock
    """
    def run(self, username, stock_symbol):
        return xml.ResultResponse('success')


class SET_BUY_TRIGGERCommand(CommandHandler):
    """
    Sets the trigger point base on the current stock price when any SET_BUY
    will execute.
    """
    def run(self, username, stock_symbol, amount):
        return xml.ResultResponse('success')


class SET_SELL_TRIGGERCommand(CommandHandler):
    """
    Sets the stock price trigger point for executing any SET_SELL triggers
    associated with the given stock and user
    """
    def run(self, username, stock_symbol, amount):
        return xml.ResultResponse('success')


class CANCEL_SET_SELLCommand(CommandHandler):
    """
    Cancels the SET_SELL associated with the given stock and user
    """
    def run(self, username, stock_symbol):
        return xml.ResultResponse('success')


class DUMPLOG_USERCommand(CommandHandler):
    """
    Print out the history of the users transactions to the user specified file
    """
    def run(self, username, filename):
        return xml.ResultResponse('success')


class DISPLAY_SUMMARYCommand(CommandHandler):
    """
    Provides a summary to the client of the given user's transaction history
    and the current status of their accounts as well as any set buy or sell
    triggers and their parameters
    """
    def run(self, username):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        # Get this users transactions
        transactions = session.query(Transaction).filter_by(user=user).all()

        # Get this users triggers
        triggers = session.query(SetTransaction).filter_by(user=user).all()

        return xml.SummaryResponse(
            transactions=transactions, triggers=triggers,
            account_balance=user.account_balance,
            reserve_balance=user.reserve_balance)


class DUMPLOGCommand(CommandHandler):
    """
    Provides a summary to the client of the given user's transaction history
    and the current status of their accounts as well as any set buy or sell
    triggers and their parameters
    """
    def run(self, *args):
        if len(args) == 2:
            username, filename = args
            return self.dumplog_user(username, filename)
        elif len(args) == 1:
            filename = args[0]
            return self.dumplog_admin(filename)
        else:
            raise TypeError('Incorrect arguments for command DUMPLOG')

    def dumplog_user(self, username, filename):
        session = get_session()
        user = session.query(User).filter_by(username=username).first()
        if not user:
            raise UserNotFoundError(username)

        # Get this users transactions
        transactions = session.query(Transaction).filter_by(user=user).all()

        # Note: this is not secure against directory traversal
        full_path = path.join(config.DUMPLOG_DIR, filename)
        with open(full_path, 'w') as f:
            res = xml.DumplogResponse(transactions)
            f.write(str(res))

        return xml.ResultResponse('Wrote transactions to "%s"' % full_path)

    def dumplog_admin(self, filename):
        # TODO: implement security for admin dumplog

        session = get_session()
        transactions = session.query(Transaction).all()

        # Note: this is not secure against directory traversal
        full_path = path.join(config.DUMPLOG_DIR, filename)
        with open(full_path, 'w') as f:
            res = xml.DumplogResponse(transactions)
            f.write(str(res))

        return xml.ResultResponse('Wrote transactions to "%s"' % full_path)


CommandHandler.register_command('ADD', ADDCommand)
CommandHandler.register_command('QUOTE', QUOTECommand)
CommandHandler.register_command('BUY', BUYCommand)
CommandHandler.register_command('COMMIT_BUY', COMMIT_BUYCommand)
CommandHandler.register_command('CANCEL_BUY', CANCEL_BUYCommand)
CommandHandler.register_command('SELL', SELLCommand)
CommandHandler.register_command('COMMIT_SELL', COMMIT_SELLCommand)
CommandHandler.register_command('CANCEL_SELL', CANCEL_SELLCommand)
CommandHandler.register_command('SET_BUY_AMOUNT', SET_BUY_AMOUNTCommand)
CommandHandler.register_command('CANCEL_SET_BUY', CANCEL_SET_BUYCommand)
CommandHandler.register_command('SET_BUY_TRIGGER', SET_BUY_TRIGGERCommand)
CommandHandler.register_command('SET_SELL_AMOUNT', SET_SELL_AMOUNTCommand)
CommandHandler.register_command('SET_SELL_TRIGGER', SET_SELL_TRIGGERCommand)
CommandHandler.register_command('CANCEL_SET_SELL', CANCEL_SET_SELLCommand)
CommandHandler.register_command('DUMPLOG_USER', DUMPLOG_USERCommand)
CommandHandler.register_command('DUMPLOG', DUMPLOGCommand)
CommandHandler.register_command('DISPLAY_SUMMARY', DISPLAY_SUMMARYCommand)

