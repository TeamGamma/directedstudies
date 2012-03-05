import unittest2 as unittest
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sps.database.session import setup_database, get_session
from sps.database.models import Base, User, Money
from sps.config import config


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

            if config.TEST_WITH_SQLITE:
                # Create an in-memory sqlite database for fast testing
                DatabaseTest._TEST_ENGINE = create_engine('sqlite:///:memory:')
            else:
                # Test with real MySQL database for completeness (much slower)
                _URL = URL(**config.DATABASE_CONNECTION_ARGS)

                DatabaseTest._TEST_ENGINE = create_engine(
                    _URL,
                    **config.DATABASE_ENGINE_ARGS
                )

        setup_database(engine=self._TEST_ENGINE)
        self.session = get_session()

        # Re-create the tables before each test
        Base.metadata.drop_all(bind=self.session.connection(),
                checkfirst=True)
        Base.metadata.create_all(bind=self.session.connection(),
                checkfirst=False)

    def tearDown(self):
        # Drop the tables after each test to avoid sideaffects
        Base.metadata.drop_all(bind=self.session.connection(),
                checkfirst=False)
        self.session.close()

    def add_all(self, *objs):
        """ Adds one or more objects to the session and commits """
        for obj in objs:
            self.session.add(obj)
        self.session.commit()

    def _user_fixture(self):
        """ Inserts user rows into the test database """
        self.add_all(
            User(username='poor_user', password='password'),
            User(username='rich_user', password='password',
                account_balance=Money(100, 50), reserve_balance=Money(0, 0)),
        )




