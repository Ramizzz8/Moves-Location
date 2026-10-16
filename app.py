from flask import Flask, render_template, request, redirect, session, flash, url_for, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
# Se renombra para no chocar con el modelo Message (mensajes entre cliente y asesor)
from flask_mail import Mail, Message as MailMessage
from functools import wraps
import pymysql
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

# Las credenciales se leen del archivo .env (no se sube a GitHub).
# Copia .env.example a .env y rellena tus valores.
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cambia-esta-clave-en-produccion')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///moves_location.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Comprueba la conexión antes de usarla: MySQL cierra las conexiones inactivas
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 280}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB por archivo

# Modo demo (despliegue público del portafolio): muestra un aviso con las cuentas de prueba
# y no envía correos reales.
DEMO_MODE = os.environ.get('DEMO_MODE') == '1'
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Configuración para subir archivos
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
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
    
    # NUEVO: Relación con el asesor asignado
    advisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    advisor = db.relationship('User', remote_side=[id])

# Modelo para mensajes
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])


# Crear tablas
with app.app_context():
    db.create_all()

AVISO_DEMO = (
    '<style>body{padding-bottom:42px}</style>'
    '<div style="position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#0b1b33;color:#c9d6ee;'
    'font:13px/1.4 Inter,system-ui,sans-serif;padding:9px 14px;text-align:center;border-top:2px solid #f6b81a">'
    '<strong style="color:#f6b81a">Demo de portafolio</strong> · Datos ficticios que se reinician cada noche · '
    'Entra con <code>cliente@moves.demo</code> o <code>admin@moves.demo</code> (contraseña <code>Demo1234!</code>)'
    '</div>'
)

# ---------- Datos y utilidades para las plantillas ----------
ESTADOS_PROCESO = {'pending': 'Pendiente', 'in_review': 'En revisión', 'completed': 'Completado'}
ESTADOS_DOCUMENTO = {'pending': 'En revisión', 'approved': 'Aprobado', 'rejected': 'Rechazado'}
PAISES = [
    ('AR', 'Argentina'), ('BO', 'Bolivia'), ('CL', 'Chile'), ('CO', 'Colombia'), ('CR', 'Costa Rica'), ('CU', 'Cuba'),
    ('EC', 'Ecuador'), ('SV', 'El Salvador'), ('ES', 'España'), ('GT', 'Guatemala'), ('HN', 'Honduras'), ('MX', 'México'),
    ('NI', 'Nicaragua'), ('PA', 'Panamá'), ('PY', 'Paraguay'), ('PE', 'Perú'), ('DO', 'República Dominicana'),
    ('UY', 'Uruguay'), ('VE', 'Venezuela'), ('OTHER', 'Otro'),
]
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


@app.template_filter('fecha')
def formatear_fecha(valor, con_hora=False):
    """Fecha en español: «14 de octubre de 2026» (y la hora si se pide)."""
    if not valor:
        return '—'
    if isinstance(valor, str):
        try:
            valor = datetime.fromisoformat(valor)
        except ValueError:
            return valor
    texto = f'{valor.day} de {MESES[valor.month - 1]} de {valor.year}'
    if con_hora and hasattr(valor, 'hour'):
        texto += f' · {valor.hour:02d}:{valor.minute:02d}'
    return texto


@app.context_processor
def datos_plantillas():
    return {
        'ahora': datetime.now(),
        'demo': DEMO_MODE,
        'paises': PAISES,
        'estados_proceso': ESTADOS_PROCESO,
        'estados_documento': ESTADOS_DOCUMENTO,
    }


@app.after_request
def insertar_aviso_demo(response):
    if DEMO_MODE and response.mimetype == 'text/html' and not response.direct_passthrough:
        html = response.get_data(as_text=True)
        if '</body>' in html:
            response.set_data(html.replace('</body>', AVISO_DEMO + '</body>', 1))
    return response


# Ruta principal (home)
@app.route('/')
def home():
    return render_template('index.html')

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.role == 'advisor':
                flash('El panel de asesores todavía está en desarrollo. Entra como cliente o como administrador.')
                return redirect('/login')
            session.clear()
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect('/admin/dashboard')
            else:
                return redirect('/dashboard')

        flash('Credenciales incorrectas. Revisa tu email y contraseña.', 'danger')
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
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip() or None  # opcional
        country = request.form.get('country', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validaciones (el navegador también valida, pero no basta)
        if not all([first_name, last_name, email, country]) or '@' not in email:
            flash('Revisa los datos: nombre, apellidos, email y país son obligatorios.', 'danger')
            return redirect('/register')

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect('/register')

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
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

        # Iniciar sesión automáticamente (antes faltaba el rol y el panel expulsaba al usuario)
        session.clear()
        session['user_id'] = new_user.id
        session['role'] = 'client'
        flash(f'¡Bienvenido, {first_name}! Tu cuenta está lista.', 'success')
        return redirect('/dashboard')

    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') != 'client':
        return redirect('/admin/dashboard')

    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user is None:
        # La sesión apunta a un usuario que ya no existe (p. ej. tras reiniciar la demo)
        session.clear()
        return redirect('/login')

    # Documentos y tipos como antes
    documents = db.session.execute(
        text('''
            SELECT d.id, d.file_path, d.uploaded_at, d.status, dt.name AS type_name
            FROM documents d
            JOIN document_types dt ON d.type_id = dt.id
            WHERE d.user_id = :user_id
            ORDER BY d.uploaded_at DESC
        '''), {'user_id': user_id}
    ).fetchall()

    document_types = db.session.execute(text('SELECT id, name FROM document_types ORDER BY name ASC')).fetchall()
    user_processes = db.session.execute(text('SELECT * FROM processes WHERE user_id = :user_id ORDER BY updated_at DESC'), {'user_id': user_id}).fetchall()

    # Mensajes (enviados y recibidos por el usuario)
    messages = db.session.execute(
        text('''
            SELECT m.id, m.content, m.created_at, m.sender_id, m.is_read, u.first_name, u.last_name
            FROM messages m
            JOIN user u ON m.sender_id = u.id
            WHERE m.sender_id = :user_id OR m.receiver_id = :user_id
            ORDER BY m.created_at DESC
        '''), {'user_id': user_id}
    ).fetchall()

    # Stats
    total_docs = len(documents)
    approved_docs = sum(1 for d in documents if d.status == 'approved')
    pending_docs = sum(1 for d in documents if d.status == 'pending')
    rejected_docs = sum(1 for d in documents if d.status == 'rejected')

    # Asesor: el del proceso más reciente o, si no, el asignado al cliente
    asesor_id = user_processes[0].advisor_id if user_processes and user_processes[0].advisor_id else user.advisor_id
    asesor = db.session.get(User, asesor_id) if asesor_id else None

    # Al abrir el panel, los mensajes recibidos se marcan como leídos
    # (la plantilla recibe el estado anterior, así se ve cuántos eran nuevos)
    db.session.execute(text('UPDATE messages SET is_read = TRUE WHERE receiver_id = :user_id AND is_read = FALSE'), {'user_id': user_id})
    db.session.commit()

    return render_template(
        'dashboard.html',
        user=user,
        asesor=asesor,
        rejected_docs=rejected_docs,
        documents=documents,
        document_types=document_types,
        user_processes=user_processes,
        total_docs=total_docs,
        approved_docs=approved_docs,
        pending_docs=pending_docs,
        messages=messages
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

        if DEMO_MODE or not app.config['MAIL_USERNAME']:
            flash('¡Mensaje recibido! (Demo: no se envía ningún correo real.)', 'success')
            return redirect(url_for('contact'))

        try:
            msg = MailMessage(
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
    advisors = User.query.filter_by(role='advisor').order_by(User.id.desc()).all()
    clientes = User.query.filter_by(role='client').order_by(User.id.desc()).limit(200).all()
    admin = db.session.get(User, session['user_id'])
    if admin is None:
        session.clear()
        return redirect('/login')

    procesos = db.session.execute(
        text('''
            SELECT p.id, p.user_id, p.status, p.updated_at, p.visa_type, p.destination_country, p.advisor_name,
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

    por_estado = {}
    for p in procesos:
        por_estado[p.status] = por_estado.get(p.status, 0) + 1
    stats = {
        'clientes': User.query.filter_by(role='client').count(),
        'procesos': len(procesos),
        'activos': len(procesos) - por_estado.get('completed', 0),
        'por_estado': por_estado,
        'docs_pendientes': db.session.execute(text("SELECT COUNT(*) FROM documents WHERE status = 'pending'")).scalar(),
        'sin_asesor': User.query.filter_by(role='client', advisor_id=None).count(),
    }
    clientes_por_asesor = {}
    for c in clientes:
        if c.advisor_id:
            clientes_por_asesor[c.advisor_id] = clientes_por_asesor.get(c.advisor_id, 0) + 1

    return render_template(
        'admin_dashboard.html',
        admin=admin,
        stats=stats,
        clientes_por_asesor=clientes_por_asesor,
        clientes=clientes,
        procesos=procesos,
        advisors=advisors,
        documentos_por_usuario=documentos_por_usuario
    )

# NUEVO: Agregar asesor
@app.route('/admin/add_advisor', methods=['POST'])
@admin_required
def add_advisor():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not all([first_name, last_name, email]) or len(password) < 8:
        flash('Completa todos los campos (contraseña de 8 caracteres o más).', 'danger')
        return redirect('/admin/dashboard#asesores')

    if User.query.filter_by(email=email).first():
        flash('El correo ya está registrado', 'danger')
        return redirect('/admin/dashboard#asesores')

    hashed_password = generate_password_hash(password)

    new_advisor = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password,
        role='advisor'
    )
    db.session.add(new_advisor)
    db.session.commit()
    flash('Asesor creado correctamente', 'success')
    return redirect('/admin/dashboard')
# Asignar asesor a un cliente
@app.route('/admin/assign_advisor/<int:client_id>', methods=['POST'])
@admin_required
def assign_advisor_to_client(client_id):
    advisor_id = request.form.get('advisor_id')

    asesor = db.session.get(User, int(advisor_id)) if advisor_id and advisor_id.isdigit() else None
    if not asesor or asesor.role != 'advisor':
        flash('Debes seleccionar un asesor', 'danger')
        return redirect('/admin/dashboard#clientes')

    # Buscar el cliente
    cliente = db.session.get(User, client_id)
    if not cliente or cliente.role != 'client':
        flash('Cliente no encontrado', 'danger')
        return redirect('/admin/dashboard#clientes')

    # Asignar el asesor al cliente y a sus procesos: los mensajes del cliente
    # se envían al asesor del proceso, así que ambos deben coincidir
    cliente.advisor_id = asesor.id
    db.session.execute(
        text('UPDATE processes SET advisor_id = :a, advisor_name = :n WHERE user_id = :u'),
        {'a': asesor.id, 'n': f'{asesor.first_name} {asesor.last_name}', 'u': cliente.id},
    )
    db.session.commit()
    flash(f'{asesor.first_name} {asesor.last_name} es ahora el asesor de {cliente.first_name} {cliente.last_name}', 'success')
    return redirect('/admin/dashboard#clientes')

# NUEVO: Cambiar estado del proceso
@app.route('/admin/process/<int:id>/status', methods=['POST'])
@admin_required
def cambiar_status(id):
    nuevo_status = request.form.get('status')
    if nuevo_status not in ESTADOS_PROCESO:
        flash('Estado no válido', 'danger')
        return redirect('/admin/dashboard#procesos')
    proceso = db.session.execute(text('SELECT * FROM processes WHERE id = :id'), {'id': id}).first()

    if proceso:
        db.session.execute(text('UPDATE processes SET status = :status WHERE id = :id'), {'status': nuevo_status, 'id': id})
        db.session.commit()
        flash(f'Proceso marcado como «{ESTADOS_PROCESO[nuevo_status].lower()}»', 'success')
    return redirect('/admin/dashboard#procesos')
# NUEVO: Cambiar estado del documento
@app.route('/admin/document/<int:id>/status', methods=['POST'])
@admin_required
def change_document_status(id):
    nuevo_status = request.form.get('status')
    if nuevo_status not in ESTADOS_DOCUMENTO:
        flash('Estado no válido', 'danger')
        return redirect('/admin/dashboard#documentos')
    db.session.execute(
        text('UPDATE documents SET status = :status WHERE id = :id'),
        {'status': nuevo_status, 'id': id}
    )
    db.session.commit()
    flash(f'Documento marcado como «{ESTADOS_DOCUMENTO[nuevo_status].lower()}»', 'success')
    return redirect('/admin/dashboard#documentos')
    


# Ruta para subir documentos
@app.route('/upload_document', methods=['POST'])
@login_required
def upload_document():
    file = request.files.get('file')
    type_id = request.form.get('type_id')

    if not file or not type_id:
        flash('Por favor selecciona un archivo y tipo de documento', 'danger')
        return redirect('/dashboard#documentos')

    if not allowed_file(file.filename):
        flash('Tipo de archivo no permitido. Solo PDF, JPG, JPEG, PNG.', 'danger')
        return redirect('/dashboard#documentos')

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
    return redirect('/dashboard#documentos')
# Ruta para servir archivos subidos
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    # Antes cualquier usuario con sesión podía descargar los documentos de otros
    if session.get('role') != 'admin':
        propio = db.session.execute(
            text('SELECT 1 FROM documents WHERE file_path = :f AND user_id = :u'),
            {'f': filename, 'u': session['user_id']},
        ).first()
        if not propio:
            abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# NUEVO: Enviar mensaje al asesor
@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    sender_id = session['user_id']
    content = (request.form.get('message') or '').strip()[:2000]

    if not content:
        flash('El mensaje no puede estar vacío', 'danger')
        return redirect('/dashboard#mensajes')

    # Asesor del proceso más reciente o, si no tiene proceso, el asignado al cliente
    process = db.session.execute(
        text('SELECT advisor_id FROM processes WHERE user_id = :user_id ORDER BY updated_at DESC LIMIT 1'),
        {'user_id': sender_id}
    ).fetchone()
    remitente = db.session.get(User, sender_id)
    asesor_id = (process.advisor_id if process and process.advisor_id else None) or (remitente.advisor_id if remitente else None)

    if not asesor_id:
        flash('Todavía no tienes un asesor asignado. Te avisaremos en cuanto lo tengas.', 'warning')
        return redirect('/dashboard#mensajes')

    new_message = Message(
        sender_id=sender_id,
        receiver_id=asesor_id,
        content=content
    )
    db.session.add(new_message)
    db.session.commit()
    flash('Mensaje enviado correctamente', 'success')
    return redirect('/dashboard#mensajes')


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
