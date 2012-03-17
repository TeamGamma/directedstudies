from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import logging
import sys
from sps.config import config

import transaction_interface
import command_forms

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('web')

@app.route("/", methods=['GET', 'POST'])
def hello():
    log.debug('Request for /: %s', request.form)

    if request.method == "POST":

        try:
            trans_server_message = checkentry( 
                        request.form.get('username', ''),
                        request.form.get('action', ''),
                        request.form.get('money value', ''),
                        request.form.get('stock quantity', ''),
                        request.form.get('stock symbol', ''),
                        request.form.get('filename', ''))
        except Exception as e:
            log.error(e)
            # Wrap exception to prevent stupid default Flask behaviour (400)
            raise Exception(e)

        if trans_server_message != False:

            log.info('Sending to transaction server: %s', repr(trans_server_message))

            response = transaction_interface.send(
                    config.TRANSACTION_SERVER_HOST, 
                    config.TRANSACTION_SERVER_PORT, 
                    trans_server_message)

            log.info('Received from transaction server: %s', repr(response))

            return  (""" 
                            Hi                      %s ! <br><br>
                            Method:                 %s <br><br>
                            Input monetary value:   %s <br>
                            Stock quantity:         %s <br>
                            Stock symbol:           %s <br>
                            Filename:                %s <br>
                            Response: %s <br>""" % (
                            request.form.get('username', ''),
                            request.form.get('action', ''),
                            request.form.get('money value', ''),
                            request.form.get('stock quantity', ''),
                            request.form.get('stock symbol', ''),
                            request.form.get('filename', ''),
                            response
                            ))

        else:
            return ('You fudged it up, big boy <br><br> Go back and try again')


    else:
        return render_template('form.html', form=command_forms)


def checkentry(username, action, money_value, stock_quantity, stock_symbol, filename):

    # Check username for validity
    if len(username) == 0:
        return False
    
    # Check each action for constraints
    if action == 'ADD':
        if  len(money_value) == 0:
            return False
        
        #Check to see if they entered a number
        try:
            if float(money_value) > 0:
                return 'ADD,' + username + ',' + money_value 
            else:
                return False
        except ValueError:
            return False          
        
    elif action == 'QUOTE':
        if len(stock_symbol) != 0: 
            return 'QUOTE,' + username + ',' + stock_symbol 
        else:
            return False

    elif action == 'BUY':
        try:
            if len(stock_symbol) != 0 and float(money_value) > 0 and len(username)!=0:
                return "BUY," + username + ',' + stock_symbol + ',' + money_value 
            else:
                return False
        except ValueError:
            return False

    elif action == 'SELL':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "SELL," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False
    
    elif action == 'SET_BUY_AMOUNT':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "SET_BUY_AMOUNT," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False

    elif action == 'SET_BUY_TRIGGER':
        try:
            if len(stock_symbol) != 0 and float(money_value) > 0 and len(username)!=0:
                return "SET_BUY_TRIGGER," + username + ',' + stock_symbol + ',' + money_value
            else:
                return False
        except ValueError:
            return False

    elif action == 'CANCEL_SET_BUY':
        if len(username) != 0 and len(stock_symbol) != 0:
            return 'CANCEL_SET_BUY,' + username + stock_symbol
        else:
            return False


    elif action == 'SET_SELL_AMOUNT':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "SET_SELL_AMOUNT," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False

    elif action == 'SET_SELL_TRIGGER':
        try:
            if len(stock_symbol) != 0 and float(money_value) > 0 and len(username)!=0:
                return "SET_SELL_TRIGGER," + username + ',' + stock_symbol + ',' + money_value
            else:
                return False
        except ValueError:
            return False

    elif action == 'CANCEL_SET_SELL':
        if len(username) != 0 and len(stock_symbol) != 0:
            return 'CANCEL_SET_SELL,' + username + stock_symbol
        else:
            return False


    elif action == 'DUMPLOG_USER':
        if len(username) != 0 and len(filename) != 0:
            return 'DUMPLOG,' + username + filename
        else:
            return False

    elif action == 'DUMPLOG':
        if len(filename) != 0:
            return 'DUMPLOG,' + filename
        else:
            return False

    elif action == 'DISPLAY_SUMMARY':
        if len(username) != 0:
            return 'DISPLAY_SUMMARY,' + username
        else:
            return False

    elif action == 'CANCEL_BUY':
        if len(username) != 0:
            return 'CANCEL_BUY,' + username
        else:
            return False

    elif action == 'CANCEL_SELL':
        if len(username) != 0:
            return 'CANCEL_SELL,' + username
        else:
            return False

    elif action == 'COMMIT_BUY':
        if len(username) != 0:
            return 'COMMIT_BUY,' + username
        else:
            return False

    elif action == 'COMMIT_SELL':
        if len(username) != 0:
            return 'COMMIT_SELL,' + username

    else:
        return False


@app.route("/some/other/path/")
def other_path():
   return "here you go"

if __name__ == "__main__":
    app.run(debug=True)
