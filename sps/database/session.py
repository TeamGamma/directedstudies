import eventlet.patcher
eventlet.patcher.monkey_patch()
import MySQLdb
from eventlet.db_pool import ConnectionPool
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sps.config import config
import logging

_URL = None
_SESSION_MAKER = None
_POOL = None

log = logging.getLogger('DB_SESSION')

def setup_database(engine=None):
    global _SESSION_MAKER, _URL, _POOL

    _URL = URL(**config.DATABASE_CONNECTION_ARGS)

    if not engine:
        # TODO: determine optimal pool size
        _POOL = ConnectionPool(MySQLdb, host=_URL.host,
                user=_URL.username, passwd=_URL.password, db=_URL.database)

        engine = create_engine(_URL,
            creator=_POOL.create,
            pool_size=_POOL.max_size,
            **config.DATABASE_ENGINE_ARGS)
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

