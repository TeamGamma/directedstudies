#!/bin/bash

# Exit this script on error
set -e

sudo apt-get update

# Install ubuntu packages
sudo apt-get install --assume-yes build-essential python-pip python-dev python-mysqldb git-core sqlite3 nginx vim

# Install python packages
sudo pip install -r requirements.txt

