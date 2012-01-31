import socket, sys

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

