from flask import Flask, render_template, request, redirect, session, flash, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_mail import Mail, Message
from functools import wraps
import pymysql
import os
from werkzeug.utils import secure_filename
from datetime import datetime


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

# Configuración para subir archivos
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Tipos de archivo permitidos (puedes ajustar)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'png', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    role = db.Column(db.String(20), default='client')

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

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect('/admin/dashboard')
            else:
                return redirect('/dashboard')

        flash('Credenciales incorrectas')
        return redirect('/login')

    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

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
@login_required
def dashboard():
    if session.get('role') != 'client':
        return redirect('/admin/dashboard')
    
    user_id = session['user_id']

    # Obtener documentos del usuario junto con su tipo
    documents = db.session.execute(
        text('''
            SELECT d.id, d.file_path, d.uploaded_at, d.status, dt.name AS type_name
            FROM documents d
            JOIN document_types dt ON d.type_id = dt.id
            WHERE d.user_id = :user_id
            ORDER BY d.uploaded_at DESC
        '''), 
        {'user_id': user_id}
    ).fetchall()

    # Obtener todos los tipos de documentos para el select
    document_types = db.session.execute(
        text('SELECT id, name FROM document_types ORDER BY name ASC')
    ).fetchall()

    # Obtener procesos del usuario (si ya lo tenías)
    user_processes = db.session.execute(
        text('SELECT * FROM processes WHERE user_id = :user_id ORDER BY updated_at DESC'),
        {'user_id': user_id}
    ).fetchall()

    return render_template(
        'dashboard.html', 
        documents=documents, 
        document_types=document_types,
        user_processes=user_processes
    )


# Logout
@app.route('/logout')
def logout():
    session.clear()
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
# Nuevo: protección de rutas de administrador
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Acceso no autorizado')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# NUEVO: Dashboard de administrador
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    clientes = User.query.filter_by(role='client').order_by(User.id.desc()).limit(10).all()

    procesos = db.session.execute(
        text('''
            SELECT p.id, p.user_id, p.status, p.updated_at,
                   u.first_name, u.last_name
            FROM processes p
            JOIN user u ON p.user_id = u.id
            ORDER BY p.updated_at DESC
        ''')
    ).fetchall()

    # Obtener documentos de todos los clientes
    documentos_por_usuario = {}
    for cliente in clientes:
        docs = db.session.execute(
            text('''
                SELECT d.id, d.file_path, d.status, dt.name AS type_name, d.uploaded_at
                FROM documents d
                JOIN document_types dt ON d.type_id = dt.id
                WHERE d.user_id = :user_id
                ORDER BY d.uploaded_at DESC
            '''), {'user_id': cliente.id}
        ).fetchall()
        documentos_por_usuario[cliente.id] = docs

    return render_template(
        'admin_dashboard.html',
        clientes=clientes,
        procesos=procesos,
        documentos_por_usuario=documentos_por_usuario
    )

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
# NUEVO: Cambiar estado del documento
@app.route('/admin/document/<int:id>/status', methods=['POST'])
@admin_required
def change_document_status(id):
    nuevo_status = request.form['status']
    db.session.execute(
        text('UPDATE documents SET status = :status WHERE id = :id'),
        {'status': nuevo_status, 'id': id}
    )
    db.session.commit()
    flash('Estado del documento actualizado', 'success')
    return redirect('/admin/dashboard#admin-documents')
    


# Ruta para subir documentos
@app.route('/upload_document', methods=['POST'])
@login_required
def upload_document():
    file = request.files.get('file')
    type_id = request.form.get('type_id')

    if not file or not type_id:
        flash('Por favor selecciona un archivo y tipo de documento', 'danger')
        return redirect('/dashboard#documents')

    if not allowed_file(file.filename):
        flash('Tipo de archivo no permitido. Solo PDF, JPG, JPEG, PNG.', 'danger')
        return redirect('/dashboard#documents')

    # Guardar archivo de forma segura
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    saved_filename = f"{session['user_id']}_{timestamp}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    file.save(file_path)

    # Insertar en base de datos
    db.session.execute(
        text('''
            INSERT INTO documents (user_id, type_id, file_path, uploaded_at, status)
            VALUES (:user_id, :type_id, :file_path, :uploaded_at, :status)
        '''), 
        {
            'user_id': session['user_id'],
            'type_id': type_id,
            'file_path': saved_filename,
            'uploaded_at': datetime.now(),
            'status': 'pending'
        }
    )
    db.session.commit()
    

    flash('Documento subido correctamente y en revisión', 'success')
    return redirect('/dashboard#documents')
# Ruta para servir archivos subidos
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
