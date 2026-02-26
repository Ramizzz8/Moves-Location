import pytest
from app import app, db
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

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
