"""
This file contains simple management and deployment commands used by the Fabric command-line tool.

To see all available commands, run `fab --list` in the same folder

To run a command, run `fab [command]`

"""

from fabric.api import *
from os import path
import sys

# Cluster servers will go here
env.hosts = []

# Add top-level package(s) to Python path
lib_path = path.abspath(path.dirname(__file__))
sys.path.insert(0, lib_path)


def transaction_server(port=6000):
    """ Run transaction server in development mode """
    from sps.transactions.server import run_server
    run_server(int(port))

