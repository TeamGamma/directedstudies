from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():
    if request.method == "POST":


        return  ( 	"""method: %s <br><br>
			input monetary value: %s <br>
                   	stock quantity: %s <br>
			stock set point: %s <br>
                  	stock symbol %s <br> """ % (
                    	
			request.form['action'],
			request.form['money value'],
                    	request.form['stock quantity'],
                    	request.form['set point'],
			request.form['stock symbol'] ))
        # put what they submitted here

    else:
        return render_template('form.html')
    

@app.route("/some/other/path/")
def other_path():
   return "here you go"

@app.route('/login')
def login(): 
    pass

@app.route('/user/test')
def test():
    return "it works dfgsdg "


@app.route('/user')
def profile(username): 
    return "hello"

    with app.test_request_context():
        print url_for('index')
        print url_for('login')
        print url_for('login', next='/')
        print url_for('profile', username='John Doe')

if __name__ == "__main__":
    app.run(debug=True)
