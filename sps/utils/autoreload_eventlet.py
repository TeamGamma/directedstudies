from __future__ import print_function
import sys, os
import eventlet
import subprocess
import time
from sps.utils.autoreload import code_changed

RESTART_CODE = 8
ERROR_SLEEP_TIME = 10

def watch_files():
    """ Watches imported files for changes """
    while True:
        if code_changed():
            print('Code was changed, exiting...')
            sys.exit(RESTART_CODE)
        else:
            eventlet.sleep(1)


def autoreload():
    if os.environ.get("EXIT_ON_CHANGE") == "true":
        # This is the child process, just spawn the code monitor and continue to main
        eventlet.spawn_n(watch_files)
        return

    print('Watching code files...')

    while True:
        # Run again with env marker added
        env = os.environ.copy()
        env["EXIT_ON_CHANGE"] = 'true'
        print('Starting child process:')
        print(sys.argv)
        retcode = subprocess.call(sys.argv, shell=False, close_fds=True, env=env)

        print('server process exited with code %d' % retcode)
        if retcode != RESTART_CODE:
            if not retcode:
                # If sugar-activity returns zero, just exit
                print('server exited')
                sys.exit(0)
            else:
                # If sugar-activity returns an error code, restart after a delay
                print('Activity did not exit safely!')
                time.sleep(ERROR_SLEEP_TIME)
        else:
            print('Server exited because of code modifications, restarting...')


