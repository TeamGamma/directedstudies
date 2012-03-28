import eventlet
from eventlet.green import socket
from random import randrange, paretovariate
from sps.database.models import Money
from datetime import datetime

_QUOTE_CLIENT = None

def get_quote_client():
    """
    Returns the global quote client, creating it first if necessary.
    """
    global _QUOTE_CLIENT

    if not _QUOTE_CLIENT:
        from sps.config import config, get_class_by_name
        if isinstance(config.QUOTE_CLIENT, str):
            _QUOTE_CLIENT = get_class_by_name(config.QUOTE_CLIENT)(**config.QUOTE_CLIENT_ARGS)
        else:
            _QUOTE_CLIENT = config.QUOTE_CLIENT

    return _QUOTE_CLIENT


class RandomQuoteClient(object):
    def __init__(self, delay_scale, delay_shape, quote_min, quote_max):
        self.delay_scale = delay_scale
        self.delay_shape = delay_shape
        self.qmin = quote_min
        self.qmax = quote_max

    def _quote_delay(self):
        return self.delay_scale * paretovariate(self.delay_shape) 

    def get_quote(self, symbol, username):
        delay = self._quote_delay()

        # Sleep for delay seconds to simulate legacy server
        eventlet.sleep(delay)

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
        message = ','.join((symbol, username)) + '\n'

        # Create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket
        s.connect(self.address)
        # Send the user's query
        s.sendall(message)
        # Read and print up to 1k of data.
        data = s.recv(1024).rstrip()

        # message format: "Quote, Stock Symbol, USER NAME, CryptoKey"
        # '58.17,APP,robodwye,1330546050315,ZcwKUqtHPq/PaprbZRKrFSw+zuIQiYA5XlEfLUkxkUIsWaN0xSiiWw==\n'
        quotes, symbol2, username2, timestamp, cryptokey = data.split(',')
        response_time = datetime.fromtimestamp(int(timestamp) / 1000)

        quote = Money.from_string(quotes)
        return quote, response_time, cryptokey



if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print 'usage: python %s stock_symbol username' % __file__
        exit(1)

    c = SENGQuoteClient(('quoteserve.seng.uvic.ca', 4444))
    for i in range(10):
        print c.get_quote(*sys.argv[1:])
