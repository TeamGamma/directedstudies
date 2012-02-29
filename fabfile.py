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

def tserver(port=6000, autoreload=True):
    """ Run transaction server in development mode """
    from sps.transactions.server import run_server
    run_server(int(port), autoreload)


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


def shell():
    """ Starts an IPython shell with a session and models imported """
    from sps.database.session import get_session
    from sps.database.models import *
    from sps.database import models
    session = get_session()
    Base.metadata.create_all(bind=session.connection(), checkfirst=True)
    from IPython import embed
    embed()

