#!/usr/bin/env python

import sys
print >> sys.stderr, 'STARTED'

from sps.config import config
from sps.transactions.server import TransactionServer

def main():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", 
                      default=config.TRANSACTION_SERVER_PORT,
                      help="port to run server on", metavar="PORT")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      default=False,
                      help="Run server in debug mode (autoreload)")

    (opt, args) = parser.parse_args()
    print opt, args

    import logging
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('tserver')

    if(opt.debug):
        log.info('Debug mode enabled')
        from sps.utils.autoreload_eventlet import autoreload
        try:
            autoreload()
        except:
            exit(0)

    try:
        log.info('Starting transaction server on port %d' % opt.port)
        transaction_server = TransactionServer(('0.0.0.0', opt.port))
        transaction_server.start()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nInterrupted'
        exit(0)
    except Exception as e:
        log.error(e)
        exit(1)


if __name__ == '__main__':
    sys.exit(main())

