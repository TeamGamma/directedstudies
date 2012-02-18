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
                   	request.form['set point'],
		        	request.form['stock symbol'])
        
        if trans_server_message != False: 
            
            transaction_interface.send('localhost',50008, trans_server_message)
        
            return  ( 	""" 
                            Hi                      %s ! <br><br>
                            Method:                 %s <br><br>
                            Input monetary value:   %s <br>
                            Stock quantity:         %s <br>
                            Stock set point:        %s <br>
                            Stock symbol            %s <br> """ % (
                            
                            request.form['username'],
                            request.form['action'],
                            request.form['money value'],
                            request.form['stock quantity'],
                            request.form['set point'],
                            request.form['stock symbol'] ))
                            
        else: return ('You fudged it up, big boy <br><br> Go back and try again')
    

    else:
        return render_template('form.html')


def checkentry(username, action, money_value, stock_quantity, set_point, stock_symbol):

    # Check username for validity
    if len(username)==0:return False
    
    # Check each action for constraints
    if action=='add money':
        if  len(money_value)==0: return False
        
        #Check to see if they entered a number
        try:
            if float(money_value)>0 : return 'ADD,'+ username + ',' + money_value 
            else: return False
        except ValueError:
            return False          
        
    elif action=='get quote':
        if len(stock_symbol)!=0: return 'QUOTE' + username + ',' + stock_symbol 
        else: return False

    elif action=='buy shares':
        return True
    elif action=='sell shares':
        return True
    elif action=='set automated point':
        return True       
    elif action=='review transaction list':
        return True
    elif action=='cancel transaction':
        if len(username)!=0: return 'CANCEL_BUY,' +username

    elif action=='commit transaction':
        if len(username)!=0: return 'COMMIT_BUY,' +username
    else: return False


@app.route("/some/other/path/")
def other_path():
   return "here you go"

if __name__ == "__main__":
    app.run(debug=True)
