import socket
import sys
from random import randrange
from sps.database.models import Money

_QUOTE_CLIENT = None

def get_quote_client():
    """
    Returns the global quote client, creating it first if necessary.
    """
    global _QUOTE_CLIENT

    if not _QUOTE_CLIENT:
        from sps.config import config
        _QUOTE_CLIENT = config.QUOTE_CLIENT()
    return _QUOTE_CLIENT


class RandomQuoteClient(object):
    stock_quote_max = 100

    def get_quote(self, symbol):
        dollars, cents = randrange(0, self.stock_quote_max), randrange(0, 100)
        return Money(dollars, cents)


class DummyQuoteClient(object):
    def __init__(self, quote_map, default=Money(0, 0)):
        self.quote_map = quote_map
        self.default = default

    def get_quote(self, symbol):
        if symbol in self.quote_map:
            return self.quote_map[symbol]
        return self.default


if __name__ == '__main__':
    # Print info for the user
    print("\nEnter: StockSYM, userid")
    print("  Invalid entry will return 'NA' for userid.")
    print("  Returns: quote,sym,userid,timestamp,cryptokey\n")

    # Get a line of text from the user
    fromUser = sys.stdin.readline()

    # Create the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket
    s.connect(('quoteserve.seng.uvic.ca', 4444))
    # Send the user's query
    s.send(fromUser)
    # Read and print up to 1k of data.
    data = s.recv(1024)
    print data
    # close the connection, and the socket
    s.close()
