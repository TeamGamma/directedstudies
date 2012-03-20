""" 
This is the Fabric file to do the deployment on the remote server

You can type Fab Type Location Username to run it
Where Type == database, transaction, or web

The fabric file will set up and launch the appropriate server
"""

#The first thing we do is import the fabric libraries
from __future__ import with_statement
from fabric.api import env, settings, roles, execute
from fabric.operations import sudo, run, put
from fabric.context_managers import cd, hide
from fabric.contrib.files import exists, upload_template
from deploy_utils import default_roles
from os import path

github_repo = 'git://github.com/TeamGamma/directedstudies.git'
fabdir = path.abspath(path.dirname(__file__))

env.roledefs = {
    'db': ['a01'],
    'web': ['a02'],
    'transaction': ['a03'],
    'vm': ['vagrant@127.0.0.1:2222']
}

# password auth
env.user = 'direct'
env.password = 'direct'

# Prevents errors with some terminal commands (service)
env.always_use_pty = False

@default_roles('transaction', 'web', 'db')
def update_network():
    """
    Updates /etc/network/interfaces and brings up the network interfaces.
    """
    name = env.host
    machine_number = int(name[1:])
    upload_template('network/interfaces', '/etc/network/interfaces', 
        template_dir=path.join(fabdir, 'config'),
        use_jinja=True, use_sudo=True, backup=True, 
        context=dict(machine_number=machine_number))
    run('cat /etc/network/interfaces')
    for interface in ['eth0', 'eth1', 'eth3']:
        sudo('ifdown %s' % interface)
        sudo('ifup %s' % interface)


@roles('transaction', 'web', 'db')
def update_config_file(quote_client='sps.quotes.client.RandomQuoteClient'):
    """
    Updates the remote config file with the local one
    """
    # Use fabfile's predefined server names
    context = {
        "transaction_server": env.roledefs['transaction'][0].split(':')[0],
        "database_server": env.roledefs['db'][0].split(':')[0],
        "quote_client": quote_client
    }
    upload_template('config_template.py', 
        '/srv/directedstudies/config.py', template_dir=path.join(fabdir, 'config'),
        use_jinja=True, use_sudo=True, backup=True, context=context)

def blank():
    """ Used for testing fabric configuration """
    pass


def deploy_all():
    """ Deploys all servers """
    execute(deploy_db)
    execute(deploy_transaction)
    execute(deploy_web)

def update():
    """ Updates code and restarts all servers """
    execute(update_code)
    execute(restart_transaction_server)
    execute(restart_web_server)


@roles('web', 'db', 'transaction')
def deploy_base():
    """
    Deploys the code and installs the base libraries for all server types
    """

    # update apt-cache library
    with hide('stdout', 'stderr'):
        sudo('apt-get update')

    # ubuntu goodies
    sudo("apt-get install --assume-yes build-essential python-pip python-dev python-mysqldb git-core sqlite3 python-mysqldb fabric python-lxml")

    # Make top-level folder if it doesn't exist
    sudo('mkdir -p /srv')

    with cd('/srv'):
        # Clone git repo if it doesn't exist
        if not exists('directedstudies'):
            sudo('git clone %s directedstudies' % github_repo)

        with cd('/srv/directedstudies/'):
            sudo('git pull')

            # Install newer pip version since Ubuntu ships with broken one
            sudo('pip install --upgrade pip')

            # Install python libs
            sudo('pip install -r requirements.txt')

    update_config_file()


@roles('web')
def deploy_web():
    """ Deploys the web server """
    deploy_base()

    # Install apache
    sudo('apt-get -y install apache2 libapache2-mod-wsgi')

    # configure apache for wsgi by copying the repo config to remote install
    put(path.join(fabdir, 'config/apache/wsgi_configuration'),
        '/etc/apache2/sites-available/wsgi_configuration', use_sudo=True)

    # create a link to the site config and delete default site config
    sudo('rm -f /etc/apache2/sites-enabled/*default')
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
    put(path.join(fabdir, 'config/mysql/my.cnf'), '/etc/mysql/my.cnf', use_sudo=True)

    # Restart database server
    sudo('service mysql restart')

    # Create the database (totally insecure)
    sql = """
    CREATE DATABASE IF NOT EXISTS sps;
    CREATE USER 'root'@'%' IDENTIFIED BY 'root';
    GRANT ALL ON sps.* TO 'root'@'%';
    """
    sudo('echo "%s" | mysql -h127.0.0.1 -uroot -proot' % sql)

    with cd('/srv/directedstudies/'):
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


@roles('transaction', 'web', 'db')
def update_code():
    """ Updates the code on all servers from GitHub """
    with cd('/srv/directedstudies'):
        sudo('git pull')


@roles('transaction')
def restart_transaction_server():
    """ Restarts the transaction server """
    with cd('/srv/directedstudies'):
        run('supervisorctl restart tserver')

@roles('web')
def restart_web_server():
    """ Restarts the web server """
    sudo('service apache2 restart')

@roles('db')
def restart_db():
    """ Restarts the database server """
    sudo('service mysql restart')


