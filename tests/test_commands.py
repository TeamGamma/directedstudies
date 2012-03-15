from datetime import datetime, timedelta
from tests.utils import DatabaseTest
from sps.transactions import commands
from sps.database.models import User, Money, Transaction, StockPurchase, Trigger
from sps.transactions import xml
from sps.quotes import client

class TestADDCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.ADDCommand()

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(username='poor_user', amount='100')
        self.assertIsInstance(retval, xml.ResultResponse)
        self.assertEqual(retval.message, "success")

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, username='unicorn', amount='100')

    def test_postcondition_add(self):
        self.command.run(username='poor_user', amount='100.60')
        user = self.session.query(User) \
            .filter_by(username='poor_user').first()
        self.assertEqual(user.account_balance.dollars, 100)
        self.assertEqual(user.account_balance.cents, 60)

    def test_postcondition_increment(self):
        self.command.run(username='rich_user', amount='5.42')
        user = self.session.query(User) \
            .filter_by(username='rich_user').first()
        self.assertEqual(user.account_balance.dollars, 105)
        self.assertEqual(user.account_balance.cents, 92)


class TestBUYCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.BUYCommand()

        # Set the quote client to a dummy that returns predictable results
        client._QUOTE_CLIENT = client.DummyQuoteClient({
            'ABAB': Money(23, 45),
            'BBBB': Money(85, 39),
        })

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, username='unicorn', stock_symbol='ABAB',
                amount='30')

    def test_insufficient_funds(self):
        """ Should return an error message if insufficient funds for one stock """
        self.assertRaises(commands.InsufficientFundsError,
                self.command.run, username='poor_user', stock_symbol='ABAB',
                amount='2')

    def test_insufficient_user_funds(self):
        """ Should return an error message if insufficient account balance """
        self.assertRaises(commands.InsufficientFundsError,
                self.command.run, username='poor_user', stock_symbol='ABAB',
                amount='23.45')

    def test_return_value(self):
        """ Should return quoted stock value, quantity to be purchased, and
        total price """
        retval = self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='60')
        self.assertIsInstance(retval, xml.QuoteResponse)
        self.assertEqual(retval.quantity, 2)
        self.assertEqual(retval.price, Money(46, 90))

    def test_multiple_buy_transaction(self):
        """ Should return an error message if an uncommitted buy transaction
        already exists """
        self.add_all(
            Transaction(username='rich_user', stock_symbol='BBBB',
                operation='BUY', committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=30)),
        )
        self.assertRaises(commands.BuyTransactionActiveError,
                self.command.run, username='rich_user', stock_symbol='ABAB',
                amount='60')

    def test_no_multiple_buy_transaction(self):
        """ Should not return an error message if an committed buy transaction
        exists """
        self.add_all(
            Transaction(username='rich_user', stock_symbol='ABAB',
                operation='BUY', committed=True, quantity=2,
                stock_value=Money(23, 45),
                creation_time=datetime.now() - timedelta(seconds=30)),
        )
        self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='60')

    def test_postcondition_buy(self):
        """ Uncommitted Transaction is created """
        self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='23.45')
        transaction = self.session.query(Transaction).filter_by(
                username='rich_user',
                stock_symbol='ABAB', 
                committed=False,
                quantity=1,
                operation='BUY').first()
        self.assertNotEqual(transaction, None)

    def test_quantity_exact(self):
        quantity = commands.amount_to_quantity(Money(25, 60), Money(25, 60))
        self.assertEqual(quantity, 1)

    def test_quantity_multiple(self):
        quantity = commands.amount_to_quantity(Money(25, 60), Money(102, 40))
        self.assertEqual(quantity, 4)

    def test_quantity_less(self):
        quantity = commands.amount_to_quantity(Money(25, 60), Money(102, 30))
        self.assertEqual(quantity, 3)

    def test_quantity_more(self):
        quantity = commands.amount_to_quantity(Money(25, 60), Money(102, 50))
        self.assertEqual(quantity, 4)

    def test_quantity_less_than_one(self):
        quantity = commands.amount_to_quantity(Money(25, 60), Money(25, 40))
        self.assertEqual(quantity, 0)


class TestSELLCommand(DatabaseTest):      
    def setUp(self):
        # set up the database as inherited from DatabaseTest
        DatabaseTest.setUp(self)
        # call user fixture to populate the database (from DatabaseTest)
        self._user_fixture()
        #associate the sell command
        self.command = commands.SELLCommand()

        # Set the quote client to a dummy that returns predictable results
        client._QUOTE_CLIENT = client.DummyQuoteClient({
            'ABAB': Money(23, 45),
            'BBBB': Money(85, 39),
        })

        self.add_all(
            # Give 'rich_user' 10 units of 'ABAB' stock
            StockPurchase(username='rich_user', stock_symbol='ABAB', quantity=10),
        )


    def test_return_value(self):
        """ Should return quoted stock value, quantity to be purchased, and
        total price """
        retval = self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='2')
        self.assertIsInstance(retval, xml.QuoteResponse)
        self.assertEqual(retval.quantity, 2)
        self.assertEqual(retval.price, Money(46, 90))


    def test_too_little_stock_to_sell(self):
        """ tests to see if returns error when requested to sell too much"""
        self.assertRaises(commands.InsufficientStockError, self.command.run,
                username='rich_user', stock_symbol='ABAB', amount='100000')
        self.assertRaises(commands.InsufficientStockError, self.command.run,
                username='poor_user', stock_symbol='ABAB', amount='100000')

    def test_wrong_user_id(self):
        """ tests to see if we have the wrong user id """
        self.assertRaises(commands.UserNotFoundError, self.command.run,
                username='garbage', stock_symbol='ABAB', amount='5')

    def test_multiple_sell_transaction(self):
        """ Should return an error message if an uncommitted sell transaction
        already exists """
        self.add_all(
            Transaction(username='rich_user', stock_symbol='ABAB',
                operation='SELL', committed=False, quantity=8,
                stock_value=Money(23, 45),
                creation_time=datetime.now() - timedelta(seconds=30)),
        )
        self.assertRaises(commands.SellTransactionActiveError,
                self.command.run, username='rich_user', stock_symbol='ABAB',
                amount='5')

    def test_no_multiple_sell_transaction(self):
        """ Should not return an error message if an committed sell transaction
        exists """
        self.add_all(
            Transaction(username='rich_user', stock_symbol='ABAB',
                operation='SELL', committed=True, quantity=8,
                stock_value=Money(23, 45),
                creation_time=datetime.now() - timedelta(seconds=30)),
        )
        self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='5')

    def test_postcondition_sell(self):
        """ Uncommitted Transaction is created """
        self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='5')
        transaction = self.session.query(Transaction).filter_by(
                username='rich_user',
                stock_symbol='ABAB', 
                committed=False,
                quantity=5,
                operation='SELL').one()
        self.assertNotEqual(transaction, None)


class TestQUOTECommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.QUOTECommand()

    def test_return_value(self):
        """ Should return a decimal value for the stock price """
        retval = self.command.run(username='poor_user', stock_symbol='ABAB')
        self.assertRegexpMatches(retval, '[0-9]+\.[0-9][0-9]')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, 
                self.command.run, username='unicorn', stock_symbol='FOO')

    def test_validates_stock_symbol_len(self):
        """ Should return an error if the stock symbol is too long """
        self.assertRaises(commands.InvalidInputError, 
                self.command.run, username='poor_user', stock_symbol='A' * 5)


class _TransactionCommandTest(object):
    """
    The base test case for any of the four transaction commands:
    COMMIT_BUY, COMMIT_SELL, CANCEL_BUY, CANCEL_SELL

    These tests are all shared by TestCOMMIT_BUYCommand,
    TestCOMMIT_SELLCommand, TestCANCEL_BUYCommand, and TestCANCEL_SELLCommand
    """
    command = None  # The command class to run
    operation = None  # 'BUY' or 'SELL'
    missing_exception = None  # e.g. NoBuyTransactionError
    expired_exception = None  # e.g. ExpiredBuyTransactionError
    transaction_type = Transaction

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(username='rich_user')
        self.assertIsInstance(retval, xml.ResultResponse)
        self.assertEqual(retval.message, "success")

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, username='unicorn')

    def test_nonexistent_transaction(self):
        """ Should return an error message if user has no transactions """
        self.assertRaises(self.missing_exception,
                self.command.run, username='poor_user')

    def test_committed_transaction(self):
        """ Should return an error message if user has only committed
        transactions """

        # Committed transaction record for user 1
        self.add_all(
            self.transaction_type(username='poor_user', stock_symbol='ABAB',
                operation=self.operation, committed=True, quantity=1,
                stock_value=Money(10, 54))
        )
        self.assertRaises(self.missing_exception,
                self.command.run, username='poor_user')

    def test_expired_transaction_remove(self):
        """ Should delete the transaction if user's transaction has expired """

        # Expired transaction record for user 1
        trans = self.transaction_type(username='poor_user', stock_symbol='ABAB',
            operation=self.operation, committed=False, quantity=1,
            stock_value=Money(10, 54),
            creation_time=datetime.now() - timedelta(seconds=61))
        self.add_all(trans)
        trans_id = trans.id

        try:
            self.command.run(username='poor_user')
        except self.expired_exception:
            pass
        count = self.session.query(self.transaction_type).filter_by(id=trans_id).count()
        self.assertEqual(count, 0, "Expired transaction not removed")

    def test_other_transaction_only(self):
        """ Should return error message if user has only the other type of
        transaction """
        other = {'BUY': 'SELL', 'SELL': 'BUY'}[self.operation]

        # other transaction record for user 1
        self.add_all(
            self.transaction_type(username='poor_user', stock_symbol='ABAB',
                operation=other, committed=False, quantity=1,
                stock_value=Money(10, 54)),
        )
        self.assertRaises(self.missing_exception,
                self.command.run, username='poor_user')


class TestCOMMIT_BUYCommand(_TransactionCommandTest, DatabaseTest):
    command = commands.COMMIT_BUYCommand()
    operation = 'BUY'
    missing_exception = commands.NoBuyTransactionError
    expired_exception = commands.ExpiredBuyTransactionError

    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.transaction = Transaction(username='rich_user', stock_symbol='ABAB',
            operation='BUY', committed=False, quantity=2,
            stock_value=Money(10, 40))
        self.add_all(self.transaction)

    def test_postcondition_balance(self):
        """ User account balance should be decremented by the price
        of the stocks"""
        self.command.run(username='rich_user')
        user = self.session.query(User) \
            .filter_by(username='rich_user').first()
        # $100.50 - 2($10.40) = $79.70
        self.assertEqual(user.account_balance.dollars, 79)
        self.assertEqual(user.account_balance.cents, 70)

        self.assertEqual(self.transaction.committed, True)

    def test_postcondition_stock(self):
        """ A single StockPurchase associated with the user should exist with
        the total quantity of the stock the user owns. """

        # Existing stock owned by user 2
        stock = StockPurchase(username='rich_user', stock_symbol='ABAB', quantity=10)
        self.add_all(stock)

        self.command.run(username='rich_user')
        stock = self.session.query(StockPurchase).filter_by(
                username='rich_user', stock_symbol='ABAB').one()

        self.assertNotEqual(stock, None)
        # 10 original stocks + 2 new
        self.assertEqual(stock.quantity, 12, "Number of stocks is wrong")

    def test_expired_transaction(self):
        """ Should return error message if user's transaction has expired """

        # Expired transaction record for user 1
        self.add_all(
            Transaction(username='poor_user', stock_symbol='ABAB',
                operation=self.operation, committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.assertRaises(self.expired_exception,
                self.command.run, username='poor_user')



class TestCOMMIT_SELLCommand(_TransactionCommandTest, DatabaseTest):
    command = commands.COMMIT_SELLCommand()
    operation = 'SELL'
    missing_exception = commands.NoSellTransactionError
    expired_exception = commands.ExpiredSellTransactionError

    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(username='rich_user', stock_symbol='ABAB',
            operation='SELL', committed=False, quantity=2,
            stock_value=Money(10, 40))

        # Existing stock owned by user 2
        self.stock = StockPurchase(username='rich_user', stock_symbol='ABAB', quantity=10)

        self.session.add_all([self.trans, self.stock])
        self.session.commit()

    def test_postcondition_balance(self):
        """ User account balance should be incremented by the price
        of the stocks"""
        self.command.run(username='rich_user')
        user = self.session.query(User) \
            .filter_by(username='rich_user').first()
        # $100.50 + 2($10.40) = $121.30
        self.assertEqual(user.account_balance.dollars, 121)
        self.assertEqual(user.account_balance.cents, 30)

        self.assertEqual(self.trans.committed, True)

    def test_postcondition_stock(self):
        """ A single StockPurchase associated with the user should exist with
        the total quantity of the stock the user owns. """

        self.command.run(username='rich_user')
        stock = self.session.query(StockPurchase).filter_by(
                username='rich_user', stock_symbol='ABAB').one()

        self.assertNotEqual(stock, None)
        # 10 original stocks - 2
        self.assertEqual(stock.quantity, 8)

    def test_expired_transaction(self):
        """ Should return error message if user's transaction has expired """

        # Expired transaction record for user 1
        self.add_all(
            Transaction(username='poor_user', stock_symbol='ABAB',
                operation=self.operation, committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.assertRaises(self.expired_exception,
                self.command.run, username='poor_user')


class TestCANCEL_BUYCommand(_TransactionCommandTest, DatabaseTest):
    command = commands.CANCEL_BUYCommand()
    operation = 'BUY'
    missing_exception = commands.NoBuyTransactionError
    expired_exception = commands.ExpiredBuyTransactionError

    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(username='rich_user', stock_symbol='ABAB',
            operation='BUY', committed=False, quantity=2,
            stock_value=Money(10, 40))

        self.add_all(self.trans)

    def test_postcondition_remove(self):
        """ The BUY transaction should be removed from the database """
        self.command.run(username='rich_user')

        # Assume there's no committed / expired transactions
        transaction = self.session.query(Transaction).first()
        self.assertEqual(transaction, None)


class TestCANCEL_SELLCommand(_TransactionCommandTest, DatabaseTest):
    command = commands.CANCEL_SELLCommand()
    operation = 'SELL'
    missing_exception = commands.NoSellTransactionError
    expired_exception = commands.ExpiredSellTransactionError

    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(username='rich_user', stock_symbol='ABAB',
            operation='SELL', committed=False, quantity=2,
            stock_value=Money(10, 40))

        self.add_all(self.trans)

    def test_postcondition_remove(self):
        """ The SELL transaction should be removed from the database """
        self.command.run(username='rich_user')

        # Assume there's no committed / expired transactions
        transaction = self.session.query(Transaction).first()
        self.assertEqual(transaction, None)



class TestSET_BUY_AMOUNTCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = commands.SET_BUY_AMOUNTCommand()

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, username='unicorn', stock_symbol='ABAB',
                amount='30')

    def test_insufficient_user_funds(self):
        """ Should return an error message if insufficient account balance """
        self.assertRaises(commands.InsufficientFundsError,
                self.command.run, username='poor_user', stock_symbol='ABAB',
                amount='23.45')

    def test_return_value(self):
        """ Should return success """
        retval = self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='23.45')
        self.assertIsInstance(retval, xml.ResultResponse)
        self.assertEqual(retval.message, "success")

    def test_postcondition_transaction(self):
        """ Inactive Trigger is created with the given username,
        operation, stock, and amount """
        self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='23.45')
        set_transaction = self.session.query(Trigger).filter_by(
                username='rich_user',
                stock_symbol='ABAB', 
                state=Trigger.State.INACTIVE,
                operation='BUY').first()
        self.assertNotEqual(set_transaction, None)
        self.assertEqual(set_transaction.amount, Money(23, 45))

    def test_postcondition_reserve(self):
        """ The required amount is transferred to the user's reserve account """
        self.command.run(username='rich_user', stock_symbol='ABAB',
                amount='23.45')
        user = self.session.query(User) \
            .filter_by(username='rich_user').first()
        # $100.50 - 23.45 = $77.05
        self.assertEqual(user.account_balance, Money(77, 05))
        self.assertEqual(user.reserve_balance, Money(23, 45))



class TestSET_SELL_AMOUNT(DatabaseTest):      
    def setUp(self):
        # set up the database as inherited from DatabaseTest
        DatabaseTest.setUp(self)
        # call user fixture to populate the database (from DatabaseTest)
        self._user_fixture()
        #associate the sell command
        self.command = commands.SET_SELL_AMOUNTCommand()

        self.add_all(
            # Give 'rich_user' 10 units of 'ABAB' stock
            StockPurchase(username='rich_user', stock_symbol='ABAB', quantity=10),
        )

    def test_successful_return_value(self):
        """ tests to see if normal transaction returns success
            and check to see if the amounts are successfully modified"""
        retval = self.command.run(username='rich_user', stock_symbol='ABAB',
                quantity='1')
        self.assertIsInstance(retval, xml.ResultResponse)
        self.assertEqual(retval.message, "success")

    def test_too_little_stock_to_sell(self):
        """ tests to see if returns error when requested to sell too much"""
        self.assertRaises(commands.InsufficientStockError, self.command.run,
                username='rich_user', stock_symbol='ABAB', quantity='100000')
        self.assertRaises(commands.InsufficientStockError, self.command.run,
                username='poor_user', stock_symbol='ABAB', quantity='1')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, self.command.run, 
                username='garbage', stock_symbol='ABAB', quantity='1')

    def test_postcondition_transaction(self):
        """ Inactive Trigger is created with the given username,
        operation, stock, and quantity """
        self.command.run(username='rich_user', stock_symbol='ABAB',
                quantity='2')
        set_transaction = self.session.query(Trigger).filter_by(
                username='rich_user',
                stock_symbol='ABAB', 
                state=Trigger.State.INACTIVE,
                quantity=2,
                operation='SELL').first()
        self.assertNotEqual(set_transaction, None)


class TestCANCEL_SET_BUYCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.command = commands.CANCEL_SET_BUYCommand()

        self._user_fixture()

        # active BUY trigger for rich_user
        self.trans = Trigger(username='rich_user', stock_symbol='ABAB',
            operation='BUY', state=Trigger.State.INACTIVE)

        self.add_all(self.trans)

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, username='unicorn', stock_symbol='ABAB')

    def test_nonexistent_trigger(self):
        """ Should return an error message if user has no matching triggers """
        self.assertRaises(commands.NoTriggerError,
                self.command.run, username='poor_user', stock_symbol='ABAB')

    def test_sell_trigger_only(self):
        """ Should return an error message if user has no matching triggers """
        # active SELL trigger for poor_user
        self.add_all(Trigger(username='poor_user', stock_symbol='ABAB',
            operation='SELL', state=Trigger.State.INACTIVE))

        self.assertRaises(commands.NoTriggerError,
                self.command.run, username='poor_user', stock_symbol='ABAB')

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(username='rich_user', stock_symbol='ABAB')
        self.assertIsInstance(retval, xml.ResultResponse)
        self.assertEqual(retval.message, "trigger cancelled")

    def test_postcondition_cancelled(self):
        """ The BUY Trigger should be marked as cancelled """
        self.command.run(username='rich_user', stock_symbol='ABAB')

        transaction = self.session.query(Trigger).filter_by(
                state=Trigger.State.CANCELLED).first()
        self.assertNotEqual(transaction, None)
        self.assertEqual(transaction.state, Trigger.State.CANCELLED)


class TestCANCEL_SET_SELLCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.command = commands.CANCEL_SET_SELLCommand()

        self._user_fixture()

        # inactive transaction record for rich_user
        self.trans = Trigger(username='rich_user', stock_symbol='ABAB',
            operation='SELL', state=Trigger.State.INACTIVE, amount=Money(0, 0))

        self.add_all(self.trans)

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(username='rich_user', stock_symbol='ABAB')
        self.assertIsInstance(retval, xml.ResultResponse)
        self.assertEqual(retval.message, "trigger cancelled")

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError,
                self.command.run, username='unicorn', stock_symbol='ABAB')

    def test_nonexistent_trigger(self):
        """ Should return an error message if user has no matching triggers """
        self.assertRaises(commands.NoTriggerError,
                self.command.run, username='poor_user', stock_symbol='ABAB')

    def test_buy_trigger_only(self):
        """ Should return an error message if user has no matching triggers """
        # active BUY trigger for poor_user
        self.add_all(Trigger(username='poor_user', stock_symbol='ABAB',
            operation='BUY', state=Trigger.State.INACTIVE))

        self.assertRaises(commands.NoTriggerError,
                self.command.run, username='poor_user', stock_symbol='ABAB')

    def test_postcondition_remove(self):
        """ The SELL Trigger should be removed from the database """
        self.command.run(username='rich_user', stock_symbol='ABAB')

        # Assume there's no committed / expired transactions
        transaction = self.session.query(Trigger).first()
        self.assertEqual(transaction, None)




class TestDISPLAY_SUMMARY(DatabaseTest):      
    def setUp(self):
        # set up the database as inherited from DatabaseTest
        DatabaseTest.setUp(self)

        #associate the sell command
        self.command = commands.DISPLAY_SUMMARYCommand()

        self.user = User(username='a', password='', 
            account_balance=Money(10, 20), reserve_balance=Money(30, 40))
        self.add_all(
            self.user,
            Transaction(user=self.user, stock_symbol='AAAA', operation='BUY',
                committed=False, quantity=1, stock_value=Money(10, 54)),
            Transaction(user=self.user, stock_symbol='BBBB', operation='SELL',
                committed=True, quantity=1, stock_value=Money(10, 54)),
            Trigger(user=self.user, amount=Money(10, 54),
                    operation='BUY', stock_symbol='AAAA', state=Trigger.State.INACTIVE),
            Trigger(user=self.user, amount=Money(10, 54),
                    operation='BUY', stock_symbol='AAAA', state=Trigger.State.RUNNING),
        )

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        self.assertRaises(commands.UserNotFoundError, self.command.run, 
                username='garbage')

    def test_successful_return_value(self):
        """ Return value should be a SummaryResponse and should contain
        committed transactions, active triggers, and the correct
        account/reserve balances. """
        res = self.command.run(username='a')

        self.assertIsInstance(res, xml.SummaryResponse)
        self.assertEqual(len(res.transactions), 2)
        self.assertEqual(len(res.triggers), 2)
        self.assertEqual(res.account_balance, self.user.account_balance)
        self.assertEqual(res.reserve_balance, self.user.reserve_balance)



