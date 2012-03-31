""" 
This is the Fabric file to do the deployment on the remote server

You can type Fab Type Location Username to run it
Where Type == database, transaction, or web

The fabric file will set up and launch the appropriate server
"""

#The first thing we do is import the fabric libraries
from __future__ import with_statement
from fabric.api import env, settings
from fabric.operations import sudo, run, put
from fabric.context_managers import cd, hide
from fabric.contrib.files import exists, upload_template
from deploy_utils import default_roles as _roles
from os import path
import re

try:
    from fabric.api import execute
except ImportError:
    pass

github_repo = 'git://github.com/TeamGamma/directedstudies.git'
fabdir = path.abspath(path.dirname(__file__))

env.roledefs = {
    'db': ['a01'],
    'web': ['a02', 'a04', 'a06'],
    'transaction': ['a03'],
    'tsung': ['a10'],
    'vm': ['vagrant@127.0.0.1:2222'],
    'master': ['a09']
}

# password auth
env.user = 'direct'
env.password = 'direct'

# Prevents errors with some terminal commands (service)
env.always_use_pty = False

def update():
    """ Updates code and config and restarts all servers """
    execute(update_code)
    execute(update_config_file)
    execute(restart_transaction_server)
    execute(restart_web_server)
    execute(restart_db)


@_roles('transaction', 'web', 'db', 'tsung')
def update_network():
    """
    Updates /etc/network/interfaces and brings up the network interfaces.
    Also changes some Linux kernel settings to increase server performance.
    """
    name = env.host
    machine_number = int(name[1:])
    upload_template('network/interfaces', '/etc/network/interfaces', 
        template_dir=path.join(fabdir, 'config'),
        use_jinja=True, use_sudo=True, backup=True, 
        context=dict(machine_number=machine_number))
    run('cat /etc/network/interfaces')

    # Network settings for server performance
    sudo('echo "2048 64512" > /proc/sys/net/ipv4/ip_local_port_range')
    sudo('echo "1" > /proc/sys/net/ipv4/tcp_tw_recycle')
    sudo('echo "1" > /proc/sys/net/ipv4/tcp_tw_reuse')
    sudo('echo "10" > /proc/sys/net/ipv4/tcp_fin_timeout')
    sudo('echo "65536" > /proc/sys/net/core/somaxconn')
    sudo('echo "65536" > /proc/sys/net/ipv4/tcp_max_syn_backlog')  

    for interface in ['eth0', 'eth1', 'eth3']:
        sudo('ifdown %s' % interface)
        sudo('ifup %s' % interface)


@_roles('transaction', 'web', 'db')
def update_config_file(quote_client='sps.quotes.client.RandomQuoteClient'):
    """
    Updates the remote config file with the local one
    """
    # Use fabfile's predefined server names
    context = {
        "transaction_server": _machine_num(env.roledefs['transaction'][0]),
        "database_server": _machine_num(env.roledefs['db'][0]),
        "quote_client": quote_client,
    }
    upload_template('config_template.py', 
        '/srv/directedstudies/config.py', template_dir=path.join(fabdir, 'config'),
        use_jinja=True, use_sudo=True, backup=True, context=context)

    run('cat /srv/directedstudies/config.py')

def blank():
    """ Used for testing fabric configuration """
    pass


def deploy_all():
    """ Deploys all servers """
    execute(deploy_db)
    execute(deploy_transaction)
    execute(deploy_web)


@_roles('web', 'db', 'transaction')
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

            sudo('python setup.py develop')

    update_config_file()


@_roles('web')
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


@_roles('db')
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

    # Create the database and user (totally insecure)
    sql = """
    CREATE DATABASE IF NOT EXISTS sps;
    CREATE USER 'root'@'%' IDENTIFIED BY 'root';
    GRANT ALL ON sps.* TO 'root'@'%';
    """
    with settings(warn_only=True): 
        sudo('echo "%s" | mysql -h127.0.0.1 -uroot -proot' % sql)

    with cd('/srv/directedstudies/'):
        #use rob's local fabfile to deal with setting up the tables
        sudo('fab setup_database')


@_roles('transaction')
def deploy_transaction():
    """ Deploys the transaction server """
    deploy_base()

    with cd('/srv/directedstudies/'):
        with settings(warn_only=True): 
            run('supervisord -c supervisord.conf')
            run('supervisorctl restart tserver')


@_roles('tsung')
def deploy_tsung():
    """ Deploys the Tsung load-testing servers and updates tsung.xml """
    with hide('stdout', 'stderr'):
        sudo('apt-get update')

    sudo("apt-get -y install erlang-nox gnuplot-nox libtemplate-perl libhtml-template-perl libhtml-template-expr-perl")

    run('wget http://tsung.erlang-projects.org/dist/ubuntu/lucid/tsung_1.4.1-1_all.deb')
    sudo('dpkg -i tsung_1.4.1-1_all.deb')

    put(path.join(fabdir, 'config/tsung.xml'), '/home/direct/tsung.xml')


@_roles('transaction', 'web', 'db')
def update_code():
    """ Updates the code on all servers from GitHub """
    with cd('/srv/directedstudies'):
        sudo('git pull')


@_roles('transaction')
def restart_transaction_server():
    """ Restarts the transaction server """
    with cd('/srv/directedstudies'):
        run('supervisorctl restart tserver')

@_roles('web')
def restart_web_server():
    """ Restarts the web server """
    sudo('service apache2 restart')

@_roles('db')
def restart_db():
    """ Restarts the database server """
    sudo('service mysql restart')

    with cd('/srv/directedstudies/'):
        # Wipe the DB and start afresh
        sudo('fab setup_database')


def _machine_num(servername):
    """
    Translates a server DNS name (a01) to an IP address on the internal
    network
    """
    hostname = servername.split(':')[0]
    return int(re.search('\d+', hostname).group(0))

