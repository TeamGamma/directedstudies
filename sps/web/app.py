from flask import Flask, request, render_template, abort, session, redirect, url_for
import logging
from os.path import dirname, abspath, join, normpath, exists
from sps.config import config, read_config_file
from lxml import objectify

# Setup logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('web')

# Load optional config file
config_file = join(abspath(dirname(__file__)), '..', '..', 'config.py')
if exists(config_file):
    log.info('Using config file "%s"', normpath(config_file))
    read_config_file(config_file)

import transaction_interface
import command_forms

app = Flask(__name__)
app.secret_key = '\x1dO\xdf\xf8\x82)\xe3\t\xf8ZmXD\xff\xbck\xa4\xfaH\xa7\x80EM\xfa'

@app.route("/")
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('form.html', form=command_forms, user=session['username'])

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Require a username of at least one character
        if not len(request.form['username']):
            abort(400)

        # Log in user
        session['username'] = request.form['username']
        return redirect(url_for('home'))
    else:
        return render_template('login.html', form=command_forms)

@app.route("/logout")
def logout():
    # Log out user
    del session['username']
    return redirect(url_for('login'))


def send_to_transactions(message):
    log.info('Sending to transaction server: %s', repr(message))

    response = transaction_interface.send(
            config.TRANSACTION_SERVER_HOST, 
            config.TRANSACTION_SERVER_PORT, 
            message)

    if response is None:
        # Resend to backup server
        response = transaction_interface.send(
                config.BACKUP_TRANSACTION_SERVER_HOST, 
                config.TRANSACTION_SERVER_PORT, 
                message)

    if response is None:
        return 'Service unavailable', 502

    log.info('Received from transaction server: %s', repr(response))

    # Try to parse XML response and determine HTTP code
    try:
        tree = objectify.fromstring(response)
        if tree.get('contents') == 'error':
            if 'System error' in str(tree.error):
                # Something went wrong in the system
                return response, 500

            # The user screwed up somehow
            return response, 400
    except:
        # Couldn't parse, just return server error
        return response, 500

    return response, 200


# Custom URL handlers for each command - makes validation and logging easier

@app.route('/KILL', methods=['POST'])
def handle_KILL():
    log.debug('KILL Request: %s', repr(dict(request.form)))
    return send_to_transactions('KILL')

@app.route('/ADD', methods=['POST'])
def handle_ADD():
    log.debug('ADD Request: %s', repr(dict(request.form)))

    username, amount = validate('username', ('amount', float))
    return send_to_transactions('ADD,' + username + ',' + amount)

@app.route('/QUOTE', methods=['POST'])
def handle_QUOTE():
    username, stock_symbol = validate('username', 'stock_symbol')
    return send_to_transactions('QUOTE,' + username + ',' + stock_symbol)

@app.route('/BUY', methods=['POST'])
def handle_BUY():
    username, stock_symbol, amount = validate('username', 'stock_symbol', ('amount', float))
    return send_to_transactions("BUY," + username + ',' + stock_symbol + ',' + amount)

@app.route('/SELL', methods=['POST'])
def handle_SELL():
    username, stock_symbol, amount = validate('username', 'stock_symbol', ('amount', float))
    return send_to_transactions("SELL," + username + ',' + stock_symbol + ',' + amount)

@app.route('/SET_BUY_AMOUNT', methods=['POST'])
def handle_SET_BUY_AMOUNT():
    username, stock_symbol, amount = validate('username', 'stock_symbol', ('amount', float))
    return send_to_transactions("SET_BUY_AMOUNT," + username + ',' + stock_symbol + ',' + amount)

@app.route('/SET_BUY_TRIGGER', methods=['POST'])
def handle_SET_BUY_TRIGGER():
    username, stock_symbol, amount = validate('username', 'stock_symbol', ('amount', float))
    return send_to_transactions("SET_BUY_TRIGGER," + username + ',' + stock_symbol + ',' + amount)

@app.route('/CANCEL_SET_BUY', methods=['POST'])
def handle_CANCEL_SET_BUY():
    username, stock_symbol = validate('username', 'stock_symbol')
    return send_to_transactions('CANCEL_SET_BUY,' + username + ',' + stock_symbol)

@app.route('/SET_SELL_AMOUNT', methods=['POST'])
def handle_SET_SELL_AMOUNT():
    username, stock_symbol, quantity = validate('username', 'stock_symbol', ('quantity', int))
    return send_to_transactions("SET_SELL_AMOUNT," + username + ',' + stock_symbol + ',' + quantity)

@app.route('/SET_SELL_TRIGGER', methods=['POST'])
def handle_SET_SELL_TRIGGER():
    username, stock_symbol, amount = validate('username', 'stock_symbol', ('amount', float))
    return send_to_transactions("SET_SELL_TRIGGER," + username + ',' + stock_symbol + ',' + amount)

@app.route('/CANCEL_SET_SELL', methods=['POST'])
def handle_CANCEL_SET_SELL():
    username, stock_symbol = validate('username', 'stock_symbol')
    return send_to_transactions('CANCEL_SET_SELL,' + username + ',' + stock_symbol)

@app.route('/CANCEL_BUY', methods=['POST'])
def handle_CANCEL_BUY():
    username = validate('username')
    return send_to_transactions('CANCEL_BUY,' + username)

@app.route('/CANCEL_SELL', methods=['POST'])
def handle_CANCEL_SELL():
    username = validate('username')
    return send_to_transactions('CANCEL_SELL,' + username)

@app.route('/COMMIT_BUY', methods=['POST'])
def handle_COMMIT_BUY():
    username = validate('username')
    return send_to_transactions('COMMIT_BUY,' + username)

@app.route('/COMMIT_SELL', methods=['POST'])
def handle_COMMIT_SELL():
    username = validate('username')
    return send_to_transactions('COMMIT_SELL,' + username)

@app.route('/DUMPLOG_USER', methods=['POST'])
def handle_DUMPLOG_USER():
    username, filename = validate('username', 'filename')
    return send_to_transactions('DUMPLOG,' + username + ',' + filename)

@app.route('/DUMPLOG', methods=['POST'])
def handle_DUMPLOG():
    filename = validate('filename')
    return send_to_transactions('DUMPLOG,' + filename)

@app.route('/DISPLAY_SUMMARY', methods=['POST'])
def handle_DISPLAY_SUMMARY():
    username = validate('username')
    return send_to_transactions('DISPLAY_SUMMARY,' + username)


@app.route("/favicon.ico")
def favicon():
    return ""


def validate(*names):
    """ Checks for a list of form names with optional validator functions """
    values = []
    for item in names:
        validator = None

        # Check if argument is a tuple of (name, validator function)
        if isinstance(item, tuple):
            name, validator = item
        else:
            # argument is just a string
            name = item

        # Get from form
        value = request.form[name]

        # Check that it's not empty
        if len(name) == 0:
            abort(400)

        if validator is not None:
            # Validator function will raise ValueError if validation fails
            try:
                validator(value)
            except ValueError:
                abort(400)
        values.append(value)

    # Return single value if only one input was requested
    if len(values) == 1:
        return values[0]
    return values



if __name__ == "__main__":
    app.run(debug=True)
