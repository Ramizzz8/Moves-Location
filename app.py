from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from functools import wraps
import pymysql

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://movesadmin:Movesadmin1234$@localhost/MovesLocation'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'   # Cambia según tu proveedor
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'tu_correo@gmail.com'  # Tu correo
app.config['MAIL_PASSWORD'] = 'tu_contraseña_de_app' # Contraseña o App Password

db = SQLAlchemy(app)
mail = Mail(app)

# Modelos
class User(db.Model):
    __tablename__ = 'user'  
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(50))
    password = db.Column(db.String(200), nullable=False)

# Crear tablas
with app.app_context():
    db.create_all()

# Ruta principal (home)
@app.route('/')
def home():
    return render_template('index.html')

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Buscar usuario por email
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.role == 'admin':
                # Inicia sesión de admin
                session.clear()  # limpiar cualquier sesión previa
                session['admin_id'] = user.id
                return redirect('/admin/dashboard')
            else:
                # Inicia sesión de cliente
                session.clear()  # limpiar cualquier sesión previa
                session['user_id'] = user.id
                return redirect('/dashboard')

        flash('Credenciales incorrectas')
        return redirect('/login')

    return render_template('login.html')


# Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener todos los campos del formulario
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form.get('phone')  # opcional
        country = request.form['country']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validaciones
        if password != confirm_password:
            flash('Las contraseñas no coinciden')
            return redirect('/register')

        if User.query.filter_by(email=email).first():
            flash('El correo ya está registrado')
            return redirect('/register')

        # Hashear contraseña
        hashed_password = generate_password_hash(password)

        # Crear nuevo usuario con todos los datos
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            country=country,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        # Iniciar sesión automáticamente
        session['user_id'] = new_user.id
        return redirect('/dashboard')

    return render_template('register.html')
# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# NUEVO: Ruta de contacto
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        mensaje = request.form['mensaje']

        try:
            msg = Message(
                subject=f"Nuevo mensaje de contacto de {nombre}",
                sender=app.config['MAIL_USERNAME'],
                recipients=['ajulianrague@gmail.com'],  # Aquí tu correo de destino
                body=f"Nombre: {nombre}\nEmail: {email}\nTeléfono: {telefono}\n\nMensaje:\n{mensaje}"
            )
            mail.send(msg)
            flash('¡Mensaje enviado correctamente!', 'success')
        except Exception as e:
            flash(f'Error al enviar el mensaje: {e}', 'danger')

        return redirect(url_for('contact'))

    return render_template('contact.html')
# NUEVO: Ruta de login para administradores
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password) and user.role == 'admin':
            session['admin_id'] = user.id
            return redirect('/admin/dashboard')
        else:
            flash('Credenciales incorrectas o no tienes permisos de administrador')
            return redirect('/admin/login')

    return render_template('admin_login.html')
# Nuevo: protección de rutas de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Debes iniciar sesión como administrador')
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function
# NUEVO: Dashboard de administrador
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Ver últimos 10 clientes registrados
    clientes = User.query.filter_by(role='client').order_by(User.id.desc()).limit(10).all()
    # Todos los procesos
    procesos = db.session.execute('SELECT p.id, p.user_id, p.status, p.updated_at, u.first_name, u.last_name FROM processes p JOIN user u ON p.user_id = u.id ORDER BY p.updated_at DESC').fetchall()
    
    return render_template('admin_dashboard.html', clientes=clientes, procesos=procesos)
# NUEVO: Cambiar estado del proceso
@app.route('/admin/process/<int:id>/status', methods=['POST'])
@admin_required
def cambiar_status(id):
    nuevo_status = request.form['status']
    proceso = db.session.execute('SELECT * FROM processes WHERE id = :id', {'id': id}).first()

    if proceso:
        db.session.execute('UPDATE processes SET status = :status WHERE id = :id', {'status': nuevo_status, 'id': id})
        db.session.commit()
        flash('Estado del proceso actualizado')
    return redirect('/admin/dashboard')
#NUEV0: Logout de administrador
@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_id', None)
    return redirect('/admin/login')




if __name__ == '__main__':
    app.run(debug=True)
