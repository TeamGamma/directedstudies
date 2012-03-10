""" 
This is the Fabric file to do the deployment on the remote server

You can type Fab Type Location Username to run it
Where Type == database, transaction, or web

The fabric file will set up and launch the appropriate server
"""

#The first thing we do is import the fabric libraries
from __future__ import with_statement
from fabric.api import env, settings, roles
from fabric.operations import sudo, run, put
from fabric.context_managers import cd, hide
from fabric.contrib.files import exists
from os.path import join, abspath, dirname

github_repo = 'git://github.com/TeamGamma/directedstudies.git'
fabdir = abspath(dirname(__file__))

vm_address = '142.104.103.30:2222'
env.roledefs = {
    'db': [vm_address],
    'web': [vm_address],
    'transaction': [vm_address],
}

# password auth
env.user = 'vagrant'
env.password = 'vagrant'

# Prevents errors with some terminal commands (service)
env.always_use_pty = False

def blank():
    """ Used for testing fabric configuration """
    pass

@roles('web', 'db', 'transaction')
def deploy_base():
    """
    Deploys the code and installs the base libraries for all server types
    """

    # update apt-cache library
    with hide('stdout', 'stderr'):
        sudo('apt-get update')

    # ubuntu goodies
    sudo("apt-get install --assume-yes build-essential python-pip python-dev python-mysqldb git-core sqlite3 apache2 libapache2-mod-wsgi python-mysqldb fabric")

    # Make top-level folder if it doesn't exist
    sudo('mkdir -p /srv')

    with cd('/srv'):
        # Clone git repo if it doesn't exist
        if not exists('directedstudies'):
            sudo('git clone %s directedstudies' % github_repo)

        with cd('/srv/directedstudies/'):
            sudo('git pull')

            #python goodies
            sudo('pip install -r requirements.txt')
            sudo('pip install eventlet sqlalchemy')


@roles('web')
def deploy_web():
    """ Deploys the web server """
    deploy_base()

    #configure apache for wsgi by copying the repo config to remote install
    put(join(fabdir, 'config/apache/wsgi_configuration'),
        '/etc/apache2/sites-available/wsgi_configuration', use_sudo=True)

    #create a link to the enabled directory
    sudo('ln -s -f /etc/apache2/sites-available/wsgi_configuration /etc/apache2/sites-enabled/wsgi_configuration_link')

    # Make log directory to prevent startup error
    sudo('mkdir -p /srv/directedstudies/logs')

    # Restart apache
    result = sudo('service apache2 restart')
    print result


@roles('db')
def deploy_db():
    """ Deploys the database server """
    deploy_base()

    # install mysql
    sudo("""debconf-set-selections <<< 'mysql-server-5.1 mysql-server/root_password password root'""")
    sudo("""debconf-set-selections <<< 'mysql-server-5.1 mysql-server/root_password_again password root'""")
    sudo('apt-get -y install mysql-server')

    # Configure the database server
    put(join(fabdir, 'config/mysql/my.cnf'), '/etc/mysql/my.cnf', use_sudo=True)

    # Restart database server
    sudo('service mysql restart')

    # Create the database
    sudo('echo "CREATE DATABASE IF NOT EXISTS sps;" | mysql -h127.0.0.1 -uroot -proot')

    with cd('/srv/directedstudies/'):
        with hide('stdout'):
            #use rob's local fabfile to deal with setting up the tables
            sudo('fab setup_database')


@roles('transaction')
def deploy_transaction():
    """ Deploys the transaction server """
    deploy_base()

    with cd('/srv/directedstudies/'):
        print sudo('python setup.py develop')
        with settings(warn_only=True): 
            run('supervisord -c supervisord.conf')
            run('supervisorctl restart tserver')


