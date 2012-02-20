from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import composite
from collections import namedtuple

Base = declarative_base()

class Money(namedtuple('Money', 'dollars cents')):
    """ 
    Used to represent money in the system without floating point errors.
    Note: Money objects are immutable 
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
    """
    __slots__ = ()

    def __composite_values__(self):
        return (self[0], self[1])

    def __add__(self, money):
        return Money(self.dollars + money.dollars, self.cents + money.cents)

    def __sub__(self, money):
        return Money(self.dollars - money.dollars, self.cents - money.cents)

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



class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(String(50))
    password = Column(String(50))
    _account_balance_dollars = Column(Integer)
    _account_balance_cents = Column(Integer)
    _reserve_balance_dollars = Column(Integer)
    _reserve_balance_cents = Column(Integer)

    # Automatically convert between Money and dollars/cents columns
    account_balance = composite(Money, _account_balance_dollars, _account_balance_cents)
    reserve_balance = composite(Money, _reserve_balance_dollars, _reserve_balance_cents)

    def __init__(self, userid, password, account_balance=None, reserve_balance=None):
        self.userid = userid
        self.password = password
        if account_balance is None:
            account_balance = Money(0, 0)
        if reserve_balance is None:
            reserve_balance = Money(0, 0)
        self._account_balance_dollars = account_balance.dollars
        self._account_balance_cents = account_balance.cents
        self._reserve_balance_dollars = reserve_balance.dollars
        self._reserve_balance_cents = reserve_balance.cents

    def __repr__(self):
        return "<User('%s', balance=%s)>" % (self.userid, self.account_balance)


class Query(Base):
    __tablename__ = 'queries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    stock_symbol = Column(String(7))
    _stock_value_dollars = Column(Integer)
    _stock_value_cents = Column(Integer)
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    crypto_key = Column(String(50))
    _query_fee_dollars = Column(Integer)
    _query_fee_cents = Column(Integer)
    query_fee = composite(Money, _query_fee_dollars, _query_fee_cents)
    timestamp = Column(String(50))

    def __init__(self, user_id, stock_symbol, stock_value, crypto_key, query_fee, timestamp):
        self.user_id = user_id
        self.stock_symbol = stock_symbol
        self.stock_value = stock_value
        self.crypto_key = crypto_key
        self.query_fee = query_fee
        self.timestamp = timestamp


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    stock_symbol = Column(String(7))
    _stock_value_dollars = Column(Integer)
    _stock_value_cents = Column(Integer)
    operation = Column(String(3))
    quantity = Column(Integer)
    _broker_fee_dollars = Column(Integer)
    _broker_fee_cents = Column(Integer)
    broker_fee = composite(Money, _broker_fee_dollars, _broker_fee_cents)
    processing_time = Column(String(50))
    timestamp = Column(String(50))

    def __init__(self):
        pass



class SetTransaction(Base):
    __tablename__ = 'set_transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    stock_symbol = Column(String(7))
    _stock_value_dollars = Column(Integer)
    _stock_value_cents = Column(Integer)
    stock_value = composite(Money, _stock_value_dollars, _stock_value_cents)
    operation = Column(String(3))
    quantity = Column(Integer)
    _broker_fee_dollars = Column(Integer)
    _broker_fee_cents = Column(Integer)
    broker_fee = composite(Money, _broker_fee_dollars, _broker_fee_cents)
    processing_time = Column(String(50))
    query_times = Column(Integer)
    timestamp = Column(String(50))

    def __init__(self):
        pass

