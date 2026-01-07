from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'


# USUARIOS SIMULADOS (luego se conecta a SQL)
users = {
'user@test.com': generate_password_hash('1234')
}


@app.route('/', methods=['GET'])
def home():
return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
email = request.form['email']
password = request.form['password']


if email in users and check_password_hash(users[email], password):
session['user'] = email
return redirect('/dashboard')
return 'Credenciales incorrectas'


@app.route('/dashboard')
def dashboard():
if 'user' not in session:
return redirect('/')
return 'Panel del usuario (backend funcionando)'


@app.route('/logout')
def logout():
session.pop('user', None)
return redirect('/')


if __name__ == '__main__':
app.run(debug=True)
