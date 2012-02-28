from datetime import datetime, timedelta
from tests.utils import DatabaseTest
from sps.transactions import commands
from sps.database.models import User, Money, Transaction, StockPurchase
from sps.quotes.client import QuoteClient, DummyQuoteClient

class TestADDCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.ADDCommand()

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user', amount='100')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, 
                self.command.run, userid='unicorn', amount='100')

    def test_postcondition_add(self):
        self.command.run(userid='user', amount='100.60')
        user = self.session.query(User) \
            .filter_by(userid='user').first()
        self.assertEqual(user.account_balance.dollars, 100)
        self.assertEqual(user.account_balance.cents, 60)

    def test_postcondition_increment(self):
        self.command.run(userid='user2', amount='5.42')
        user = self.session.query(User) \
            .filter_by(userid='user2').first()
        self.assertEqual(user.account_balance.dollars, 105)
        self.assertEqual(user.account_balance.cents, 92)


class TestQUOTECommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.QUOTECommand()

        # Set the quote client to a dummy that returns predictable results
        QuoteClient.set_quote_client(DummyQuoteClient({
            'AAAA': Money(23, 45),
            'BBBB': Money(85, 39),
        }))

    def test_return_value(self):
        """ Should return a decimal value for the stock price """
        retval = self.command.run(userid='user', stock_symbol='AAAA')
        self.assertRegexpMatches(retval, '[0-9]+\.[0-9][0-9]')
        self.assertEqual(retval, '23.45')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, 
                self.command.run, userid='unicorn', stock_symbol='FOO')

    def test_validates_stock_symbol_len(self):
        """ Should return an error if the stock symbol is too long """
        self.assertRaises(commands.InvalidInputError, 
                self.command.run, userid='user', stock_symbol='A' * 5)


class TestCOMMIT_BUYCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.COMMIT_BUYCommand()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(user_id=2, stock_symbol='AAAA',
            operation='BUY', committed=False, quantity=2,
            stock_value=Money(10, 40))

        self.add_all(self.trans)

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user2')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, 
                self.command.run, userid='unicorn')

    def test_nonexistent_buy(self):
        """ Should return an error message if user has no transactions """
        self.assertRaises(commands.NoBuyTransactionError, 
                self.command.run, userid='user')

    def test_committed_buy(self):
        """ Should return an error message if user has only committed
        transactions """

        # Committed transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=True, quantity=1,
                stock_value=Money(10, 54))
        )
        self.assertRaises(commands.NoBuyTransactionError, 
                self.command.run, userid='user')

    def test_expired_transaction(self):
        """ Should return error message if user has no valid transactions """

        # Expired transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.assertRaises(commands.ExpiredBuyTransactionError, 
                self.command.run, userid='user')

    def test_sell_transaction_only(self):
        """ Should return error message if user has only SELL transactions """

        # SELL transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=False, quantity=1,
                stock_value=Money(10, 54)),
        )
        self.assertRaises(commands.NoBuyTransactionError, 
                self.command.run, userid='user')

    def test_postcondition_balance(self):
        """ User account balance should be decremented by the price
        of the stocks"""
        self.command.run(userid='user2')
        user = self.session.query(User) \
            .filter_by(userid='user2').first()
        # $100.50 - 2($10.40) = $79.70
        self.assertEqual(user.account_balance.dollars, 79)
        self.assertEqual(user.account_balance.cents, 70)

        self.assertEqual(self.trans.committed, True)

    def test_postcondition_stock(self):
        """ A single StockPurchase associated with the user should exist with
        the total quantity of the stock the user owns. """

        # Existing stock owned by user 2
        stock = StockPurchase(user_id=2, stock_symbol='AAAA', quantity=10)
        self.add_all(stock)

        self.command.run(userid='user2')
        stock = self.session.query(StockPurchase).filter_by(
                user_id=2, stock_symbol='AAAA').one()

        self.assertNotEqual(stock, None)
        # 10 original stocks + 2 new
        self.assertEqual(stock.quantity, 12, "Number of stocks is wrong")


class TestCOMMIT_SELLCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.COMMIT_SELLCommand()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(user_id=2, stock_symbol='AAAA',
            operation='SELL', committed=False, quantity=2,

            stock_value=Money(10, 40))

        # Existing stock owned by user 2
        self.stock = StockPurchase(user_id=2, stock_symbol='AAAA', quantity=10)

        self.session.add_all([self.trans, self.stock])
        self.session.commit()

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user2')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, 
                self.command.run, userid='unicorn')

    def test_nonexistent_sell(self):
        """ Should return an error message if user has no transactions """
        self.assertRaises(commands.NoSellTransactionError, 
                self.command.run, userid='user')

    def test_committed_sell(self):
        """ Should return an error message if user has only committed
        transactions """

        # Committed transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=True, quantity=1,
                stock_value=Money(10, 54))
        )
        self.assertRaises(commands.NoSellTransactionError, 
                self.command.run, userid='user')

    def test_expired_transaction(self):
        """ Should return error message if user has no valid transactions """

        # Expired transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.assertRaises(commands.ExpiredSellTransactionError, 
                self.command.run, userid='user')

    def test_buy_transaction_only(self):
        """ Should return error message if user has only SELL transactions """

        # SELL transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=False, quantity=1,
                stock_value=Money(10, 54)),
        )
        self.assertRaises(commands.NoSellTransactionError, 
                self.command.run, userid='user')

    def test_postcondition_balance(self):
        """ User account balance should be incremented by the price
        of the stocks"""
        self.command.run(userid='user2')
        user = self.session.query(User) \
            .filter_by(userid='user2').first()
        # $100.50 + 2($10.40) = $121.30
        self.assertEqual(user.account_balance.dollars, 121)
        self.assertEqual(user.account_balance.cents, 30)

        self.assertEqual(self.trans.committed, True)

    def test_postcondition_stock(self):
        """ A single StockPurchase associated with the user should exist with
        the total quantity of the stock the user owns. """

        self.command.run(userid='user2')
        stock = self.session.query(StockPurchase).filter_by(
                user_id=2, stock_symbol='AAAA').one()

        self.assertNotEqual(stock, None)
        # 10 original stocks - 2
        self.assertEqual(stock.quantity, 8)


class TestCANCEL_BUYCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.CANCEL_BUYCommand()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(user_id=2, stock_symbol='AAAA',
            operation='BUY', committed=False, quantity=2,
            stock_value=Money(10, 40))

        self.add_all(self.trans)

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user2')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, userid='unicorn')

    def test_nonexistent_buy(self):
        """ Should return an error message if user has no transactions """
        self.assertRaises(commands.NoBuyTransactionError,
                self.command.run, userid='user')

    def test_committed_buy(self):
        """ Should return an error message if user has only committed
        transactions """

        # Committed transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=True, quantity=1,
                stock_value=Money(10, 54))
        )
        self.assertRaises(commands.NoBuyTransactionError,
                self.command.run, userid='user')

    def test_expired_transaction(self):
        """ Should return error message if user has no valid transactions """

        # Expired transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.assertRaises(commands.ExpiredBuyTransactionError, 
                self.command.run, userid='user')

    def test_sell_transaction_only(self):
        """ Should return error message if user has only SELL transactions """

        # SELL transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=False, quantity=1,
                stock_value=Money(10, 54)),
        )
        self.assertRaises(commands.NoBuyTransactionError, 
                self.command.run, userid='user')

    def test_postcondition_remove(self):
        """ The BUY transaction should be removed from the database """
        self.command.run(userid='user2')

        # Assume there's no committed / expired transactions
        transaction = self.session.query(Transaction).first()
        self.assertEqual(transaction, None)


class TestCANCEL_SELLCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.CANCEL_SELLCommand()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(user_id=2, stock_symbol='AAAA',
            operation='SELL', committed=False, quantity=2,
            stock_value=Money(10, 40))

        self.add_all(self.trans)

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user2')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, userid='unicorn')

    def test_nonexistent_sell(self):
        """ Should return an error message if user has no transactions """
        self.assertRaises(commands.NoSellTransactionError,
                self.command.run, userid='user')

    def test_committed_sell(self):
        """ Should return an error message if user has only committed
        transactions """

        # Committed transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=True, quantity=1,
                stock_value=Money(10, 54))
        )
        self.assertRaises(commands.NoSellTransactionError,
                self.command.run, userid='user')

    def test_expired_transaction(self):
        """ Should return error message if user has no valid transactions """

        # Expired transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.assertRaises(commands.ExpiredSellTransactionError,
                self.command.run, userid='user')

    def test_buy_transaction_only(self):
        """ Should return error message if user has only BUY transactions """

        # BUY transaction record for user 1
        self.add_all(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=False, quantity=1,
                stock_value=Money(10, 54)),
        )
        self.assertRaises(commands.NoSellTransactionError,
                self.command.run, userid='user')

    def test_postcondition_remove(self):
        """ The SELL transaction should be removed from the database """
        self.command.run(userid='user2')

        # Assume there's no committed / expired transactions
        transaction = self.session.query(Transaction).first()
        self.assertEqual(transaction, None)

