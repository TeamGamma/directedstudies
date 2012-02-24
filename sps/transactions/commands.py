"""
This file does stuff.


"""
from sps.database.session import get_session
from sps.database.models import User, Money, Transaction
from sps.quotes.client import QuoteClient
from datetime import datetime

class CommandError(Exception):
    pass


class UnknownCommandError(CommandError):
    pass


class InvalidCommandArgumentsError(CommandError):
    pass


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
    def run(self, userid, amount):
        session = get_session()
        user = session.query(User).filter_by(userid=userid).first()
        if not user:
            return 'error: user does not exist\n'
        amount = Money.from_string(amount)
        user.account_balance += amount
        session.commit()
        return 'success\n'


class QUOTECommand(CommandHandler):
    """
    Get the current quote for the stock for the specified user
    """
    def run(self, userid, stock_symbol):
        session = get_session()
        user = session.query(User).filter_by(userid=userid).first()
        if not user:
            return 'error: user does not exist\n'
        if len(stock_symbol) > 4:
            return 'error: invalid input\n'
        quote_client = QuoteClient.get_quote_client()
        quote = quote_client.get_quote(stock_symbol)
        return str(quote)


class BUYCommand(CommandHandler):
    """
    Buy the dollar amount of the stock for the specified user at the current
    price.
    """
    def run(self, userid, stock_symbol, amount):
        return 'success\n'


class COMMIT_BUYCommand(CommandHandler):
    """
    Commits the most recently executed BUY command
    """
    def run(self, userid):
        session = get_session()
        user = session.query(User).filter_by(userid=userid).first()
        if not user:
            return 'error: user does not exist\n'
        transaction = session.query(Transaction).filter_by(
            user_id=user.id, operation='BUY', committed=False
        ).first()
        if not transaction:
            return 'error: no BUY transaction is pending\n'

        if (datetime.now() - transaction.creation_time).total_seconds() > 60:
            return 'error: BUY transaction has expired\n'

        price = transaction.stock_value * transaction.quantity

        user.account_balance -= price
        transaction.committed = True
        session.commit()

        return 'success\n'


class CANCEL_BUYCommand(CommandHandler):
    """
    Cancels the most recently executed BUY Command
    """
    def run(self, userid):
        return 'success\n'


class SELLCommand(CommandHandler):
    """
    Sell the specified dollar mount of the stock currently held by the
    specified user at the current price.
    """
    def run(self, userid, stock_symbol, amount):
        return 'success\n'


class COMMIT_SELLCommand(CommandHandler):
    """
    Commits the most recently executed SELL command
    """
    def run(self, userid):
        return 'success\n'


class CANCEL_SELLCommand(CommandHandler):
    """
    Cancels the most recently executed SELL Command
    """
    def run(self, userid):
        return 'success\n'


class SET_BUY_AMOUNTCommand(CommandHandler):
    """
    Sets a defined amount of the given stock to buy when the current stock
    price is less than or equal to the BUY_TRIGGER
    """
    def run(self, userid, stock_symbol, amount):
        return 'success\n'


class CANCEL_SET_BUYCommand(CommandHandler):
    """
    Cancels a SET_BUY command issued for the given stock
    """
    def run(self, userid, stock_symbol):
        return 'success\n'


class SET_BUY_TRIGGERCommand(CommandHandler):
    """
    Sets the trigger point base on the current stock price when any SET_BUY
    will execute.
    """
    def run(self, userid, stock_symbol, amount):
        return 'success\n'


class SET_SELL_AMOUNTCommand(CommandHandler):
    """
    Sets a defined amount of the specified stock to sell when the current stock
    price is equal or greater than the sell trigger point
    """
    def run(self, userid, stock_symbol, amount):
        return 'success\n'


class SET_SELL_TRIGGERCommand(CommandHandler):
    """
    Sets the stock price trigger point for executing any SET_SELL triggers
    associated with the given stock and user
    """
    def run(self, userid, stock_symbol, amount):
        return 'success\n'


class CANCEL_SET_SELLCommand(CommandHandler):
    """
    Cancels the SET_SELL associated with the given stock and user
    """
    def run(self, userid, stock_symbol):
        return 'success\n'


class DUMPLOG_USERCommand(CommandHandler):
    """
    Print out the history of the users transactions to the user specified file
    """
    def run(self, userid, filename):
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
    def run(self, userid):
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

