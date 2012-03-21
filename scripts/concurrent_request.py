"""
Spawn multiple client connections and collect their results.
"""
import eventlet
from eventlet.green import socket
from datetime import datetime

ADDRESS = ('localhost', 4444)
REQUEST_MSG = 'AAAA,user\n'
NUM_REQUESTS = 100

def request(address, message):
    c = socket.socket()
    c.connect(address)
    #print '%s connected' % (address,)
    c.sendall(message)
    return c.recv(1024)

pile = eventlet.GreenPile(NUM_REQUESTS * 2)

def load_test(num_requests):
    for i in range(num_requests):
        pile.spawn(request, ADDRESS, REQUEST_MSG)
        #print 'Spawned: %s' % (ADDRESS,)
    print 'Spawned %d requests' % num_requests

    start = datetime.now()
    for i, result in zip(range(num_requests), pile):
        #print '%d: %s' % (i, repr(result))
        pass
    elapsed = datetime.now() - start
    print 'Finished %d requests' % num_requests
    print 'Total time: %s' % elapsed

for i in range(10):
    load_test(NUM_REQUESTS)
