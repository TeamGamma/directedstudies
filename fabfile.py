"""
This file contains simple management and deployment commands used by the Fabric
command-line tool.

To see all available commands, run `fab --list` in the same folder

To run a command, run `fab [command]`

"""

from fabric.api import env, hosts
from os import path
import sys

# Cluster servers will go here
env.hosts = []

# Add top-level package(s) to Python path
lib_path = path.abspath(path.dirname(__file__))
sys.path.insert(0, lib_path)

# TODO: run from separate script files so that we can execute on the server
def create_tables():
    """ Creates all database tables. Will fail if tables already exist. """
    from sps.database.session import get_session
    from sps.database.models import Base
    session = get_session()
    Base.metadata.create_all(bind=session.connection(), checkfirst=False)


def drop_tables():
    """ Drops all database tables. Will fail if tables don't exist. """
    from sps.database.session import get_session
    from sps.database.models import Base
    session = get_session()
    Base.metadata.drop_all(bind=session.connection(), checkfirst=False)

def setup_database():
    """
    Recreates all tables and installs some example fixtures in the database
    """
    from sps.database import fixtures
    session = fixtures.get_session()

    fixtures.drop_tables(session)
    fixtures.create_tables(session)
    fixtures.users(session)
    fixtures.buy_transaction_and_user(session)
    fixtures.sell_transaction_and_user(session)


def shell():
    """ Starts an IPython shell with a session and models imported """
    from sps.database.session import get_session
    from sps.database.models import (
        Base, Money, User, Query, StockPurchase, Transaction, SetTransaction
    )
    from sps.database import models
    from sps.database import fixtures
    session = get_session()
    Base.metadata.create_all(bind=session.connection(), checkfirst=True)
    from IPython import embed
    embed()

