""" 
This is the Fabric file to do the deployment on the remote server

You can type Fab Type Location Username to run it
Where Type == database, transaction, or web

The fabric file will set up and launch the appropriate server
"""

#The first thing we do is import the fabric libraries
from __future__ import with_statement
from fabric.api import env, hosts, settings
from fabric.operations import put, sudo, run
from fabric.context_managers import cd
from fabric.contrib.files import exists
from os import path
import sys

#setup remote servers
env.user = 'vagrant'
env.password = 'vagrant'
# add remote host addresses here
env.hosts = ['142.104.215.106:2222']

github_repo_address = 'git://github.com/TeamGamma/directedstudies.git'


def deploy(server_type='web'):
    
    #install all the goodies

    #update apt-cache library
    sudo('apt-get update')

    # ubuntu goodies
    sudo("""apt-get install --assume-yes build-essential python-pip python-dev python-mysqldb git-core sqlite3 apache2 libapache2-mod-wsgi python-mysqldb fabric""")

    #clone git repository
    sudo('mkdir -p /srv')

    with cd('/srv'):
        if not exists('directedstudies'):
            sudo('git clone %s directedstudies' % (github_repo_address))
        
        with cd('/srv/directedstudies/'):
            sudo('git pull')
        #python goodies
        sudo('pip install -r directedstudies/requirements.txt')
        sudo('pip install eventlet sql-alchemy')
    
    run('cd /srv/directedstudies')

    if server_type == 'web':
        #start the web server

        #configure apache for wsgi by copying the repo config to remote install
        sudo('cp /srv/directedstudies/deployment/config/apache/wsgi_configuration /etc/apache2/sites-available/')
        #create a link to the enabled directory
        sudo("""ln -s -f /etc/apache2/sites-available/wsgi_configuration /etc/apache2/sites-enabled/wsgi_configuration_link""")
       
        sudo("mkdir -p /srv/directedstudies/logs")
        
        #restart apache2 to configure
        result = sudo('service apache2 restart', pty=False)
       
    elif server_type == 'transaction':
        #configure our libraries to act as packages?
        with cd('/srv/directedstudies/'):
            sudo('python setup.py develop')
        
        #navigate to server and run it. nice and easy right?
        with cd('/srv/directedstudies/sps/transactions/'):
            sudo('python server.py')

    elif server_type == 'database':
        #start the database server
        sudo("""debconf-set-selections <<< 'mysql-server-5.1 mysql-server/root_password password root'""")
        sudo("""debconf-set-selections <<< 'mysql-server-5.1 mysql-server/root_password_again password root'""")
        sudo('apt-get -y install mysql-server')
        
        #Configure the database server
        #remove old config
        sudo('rm -f /etc/mysql/my.cnf')
        #replace with new
        sudo('cp /srv/directedstudies/deployment/config/mysql/my.cnf /etc/mysql')

        #run mysql and do the setup
        with settings(warn_only=True): 
            sudo ('echo "create database sps;" | mysql -h127.0.0.1 -uroot -proot')
        with cd('/srv/directedstudies/'):
            #use rob's fabfile to deal with setting up the tables
            sudo('fab setup_database')

    else:
        print 'invalid server type chosen'


