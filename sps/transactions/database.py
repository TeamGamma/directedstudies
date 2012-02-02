import MySQLdb
from eventlet.db_pool import ConnectionPool
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_URL = URL('mysql', username='root', password='root', host='127.0.0.1', port=3306, database='sps')
_SESSION_MAKER = None

def _get_session_maker():
    pool = ConnectionPool(MySQLdb, host=_URL.host, user=_URL.username, passwd=_URL.password, db=_URL.database)
    
    # TODO: customize engine
    engine = create_engine(_URL,
        creator=pool.create,
        pool_size=pool.max_size
    )

    # TODO: figure out actual values for options
    return sessionmaker(bind=engine,
        autocommit=True,
        expire_on_commit=True)

    

def get_session():
    global _SESSION_MAKER

    if _SESSION_MAKER is None:
        _SESSION_MAKER = _get_session_maker()

    session = _SESSION_MAKER()
    return session
    
