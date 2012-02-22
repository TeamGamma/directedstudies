import unittest
from sqlalchemy import create_engine
from sps.database.session import setup_database, get_session
from sps.database.models import Base, User, Money


class DatabaseTest(unittest.TestCase):
    """
    Sets up an in-memory sqlite database connection and session.
    This will override any other use of sps.database.get_session to use the
    same connection.
    """
    _TEST_ENGINE = None

    def setUp(self):
        # Re-use the same test database for all tests using this class
        if DatabaseTest._TEST_ENGINE is None:
            DatabaseTest._TEST_ENGINE = create_engine('sqlite:///:memory:')

        setup_database(engine=self._TEST_ENGINE)
        self.session = get_session()

        # Re-create the tables before each test
        Base.metadata.create_all(bind=self.session.connection(), 
                checkfirst=False)

    def tearDown(self):
        # Drop the tables after each test to avoid sideaffects
        Base.metadata.drop_all(bind=self.session.connection(), 
                checkfirst=False)
        self.session.close()

    def _user_fixture(self): 
        """ Inserts user rows into the test database """ 
        self.session.add_all([
            User(userid='user', password='password'),
            User(userid='user2', password='password', 
                account_balance=Money(100, 50), reserve_balance=Money(0, 0)),
        ]) 
        self.session.commit()




