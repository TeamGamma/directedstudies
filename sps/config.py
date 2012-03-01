from sps.quotes.client import RandomQuoteClient

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
        'echo': True,
    }

    QUOTE_CLIENT = RandomQuoteClient()


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

