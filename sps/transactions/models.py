from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import composite
from collections import namedtuple

Base = declarative_base()

class Money(namedtuple('Money', 'dollars cents')):
    """ 
    Used to represent money in the system without floating point errors.
    Note: Money objects are immutable.

    >>> m1 = Money(dollars=10, cents=20)
    >>> m1.dollars, m1.cents
    (10, 20)

    >>> m2 = Money(10, 20)
    >>> m1 == m2
    True
    """
    __slots__ = ()

    def __composite_values__(self):
        return (self[0], self[1])


class Client(Base):
    __tablename__ = 'Client'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    password = Column(String(50))
    account_balance_dollars = Column(Integer)
    account_balance_cents = Column(Integer)
    reserve_balance_dollars = Column(Integer)
    reserve_balance_cents = Column(Integer)

    account_balance = composite(Money, account_balance_dollars, account_balance_cents)
    reserve_balance = composite(Money, reserve_balance_dollars, reserve_balance_cents)

    def __init__(self, username, password, account_balance, reserve_balance):
        self.username = username
        self.password = password
        self.account_balance_dollars = account_balance.dollars
        self.account_balance_cents = account_balance.cents
        self.reserve_balance_dollars = reserve_balance.dollars
        self.reserve_balance_cents = reserve_balance.cents

    def __repr__(self):
       return "<Client('%s', balance=%s)>" % (self.username, self.account_balance)


class Query(Base):
    __tablename__ = 'Query Transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer)
    stock_symbol = Column(String(7))
    stock_value  = Column(Float)
    crypto_key   = Column(String(50))
    query_fee    = Column(Float)
    timestamp    = Column(String(50))

    def __init__(self):
        pass


class Transaction(Base):
    __tablename__ = 'Buy/Sell Transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer)
    stock_symbol = Column(String(7))
    stock_value  = Column(Float)
    operation    = Column(String(3))
    quantity     = Column(Integer)
    broker_fee   = Column(Float)
    processing_time = Column(String(50))
    timestamp    = Column(String(50))

    def __init__(self):
        pass



class SetTransaction(Base):
    __tablename__ = 'Set Buy/Sell Transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer)
    stock_symbol = Column(String(7))
    stock_value  = Column(Float)
    operation    = Column(String(3))
    quantity     = Column(Integer)
    broker_fee   = Column(Float)
    processing_time = Column(String(50))
    query_times  = Column(Integer)
    timestamp    = Column(String(50))

    def __init__(self):
        pass

