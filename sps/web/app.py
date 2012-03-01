from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

import transaction_interface

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def hello():
    if request.method == "POST":

        trans_server_message = checkentry( 
                    request.form['username'],
                    request.form['action'],
                    request.form['money value'],
                    request.form['stock quantity'],
                    request.form['stock symbol'],
                    request.form['filename'])
       


        if trans_server_message != False:
      
            response = transaction_interface.send('localhost', 50008, trans_server_message)
        
            return  (""" 
                            Hi                      %s ! <br><br>
                            Method:                 %s <br><br>
                            Input monetary value:   %s <br>
                            Stock quantity:         %s <br>
                            Stock symbol:           %s <br>
                            Filename:                %s <br>
                            Response: %s <br>""" % (
                            request.form['username'],
                            request.form['action'],
                            request.form['money value'],
                            request.form['stock quantity'],
                            request.form['stock symbol'],
                            request.form['filename'],
                            response
                            ))
                            
        else:
            return ('You fudged it up, big boy <br><br> Go back and try again')
    

    else:
        return render_template('form.html')


def checkentry(username, action, money_value, stock_quantity, stock_symbol, filename):

    # Check username for validity
    if len(username) == 0:
        return False
    
    # Check each action for constraints
    if action == 'add money':
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
        
    elif action == 'get quote':
        if len(stock_symbol) != 0: 
            return 'QUOTE' + username + ',' + stock_symbol 
        else:
            return False

    elif action == 'buy shares':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "BUY," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False

    elif action == 'sell shares':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "SELL," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False
    
    elif action == 'set buy amount':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "SET_BUY_AMOUNT," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False

    elif action == 'set buy trigger':
        try:
            if len(stock_symbol) != 0 and float(money_value) > 0 and len(username)!=0:
                return "SET_BUY_TRIGGER," + username + ',' + stock_symbol + ',' + money_value
            else:
                return False
        except ValueError:
            return False

    elif action == 'cancel set buy':
        if len(username) != 0 and len(stock_symbol) != 0:
            return 'CANCEL_SET_BUY,' + username + stock_symbol
        else:
            return False


    elif action == 'set sell amount':
        try:
            if len(stock_symbol) != 0 and float(stock_quantity) > 0 and len(username)!=0:
                return "SET_SELL_AMOUNT," + username + ',' + stock_symbol + ',' + stock_quantity
            else:
                return False
        except ValueError:
            return False

    elif action == 'set sell trigger':
        try:
            if len(stock_symbol) != 0 and float(money_value) > 0 and len(username)!=0:
                return "SET_SELL_TRIGGER," + username + ',' + stock_symbol + ',' + money_value
            else:
                return False
        except ValueError:
            return False

    elif action == 'cancel set sell':
        if len(username) != 0 and len(stock_symbol) != 0:
            return 'CANCEL_SET_SELL,' + username + stock_symbol
        else:
            return False


    elif action == 'dump log user':
        if len(username) != 0 and len(filename) != 0:
            return 'DUMPLOG,' + username + filename
        else:
            return False

    elif action == 'dump log all':
        if len(filename) != 0:
            return 'DUMPLOG,' + filename
        else:
            return False

    elif action == 'display summary':
        if len(username) != 0:
            return 'DISPLAY_SUMMARY,' + username
        else:
            return False
    
    elif action == 'cancel buy':
        if len(username) != 0:
            return 'CANCEL_BUY,' + username
        else:
            return False

    elif action == 'cancel sell':
        if len(username) != 0:
            return 'CANCEL_SELL,' + username
        else:
            return False

    elif action == 'commit buy':
        if len(username) != 0:
            return 'COMMIT_BUY,' + username
        else:
            return False

    elif action == 'commit sell':
        if len(username) != 0:
            return 'COMMIT_SELL,' + username
    
    else:
        return False


@app.route("/some/other/path/")
def other_path():
   return "here you go"

if __name__ == "__main__":
    app.run(debug=True)
