from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    password = Column(String(50))
    funds = Column(Integer)

    def __init__(self, username, password, funds=0):
        self.username = username
        self.password = password
        self.funds = funds

    def __repr__(self):
       return "<User('%s','%s', '%s')>" % (self.username, self.password)

