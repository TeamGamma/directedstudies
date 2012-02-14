import socket, sys
from random import randrange
from sps.transactions.models import Money

class QuoteClient(object):
    """
    A client for requesting quotes from a stock quote server.
    """
    @staticmethod
    def str_to_money(money_str):
        """
        Converts the quote servers representation of money (e.g. "1.43") into a Money
        >>> money_str = "1.43"
        >>> money = QuoteClient.str_to_money(money_str)
        >>> money.dollars, money.cents
        (1, 43)
        """
        dollars, cents = map(int, money_str.split('.'))
        return Money(dollars, cents)

    @staticmethod
    def money_to_str(money):
        """
        Converts a Money object into the string representation used by the server
        >>> money = Money(dollars=45, cents=67)
        >>> QuoteClient.money_to_str(money)
        '45.67'
        """
        return '.'.join(map(str, money))



class RandomQuoteClient(QuoteClient):
    stock_quote_max = 100

    def get_quote(self, symbol):
        dollars, cents = randrange(0, self.stock_quote_max), randrange(0, 100)
        return Money(dollars, cents)



if __name__ == '__main__':
    # Print info for the user
    print("\nEnter: StockSYM, userid");
    print("  Invalid entry will return 'NA' for userid.");
    print("  Returns: quote,sym,userid,timestamp,cryptokey\n");

    # Get a line of text from the user
    fromUser = sys.stdin.readline();

    # Create the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket
    s.connect(('quoteserve.seng.uvic.ca',4444))
    # Send the user's query
    s.send(fromUser)
    # Read and print up to 1k of data.
    data = s.recv(1024)
    print data
    # close the connection, and the socket
    s.close()

