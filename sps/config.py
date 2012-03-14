"""
Default configuration and related utilities for the entire system.

NOTE: You can't import ANYTHING from the rest of the codebase here
(e.g.  sps.*), or a circular dependency will be created.

"""
from datetime import timedelta

class ConfigObject():
    """
    Provides default values for all possible keys in the configuration file
    """
    TRANSACTION_SERVER_HOST = 'localhost'
    TRANSACTION_SERVER_PORT = 6000

    DATABASE_CONNECTION_ARGS = {
        'drivername': 'mysql',
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'sps',
        'username': 'root',
        'password': 'root',
    }
    DATABASE_ENGINE_ARGS = {
        'echo': False,
    }

    DATABASE_TABLE_ARGS = {
        'mysql_engine': 'InnoDB',
    }

    QUOTE_CLIENT = 'sps.quotes.client.RandomQuoteClient'

    TRANSACTION_TIMEOUT = timedelta(seconds=60)

    TEST_WITH_SQLITE = True

    DUMPLOG_DIR = '/tmp/'

    # Interval between trigger checks in seconds
    TRIGGER_INTERVAL = 3


# The global configuration object
config = ConfigObject()

def get_class_by_name(path):
    module_name, class_name = path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)

def read_config_file(filename):
    """
    Reads a Python configuration file and replaces attributes in the
    configuration. Returns the global ConfigObject.
    """
    global config
    execfile(filename, globals(), config.__dict__)
    return config

