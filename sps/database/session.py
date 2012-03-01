import MySQLdb
from eventlet.db_pool import ConnectionPool
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sps.config import config

_SESSION_MAKER = None


def setup_database(engine=None):
    global _SESSION_MAKER, _URL

    _URL = URL(**config.DATABASE_CONNECTION_ARGS)

    if not engine:
        # TODO: determine optimal pool size
        pool = ConnectionPool(MySQLdb, host=_URL.host,
                user=_URL.username, passwd=_URL.password, db=_URL.database)

        engine = create_engine(_URL,
            creator=pool.create,
            pool_size=pool.max_size,
            **config.DATABASE_ENGINE_ARGS
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
