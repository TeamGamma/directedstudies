from datetime import timedelta

TRANSACTION_SERVER_HOST = '192.168.252.{{ transaction_server }}'
BACKUP_TRANSACTION_SERVER_HOST = '192.168.252.{{ backup_transaction_server }}'
TRANSACTION_SERVER_PORT = 6000

DATABASE_CONNECTION_ARGS = {
    'drivername': 'mysql',
    'host': '192.168.252.{{ database_server }}',
    'port': 3306,
    'database': 'sps',
    'username': 'root',
    'password': 'root',
}
DATABASE_ENGINE_ARGS = {
    'echo': False,
}

DATABASE_TABLE_ARGS = {
    'mysql_engine': 'InnoDB',
}

TRANSACTION_TIMEOUT = timedelta(seconds=60)

TEST_WITH_SQLITE = True

DUMPLOG_DIR = '/tmp/'

# Interval between trigger checks in seconds
TRIGGER_INTERVAL = 3

