from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():
    if request.method == "POST":
        return  ( """your name is %s  <br>
                   your password is %s <br>
                   your fruits are %s <br>
                    you're from %s <br>""" % (
                    request.form['username'], 
                    request.form['password'],
                    request.form['foods'],
                    request.form['continent'] ))
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
