from datetime import timedelta

TRANSACTION_SERVER_HOST = '{{ transaction_server }}'
TRANSACTION_SERVER_PORT = 6000

DATABASE_CONNECTION_ARGS = {
    'drivername': 'mysql',
    'host': '{{ database_server }}',
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

QUOTE_CLIENT = '{{ quote_client }}'

TRANSACTION_TIMEOUT = timedelta(seconds=60)

TEST_WITH_SQLITE = True

DUMPLOG_DIR = '/tmp/'

# Interval between trigger checks in seconds
TRIGGER_INTERVAL = 3

