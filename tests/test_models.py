from tests.utils import unittest
from sps.database.models import User, Money


class TestUserAttributes(unittest.TestCase):
    def setUp(self):
        self.user = User(
            userid='user', password='pass',
            account_balance=Money(10, 50), reserve_balance=Money(20, 25)
        )

    def test_basic_attrs(self):
        self.assertEqual(self.user.userid, 'user')
        self.assertEqual(self.user.password, 'pass')
        self.assertEqual(self.user._account_balance_dollars, 10)
        self.assertEqual(self.user._account_balance_cents, 50)
        self.assertEqual(self.user._reserve_balance_dollars, 20)
        self.assertEqual(self.user._reserve_balance_cents, 25)

    def test_balance_get(self):
        account_balance = self.user.account_balance
        self.assertEqual(account_balance.dollars, 10)
        self.assertEqual(account_balance.cents, 50)

        reserve_balance = self.user.reserve_balance
        self.assertEqual(reserve_balance.dollars, 20)
        self.assertEqual(reserve_balance.cents, 25)

    def test_balance_set(self):
        self.user.reserve_balance = Money(dollars=56, cents=42)
        self.assertEqual(self.user.reserve_balance.dollars, 56)
        self.assertEqual(self.user.reserve_balance.cents, 42)

        self.user.account_balance = Money(dollars=88, cents=37)
        self.assertEqual(self.user.account_balance.dollars, 88)
        self.assertEqual(self.user.account_balance.cents, 37)
