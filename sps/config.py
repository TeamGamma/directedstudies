from sps.quotes.client import RandomQuoteClient
from datetime import timedelta

class ConfigObject():
    """
    Provides default values for all possible keys in the configuration file
    """
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
        'echo': 'debug',
    }

    QUOTE_CLIENT = RandomQuoteClient()

    TRANSACTION_TIMEOUT = timedelta(seconds=60)


# The global configuration object
config = ConfigObject()


def read_config_file(filename):
    """
    Reads a Python configuration file and replaces attributes in the
    configuration. Returns the global ConfigObject.
    """
    global config
    execfile(filename, globals(), config.__dict__)
    return config

