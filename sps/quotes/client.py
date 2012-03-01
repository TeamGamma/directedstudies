from random import randrange
from sps.database.models import Money
from eventlet.green import socket

_QUOTE_CLIENT = None

def get_quote_client():
    """
    Returns the global quote client, creating it first if necessary.
    """
    global _QUOTE_CLIENT

    if not _QUOTE_CLIENT:
        from sps.config import config
        _QUOTE_CLIENT = config.QUOTE_CLIENT
    return _QUOTE_CLIENT


class RandomQuoteClient(object):
    def __init__(self, quote_min=0, quote_max=100):
        self.qmin = quote_min
        self.qmax = quote_max

    def get_quote(self, symbol, username):
        dollars, cents = randrange(self.qmin, self.qmax), randrange(0, 100)
        return Money(dollars, cents)


class DummyQuoteClient(object):
    def __init__(self, quote_map, default=Money(0, 0)):
        self.quote_map = quote_map
        self.default = default

    def get_quote(self, symbol, username):
        if symbol in self.quote_map:
            return self.quote_map[symbol]
        return self.default


class SENGQuoteClient(object):
    def __init__(self, address):
        self.address = address

    def get_quote(self, symbol, username):
        message = ','.join(symbol, username)

        # Create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket
        s.connect(self.address)
        # Send the user's query
        s.sendall(message)
        # Read and print up to 1k of data.
        data = s.recv(1024)

        # message format: "Quote, Stock Symbol, USER NAME, CryptoKey"
        # '58.17,APP,robodwye,1330546050315,ZcwKUqtHPq/PaprbZRKrFSw+zuIQiYA5XlEfLUkxkUIsWaN0xSiiWw==\n'
        quotes, symbol2, username2, cryptokey = data.split(',')

        quote = Money.from_string(quotes)
        return quote, cryptokey




if __name__ == '__main__':
    import socket
    import sys

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
