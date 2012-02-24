from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func, Column, Integer, String, DateTime
from sqlalchemy.orm import composite
from collections import namedtuple
from sps.database.utils import InitMixin, ReprMixin

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
Base = declarative_base()


class User(InitMixin, ReprMixin, Base):
    """
    A user of the system, with a primary and reserve account.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(String(50))
    password = Column(String(50))
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
    user_id = Column(Integer)
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH))
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    crypto_key = Column(String(50))
    query_fee = composite(Money, _query_fee_dollars, _query_fee_cents)

    # Auto-set timestamp when created
    query_time = Column(DateTime, default=func.now())



class Transaction(InitMixin, ReprMixin, Base):
    """
    A transaction record created by the BUY or SELL commands.
    """
    __tablename__ = 'transactions'

    _stock_value_dollars = Column(Integer, default=0)
    _stock_value_cents = Column(Integer, default=0)
    _broker_fee_dollars = Column(Integer, default=0)
    _broker_fee_cents = Column(Integer, default=0)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH))
    operation = Column(String(3))
    quantity = Column(Integer)
    broker_fee = composite(Money, _broker_fee_dollars, _broker_fee_cents)
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    processing_time = Column(String(50))

    # Auto-set timestamp when created
    creation_time = Column(DateTime, default=func.now())



class SetTransaction(InitMixin, ReprMixin, Base):
    """
    A transaction record for a trigger created by the SET_BUY_TRIGGER or
    SET_SELL_TRIGGER commands.
    """
    __tablename__ = 'set_transactions'

    BUY = 0
    SELL = 1

    _stock_value_dollars = Column(Integer, default=0)
    _stock_value_cents = Column(Integer, default=0)
    _broker_fee_dollars = Column(Integer, default=0)
    _broker_fee_cents = Column(Integer, default=0)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    stock_symbol = Column(String(STOCK_SYMBOL_LENGTH))
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    operation = Column(Integer)
    quantity = Column(Integer)
    broker_fee = composite(Money, _broker_fee_dollars, _broker_fee_cents)
    processing_time = Column(String(50))
    query_times = Column(Integer)

    # Auto-set timestamp when created
    creation_time = Column(DateTime, default=func.now())

