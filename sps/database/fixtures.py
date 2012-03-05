from sps.database.session import get_session
from sps.database.models import Base, User, Money, Transaction

def create_tables(session=None):
    if session is None:
        session = get_session()
    Base.metadata.create_all(bind=session.connection(), checkfirst=True)

def drop_tables(session=None):
    if session is None:
        session = get_session()
    Base.metadata.drop_all(bind=session.connection(), checkfirst=True)

def users(session=None):
    """ Inserts user rows into the test database """
    if session is None:
        session = get_session()

    users = [
        User(username='poor_user', password='password'),
        User(username='rich_user', password='password',
            account_balance=Money(1000, 50), reserve_balance=Money(0, 0)),
    ]
    session.add_all(users)
    session.commit()
    return users

def buy_transaction_and_user(session=None):
    """
    Inserts a user and associated BUY transaction into the test database
    """
    if session is None:
        session = get_session()

    user = User(username='buy_transaction_and_user', password='password',
        account_balance=Money(100, 50), reserve_balance=Money(0, 0))
    trans = Transaction(user=user, stock_symbol='AAAA',
        operation='BUY', committed=False, quantity=2,
        stock_value=Money(10, 40))
    session.add_all((user, trans))
    session.commit()
    return user, trans

def sell_transaction_and_user(session=None):
    """
    Inserts a user and associated SELL transaction into the test database
    """
    if session is None:
        session = get_session()

    user = User(username='sell_transaction_and_user', password='password',
        account_balance=Money(100, 50), reserve_balance=Money(0, 0))
    trans = Transaction(user=user, stock_symbol='AAAA',
        operation='SELL', committed=False, quantity=2,
        stock_value=Money(10, 40))
    session.add_all((user, trans))
    session.commit()
    return user, trans

