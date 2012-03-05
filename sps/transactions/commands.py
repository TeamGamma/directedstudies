"""
This file contains the implementations for all transaction server commands.
"""
from sps.database.session import get_session
from sps.database.models import User, Money, Transaction, StockPurchase
from sps.quotes.client import get_quote_client
from sps.config import config
from datetime import datetime

class CommandError(Exception):
    """
    An exception that holds both a message for the user and the original cause
    """
    user_message = 'error: System error'

    @property
    def message(self):
        return self.user_message

class InsufficientFundsError(CommandError):
    user_message = "error: insufficient funds\n"

class InsufficientStockError(CommandError):
    user_message = 'error: insufficient stock quantity\n'

class UnknownCommandError(CommandError):
    user_message = 'error: unknown command\n'

class UserNotFoundError(CommandError):
    user_message = 'error: unknown user\n'

class InvalidInputError(CommandError):
    user_message = 'error: invalid input\n'

class NoBuyTransactionError(CommandError):
    user_message = 'error: no BUY transaction is pending\n'

class NoSellTransactionError(CommandError):
    user_message = 'error: no SELL transaction is pending\n'

class ExpiredBuyTransactionError(CommandError):
    user_message = 'error: BUY transaction has expired\n'

class ExpiredSellTransactionError(CommandError):
    user_message = 'error: SELL transaction has expired\n'

class BuyTransactionActiveError(CommandError):
    user_message = 'error: a BUY transaction is already active\n'

class SellTransactionActiveError(CommandError):
    user_message = 'error: a SELL transaction is already active\n'

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
        return message + '\n'

CommandHandler.register_command('ECHO', EchoCommand)


class UppercaseCommand(CommandHandler):
    """
     Like ECHO, but returns the message in uppercase
    """
    def run(self, message):
        return message.upper() + '\n'

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
        return 'success\n'


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

        price = quantity * quote
        if user.account_balance < price:
            raise InsufficientFundsError()

        transaction = Transaction(user=user, quantity=quantity, operation='BUY', 
                stock_symbol='AAAA', stock_value=quote, committed=False)
        session.add(transaction)
        session.commit()
        return ','.join([str(quote), str(quantity), str(quote * quantity)])

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

        return 'success\n'


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

        if (datetime.now() - transaction.creation_time) > config.TRANSACTION_TIMEOUT:
            raise ExpiredBuyTransactionError(username)

        session.delete(transaction)
        session.commit()

        return 'success\n'


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

        # make transaction
        self.trans = Transaction(username=user.username, 
                stock_symbol=stock_symbol, operation='SELL', committed=False, 
                quantity=amount, stock_value=quoted_stock_value)

        # commit transaction after all actions for atomicity
        session.add(self.trans)
        session.commit()

        return 'success\n'


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

        return 'success\n'


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

        if (datetime.now() - transaction.creation_time) > config.TRANSACTION_TIMEOUT:
            raise ExpiredSellTransactionError(username)

        session.delete(transaction)
        session.commit()

        return 'success\n'


class SET_BUY_AMOUNTCommand(CommandHandler):
    """
    Sets a defined amount of the given stock to buy when the current stock
    price is less than or equal to the BUY_TRIGGER
    """
    def run(self, username, stock_symbol, amount):
        return 'success\n'


class CANCEL_SET_BUYCommand(CommandHandler):
    """
    Cancels a SET_BUY command issued for the given stock
    """
    def run(self, username, stock_symbol):
        return 'success\n'


class SET_BUY_TRIGGERCommand(CommandHandler):
    """
    Sets the trigger point base on the current stock price when any SET_BUY
    will execute.
    """
    def run(self, username, stock_symbol, amount):
        return 'success\n'


class SET_SELL_AMOUNTCommand(CommandHandler):
    """
    Sets a defined amount of the specified stock to sell when the current stock
    price is equal or greater than the sell trigger point
    """
    def run(self, username, stock_symbol, amount):
        return 'success\n'


class SET_SELL_TRIGGERCommand(CommandHandler):
    """
    Sets the stock price trigger point for executing any SET_SELL triggers
    associated with the given stock and user
    """
    def run(self, username, stock_symbol, amount):
        return 'success\n'


class CANCEL_SET_SELLCommand(CommandHandler):
    """
    Cancels the SET_SELL associated with the given stock and user
    """
    def run(self, username, stock_symbol):
        return 'success\n'


class DUMPLOG_USERCommand(CommandHandler):
    """
    Print out the history of the users transactions to the user specified file
    """
    def run(self, username, filename):
        return 'success\n'


class DUMPLOGCommand(CommandHandler):
    """
    Print out to the specified file the complete set of transactions that have
    occurred in the system.
    """
    def run(self, filename):
        return 'success\n'


class DISPLAY_SUMMARYCommand(CommandHandler):
    """
    Provides a summary to the client of the given user's transaction history
    and the current status of their accounts as well as any set buy or sell
    triggers and their parameters
    """
    def run(self, username):
        return 'success\n'


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

