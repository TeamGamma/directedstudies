from tests.utils import DatabaseTest
from sps.transactions.commands import ADDCommand, QUOTECommand
from sps.database.models import User

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

    def test_postconditions(self):
        self.command.run(userid='user', amount='100.60')
        user = self.session.query(User) \
            .filter_by(userid='user').first() 
        self.assertEqual(user.account_balance.dollars, 100)
        self.assertEqual(user.account_balance.cents, 60)


class TestQUOTECommand(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self._user_fixture()
        self.command = QUOTECommand()

    def test_return_value(self):
        """ Should return a decimal value for the stock price """
        retval = self.command.run(userid='user', stock_symbol='FOO')
        self.assertRegexpMatches(retval, '[0-9]+\.[0-9][0-9]')

    def test_nonexistent_user(self):
        """ Should return an error message if the user does not exist """
        retval = self.command.run(userid='unicorn', stock_symbol='FOO')
        self.assertEqual(retval, 'error: user does not exist\n')

