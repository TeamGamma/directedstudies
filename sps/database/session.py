import MySQLdb
from eventlet.db_pool import ConnectionPool
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_URL = URL(
    'mysql',
    username='root', password='root',
    host='127.0.0.1', port=3306, database='sps'
)
_SESSION_MAKER = None

# Log all statements
SQLALCHEMY_ECHO = True


def setup_database(engine=None):
    global _SESSION_MAKER

    if not engine:
        # TODO: determine optimal pool size
        pool = ConnectionPool(MySQLdb, host=_URL.host,
                user=_URL.username, passwd=_URL.password, db=_URL.database)

        engine = create_engine(_URL,
            creator=pool.create,
            pool_size=pool.max_size,
            echo=SQLALCHEMY_ECHO
        )
    else:
        engine = engine

    _SESSION_MAKER = sessionmaker(bind=engine,
        autocommit=False,
        expire_on_commit=True)


def get_session():
    global _SESSION_MAKER

    if _SESSION_MAKER is None:
        setup_database()

    session = _SESSION_MAKER()

    # Force connection now to prevent later errors
    session.connection()

    return session
