from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():
    if request.method == "POST":

        if ( checkentry( request.form['action'],
        			request.form['money value'],
                   	request.form['stock quantity'],
                   	request.form['set point'],
		        	request.form['stock symbol'])) == True: 

        
            return  ( 	""" method: %s <br><br>
                            input monetary value: %s <br>
                            stock quantity: %s <br>
                            stock set point: %s <br>
                            stock symbol %s <br> """ % (
                            
                            request.form['action'],
                            request.form['money value'],
                            request.form['stock quantity'],
                            request.form['set point'],
                            request.form['stock symbol'] ))
                            
        else: return ('You fudged it up, big boy')
    

    else:
        return render_template('form.html')


def checkentry(action, money_value, stock_quantity, set_point, stock_symbol):

    # check each action for constraints
    if action=='add money':
        if  len(money_value)==0: return False
        
        #check to see if they entered a number
        try:
            if float(money_value)>0 : return True
            else: return False
        except ValueError:
            return False          
        
    elif action=='get quote':
        if len(stock_symbol)!=0: return True
        else: return False

    elif action=='buy shares':
        return True
    elif action=='sell shares':
        return True
    elif action=='set automated point':
        return Trure       
    elif action=='review transaction list':
        return True
    elif action=='cancel transaction':
        return True
    elif action=='commit transaction':
        return True
    else: return True



@app.route("/some/other/path/")
def other_path():
   return "here you go"

if __name__ == "__main__":
    app.run(debug=True)
