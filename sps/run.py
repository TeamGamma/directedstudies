'''
Created on Jan 24, 2012

@author: rob
'''


if __name__ == '__main__':
    try:
        import flask, sqlalchemy, MySQLdb
    except ImportError:
        print 'Failed to import:'
        raise
    print 'Success!'
