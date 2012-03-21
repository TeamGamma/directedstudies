#!/usr/bin/env python

import sys

from sps.config import config, read_config_file
from sps.transactions.server import TransactionServer
from os.path import exists, normpath

def main():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      default=False,
                      help="Run server in debug mode (autoreload)")
    parser.add_option("-f", "--config-file", dest="config", 
                      default=config.CONFIG_FILE_PATH,
                      help="Path to configuration file", metavar="FILE")

    import logging
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('tserver')

    (opt, args) = parser.parse_args()
    log.debug(opt)
    log.debug(args)

    if exists(opt.config):
        log.info('Using config file "%s"', normpath(opt.config))
        read_config_file(opt.config)

    if(opt.debug):
        log.info('Debug mode enabled')
        from sps.utils.autoreload_eventlet import autoreload
        try:
            autoreload()
        except:
            exit(0)

    try:
        log.info('Starting transaction server on port %d' % config.TRANSACTION_SERVER_PORT)
        transaction_server = TransactionServer(('0.0.0.0', config.TRANSACTION_SERVER_PORT))
        transaction_server.start()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nInterrupted'
        exit(0)
    except Exception as e:
        log.error(e)
        exit(1)


if __name__ == '__main__':
    sys.exit(main())

