import sps.quotes.client

class ConfigObject():
    """
    Provides default values for all possible keys in the configuration file
    """
    TRANSACTION_SERVER_PORT = 6000

    DATABASE_ARGS = {
        'drivername': 'mysql',
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'sps',
        'username': 'root',
        'password': 'root',
    }

    QUOTE_CLIENT = sps.quotes.client.RandomQuoteClient

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

