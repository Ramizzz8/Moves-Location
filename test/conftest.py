import pytest
from sqlalchemy import text
from app import app, db
from werkzeug.security import generate_password_hash

# Tablas que la app consulta con SQL directo (no son modelos de SQLAlchemy),
# versión compatible con SQLite para los tests
TABLAS_SQL = [
    "CREATE TABLE IF NOT EXISTS document_types (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL)",
    "INSERT INTO document_types (id, name) VALUES (1, 'Pasaporte'), (2, 'Formulario de solicitud')",
    """CREATE TABLE IF NOT EXISTS processes (
        id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, advisor_id INTEGER, advisor_name VARCHAR(200),
        destination_country VARCHAR(80), visa_type VARCHAR(100), start_date DATE,
        status VARCHAR(50) DEFAULT 'pending', updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, type_id INTEGER NOT NULL,
        file_path VARCHAR(255) NOT NULL, status VARCHAR(20) DEFAULT 'pending',
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP)""",
]

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        for sentencia in TABLAS_SQL:
            db.session.execute(text(sentencia))
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()
        with db.engine.begin() as conexion:
            for tabla in ('documents', 'processes', 'document_types'):
                conexion.execute(text(f'DROP TABLE IF EXISTS {tabla}'))

@pytest.fixture
def init_database():
    from app import User
    with app.app_context():
        user = User(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            password=generate_password_hash("1234"),
            role="client"
        )
        db.session.add(user)
        db.session.commit()
        return user
