"""
This file contains simple management and deployment commands used by the Fabric
command-line tool.

To see all available commands, run `fab --list` in the same folder

To run a command, run `fab [command]`

"""

from fabric.decorators import runs_once
from deployment.fabfile import * # NOQA

@runs_once
def create_tables():
    """ LOCAL: Creates all database tables. Will fail if tables already exist. """
    from sps.database.session import get_session
    from sps.database.models import Base
    session = get_session()
    Base.metadata.create_all(bind=session.connection(), checkfirst=False)


@runs_once
def drop_tables():
    """ LOCAL: Drops all database tables. Will fail if tables don't exist. """
    from sps.database.session import get_session
    from sps.database.models import Base
    session = get_session()

    # Drop all tables except user
    tables = Base.metadata.tables
    non_user_tables = [table for tablename, table in tables.items() if tablename != 'users']
    Base.metadata.drop_all(bind=session.connection(), checkfirst=False,
        tables=non_user_tables)

    # Now drop the user table
    Base.metadata.drop_all(bind=session.connection(), checkfirst=False)


@runs_once
def setup_database():
    """
    LOCAL: Recreates all tables and installs some example fixtures in the database
    """
    from sps.database import fixtures
    session = fixtures.get_session()

    fixtures.drop_tables(session)
    fixtures.create_tables(session)
    fixtures.users(session)
    #fixtures.buy_transaction_and_user(session)
    #fixtures.sell_transaction_and_user(session)


