from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

# Used to represent money in the system without floating point errors
Money = namedtuple('Money', 'dollars cents')

class Client(Base):
    __tablename__ = 'Client'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    password = Column(String(50))
    account_balance = Column(Integer)
    reserve_balance = Column(Integer)

    def __init__(self, username, password, funds=0):
        self.username = username
        self.password = password
        self.account_balance = funds
	self.reserve_balance = 0

    def __repr__(self):
       return "<User('%s','%s', '%s')>" % (self.username, self.password)


class Query(Base):
    __tablename__ = 'Query Transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer)
    stock_symbol = Column(String(7))
    stock_value  = Column(Double)
    crypto_key   = Column(String(50))
    query_fee    = Column(Double)
    timestamp    = Column(String(50))

    def __init__(self):

    def __repr__(self):


class Transaction(Base):
    __tablename__ = 'Buy/Sell Transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer)
    stock_symbol = Column(String(7))
    stock_value  = Column(Double)
    operation    = Column(String(3))
    quantity     = Column(Integer)
    broker_fee   = Column(Double)
    processing_time = Column(String(50))
    timestamp    = Column(String(50))

    def __init__(self):

    def __repr__(self):


class SetTransaction(Base):
    __tablename__ = 'Set Buy/Sell Transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer)
    stock_symbol = Column(String(7))
    stock_value  = Column(Double)
    operation    = Column(String(3))
    quantity     = Column(Integer)
    broker_fee   = Column(Double)
    processing_time = Column(String(50))
    query_times  = Column(Integer)
    timestamp    = Column(String(50))

    def __init__(self):

    def __repr__(self):

