""" 
This is the Fabric file to do the deployment on the remote server

You can type Fab Type Location Username to run it
Where Type == database, transaction, or web

The fabric file will set up and launch the appropriate server
"""

#The first thing we do is import the fabric libraries
from fabric.api import env, hosts
from fabric.operations import put, sudo
from fabric.context_managers import cd
from os import path
import sys

#setup remote servers
env.user = 'vagrant'
env.password = 'vagrant'
# add remote host addresses here
env.hosts = ['142.104.125.207:2222']

github_repo_address = 'git://github.com/TeamGamma/directedstudies.git'


def deploy(server_type='web'):
    
    #install all the goodies

    #update apt-cache library
    sudo('apt-get update')

    # ubuntu goodies
    sudo("""apt-get install --assume-yes build-essential python-pip python-dev python-mysqldb git-core sqlite3 apache2 libapache2-mod-wsgi""")

    #python goodies
    sudo('pip install -r requirements.txt')

    #clone git repository
    sudo('mkdir /srv/directedstudies')
    cd('/srv/directedstudies')
    sudo('git clone %s' % (github_repo_address))

    if server_type == 'web':
        #start the web server

        #configure apache for wsgi by copying the repo config to remote install
        put('config/apache/wsgi_configuration' '/etc/apache2/sites-available/')
        #create a link to the enabled directory
        sudo("""ln -s /etc/apache2/sites-available/wsgi_configuration
                /etc/apache2/sites-enabled/wsgi_configuration_link""")
        #remove the original default link to avoid getting messed up
        sudo('rm /etc/apache2/sites-enabled/000-default')
        
        #restart apache2 to configure
        sudo('service apache2 restart')
        
    elif server_type == 'transaction':
        #navigate to server and run it. nice and easy right?
        cd('/srv/directedstudies/sps/transactions/')
        sudo('python server.py')

    elif server_type == 'database':
        #start the database server
        sudo("""debconf-set-selections <<< 'mysql-server-5.1 mysql-server/root_password password root'""")
        sudo("""debconf-set-selections <<< 'mysql-server-5.1 mysql-server/root_password_again password root'""")
        sudo('apt-get -y install mysql-server')
        
        #Configure the database server
        #remove old config
        sudo('rm /etc/mysql/my.cnf')
        #replace with new
        sudo('rm config/mysql/my.cnf')

        #run mysql and do the setup
        sudo ('echo "create database sps;" | mysql -h127.0.0.1 -uroot -proot')
        cd('/srv/directedstudies/')
        #use rob's fabfile to deal with setting up the tables
        sudo('fab setup_database')

    else:
        print 'invalid server type chosen'


