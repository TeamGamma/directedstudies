#!/usr/bin/env python
"""
Command-line utility to run transaction server, etc.
"""

if __name__ == '__main__':
    from os import path
    import sys
    lib_path = path.abspath(path.dirname(__file__))
    sys.path.insert(0, lib_path)

    from sps.transactions.server import run as run_transaction_server
    run_transaction_server()


