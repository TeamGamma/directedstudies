from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy import func
from sqlalchemy.orm import relationship, backref, composite
from collections import namedtuple
from sps.database.utils import InitMixin, ReprMixin
from sps.config import config

# Maximum length of stock symbol string
STOCK_SYMBOL_LENGTH = 8

class Money(namedtuple('Money', 'dollars cents')):
    """
    Used to represent money in the system without floating point errors.
    Note: Money objects are immutable.
    (you can't assign dollars and cents directly)

    >>> m1 = Money(dollars=10, cents=20)
    >>> m1.dollars, m1.cents
    (10, 20)

    >>> m2 = Money(10, 20)
    >>> m1 == m2
    True

    >>> money = Money(dollars=45, cents=67)
    >>> str(money)
    '45.67'

    >>> money = Money(dollars=45, cents=0)
    >>> str(money)
    '45.00'

    >>> money_str = "1.43"
    >>> money = Money.from_string(money_str)
    >>> money.dollars, money.cents
    (1, 43)

    >>> money_str = "65"
    >>> money = Money.from_string(money_str)
    >>> money.dollars, money.cents
    (65, 0)

    >>> m = Money(1,90) + Money(3,20)
    >>> m.dollars, m.cents
    (5, 10)

    >>> m = Money(5,10) - Money(3,20)
    >>> m.dollars, m.cents
    (1, 90)

    >>> m = Money(3,30) * 4
    >>> m.dollars, m.cents
    (13, 20)
    """
    __slots__ = ()

    def __composite_values__(self):
        return (self[0], self[1])

    def __add__(self, money):
        cents = self.cents + money.cents
        return Money(self.dollars + money.dollars + cents / 100,
                cents % 100)

    def __sub__(self, money):
        cents = self.cents - money.cents
        if cents < 0:
            return Money(self.dollars - money.dollars + (cents / 100),
                cents % 100)
        return Money(self.dollars - money.dollars, cents % 100)

    def __mul__(self, scalar):
        cents = self.cents * scalar
        return Money(self.dollars * scalar + cents / 100, cents % 100)

    def __str__(self):
        """
        Converts a Money object into a string representation.
        """
        return "%d.%02d" % (self.dollars, self.cents)

    @staticmethod
    def from_string(money_str):
        """
        Converts the string representation of money (e.g. "1.43") into a Money
        """
        if '.' in money_str:
            dollars, cents = map(int, money_str.split('.'))
        else:
            dollars, cents = int(money_str), 0
        return Money(dollars, cents)


# Base class for all SQLAlchemy models
class Base(object):
    __table_args__ = config.DATABASE_TABLE_ARGS

Base = declarative_base(cls=Base)


class User(InitMixin, ReprMixin, Base):
    """
    A user of the system, with a primary and reserve account.
    """
    __tablename__ = 'users'

    username = Column(String(50), primary_key=True, nullable=False)
    password = Column(String(50), nullable=False)
    _account_balance_dollars = Column(Integer, default=0)
    _account_balance_cents = Column(Integer, default=0)
    _reserve_balance_dollars = Column(Integer, default=0)
    _reserve_balance_cents = Column(Integer, default=0)

    # Automatically convert between Money and dollars/cents columns
    account_balance = composite(Money,
            _account_balance_dollars, _account_balance_cents)
    reserve_balance = composite(Money,
            _reserve_balance_dollars, _reserve_balance_cents)



class Query(InitMixin, ReprMixin, Base):
    """
    The result of a query for a stock symbol at a given time.
    """
    __tablename__ = 'queries'

    _stock_value_dollars = Column(Integer, default=0)
    _stock_value_cents = Column(Integer, default=0)
    _query_fee_dollars = Column(Integer, default=0)
    _query_fee_cents = Column(Integer, default=0)

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), ForeignKey('users.username'), nullable=False)
    user = relationship("User", backref=backref('queries'))
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH), nullable=False)
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    query_fee = composite(Money, _query_fee_dollars, _query_fee_cents)
    crypto_key = Column(String(50), nullable=False)

    # Auto-set timestamp when created
    query_time = Column(DateTime, default=func.now())



class Transaction(InitMixin, ReprMixin, Base):
    """
    A transaction record created by the BUY or SELL commands.
    """
    __tablename__ = 'transactions'

    # Stock value is the value of a single stock, not the total
    _stock_value_dollars = Column(Integer, default=0)
    _stock_value_cents = Column(Integer, default=0)

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), ForeignKey('users.username'), nullable=False)
    user = relationship("User", backref=backref('transactions'))
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH), nullable=False)
    operation = Column(String(4), nullable=False)
    quantity = Column(Integer, nullable=False)
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    committed = Column(Boolean, nullable=False)

    # Auto-set timestamp when created
    creation_time = Column(DateTime, default=func.now())



class SetTransaction(InitMixin, ReprMixin, Base):
    """
    A transaction record for a trigger created by the SET_BUY_TRIGGER or
    SET_SELL_TRIGGER commands.
    """
    __tablename__ = 'set_transactions'

    # Trigger value to sell the stock at
    _trigger_value_dollars = Column(Integer, default=0)
    _trigger_value_cents = Column(Integer, default=0)

    # Dollar value of the stock to buy or sell
    _amount_dollars = Column(Integer, default=0)
    _amount_cents = Column(Integer, default=0)

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), ForeignKey('users.username'), nullable=False)
    user = relationship("User", backref=backref('set_transactions'))
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH), nullable=False)
    trigger_value = composite(Money, _trigger_value_dollars, _trigger_value_cents)
    amount = composite(Money, _amount_dollars, _amount_cents)
    quantity = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, nullable=False)
    operation = Column(String(3), nullable=False)

    # Auto-set timestamp when created
    creation_time = Column(DateTime, default=func.now())


class StockPurchase(InitMixin, ReprMixin, Base):
    """
    Represents the ownership of a quantity of a stock, identified by
    symbol, by a user.
    """
    __tablename__ = 'stock_purchases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), ForeignKey('users.username'), nullable=False)
    user = relationship("User", backref=backref('stock_purchases'))
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Auto-set timestamp when created
    query_time = Column(DateTime, default=func.now())

