import unittest
from tests.utils import DatabaseTest
from sps.transactions.commands import ADDCommand, QUOTECommand
from sps.database.models import User, Money
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


