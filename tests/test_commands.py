import unittest
from datetime import datetime, timedelta
from tests.utils import DatabaseTest
from sps.transactions.commands import (
    ADDCommand, QUOTECommand, COMMIT_BUYCommand
)
from sps.database.models import User, Money, Transaction
from sps.quotes.client import QuoteClient, DummyQuoteClient

class TestADDCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = ADDCommand()

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user', amount='100')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        retval = self.command.run(userid='unicorn', amount='100')
        self.assertEqual(retval, 'error: user does not exist\n')

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
        self.command = QUOTECommand()

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
        retval = self.command.run(userid='unicorn', stock_symbol='FOO')
        self.assertEqual(retval, 'error: user does not exist\n')

    def test_validates_stock_symbol_len(self):
        """ Should return an error if the stock symbol is too long """
        retval = self.command.run(userid='user', stock_symbol='A' * 5)
        self.assertEqual(retval, 'error: invalid input\n')


class TestCOMMIT_BUYCommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = COMMIT_BUYCommand()

        # Uncommitted transaction record for user 2 ("user1")
        self.trans = Transaction(user_id=2, stock_symbol='AAAA',
            operation='BUY', committed=False, quantity=2,
            stock_value=Money(10, 40))

        self.session.add(self.trans)
        self.session.commit()

    def test_return_value(self):
        """ Should return "success" """
        retval = self.command.run(userid='user2')
        self.assertEqual(retval, 'success\n')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        retval = self.command.run(userid='unicorn')
        self.assertEqual(retval, 'error: user does not exist\n')

    def test_nonexistent_buy(self):
        """ Should return an error message if user has no transactions """
        retval = self.command.run(userid='user')
        self.assertEqual(retval, 'error: no BUY transaction is pending\n')

    def test_committed_buy(self):
        """ Should return an error message if user has only committed
        transactions """

        # Committed transaction record for user 1
        self.session.add(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=True, quantity=1,
                stock_value=Money(10, 54))
        )
        self.session.commit()
        retval = self.command.run(userid='user')
        self.assertEqual(retval, 'error: no BUY transaction is pending\n')

    def test_expired_transaction(self):
        """ Should return error message if user has no valid transactions """

        # Expired transaction record for user 1
        self.session.add(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='BUY', committed=False, quantity=1,
                stock_value=Money(10, 54),
                creation_time=datetime.now() - timedelta(seconds=61)),
        )
        self.session.commit()
        retval = self.command.run(userid='user')
        self.assertEqual(retval, 'error: BUY transaction has expired\n')

    def test_sell_transaction_only(self):
        """ Should return error message if user has only SELL transactions """

        # SELL transaction record for user 1
        self.session.add(
            Transaction(user_id=1, stock_symbol='AAAA',
                operation='SELL', committed=False, quantity=1,
                stock_value=Money(10, 54)),
        )
        self.session.commit()
        retval = self.command.run(userid='user')
        self.assertEqual(retval, 'error: no BUY transaction is pending\n')

    def test_postconditions(self):
        """ User account balance should be decremented by the price
        of the stocks"""
        self.command.run(userid='user2')
        user = self.session.query(User) \
            .filter_by(userid='user2').first()
        # $100.50 - 2($10.40) = $79.70
        self.assertEqual(user.account_balance.dollars, 79)
        self.assertEqual(user.account_balance.cents, 70)

        self.assertEqual(self.trans.committed, True)


