from app import db, User
from werkzeug.security import generate_password_hash, check_password_hash

def test_create_user(client):
    user = User(
        first_name="Ana",
        last_name="Lopez",
        email="ana@test.com",
        password=generate_password_hash("1234")
    )
    db.session.add(user)
    db.session.commit()
    assert user.id is not None

def test_email_unique(client):
    user1 = User(first_name="A", last_name="B", email="dup@test.com", password="123")
    db.session.add(user1)
    db.session.commit()

    user2 = User(first_name="C", last_name="D", email="dup@test.com", password="123")
    db.session.add(user2)

    try:
        db.session.commit()
        assert False
    except:
        assert True

def test_password_hash():
    hashed = generate_password_hash("1234")
    assert check_password_hash(hashed, "1234")

def test_default_role(client):
    user = User(first_name="A", last_name="B", email="role@test.com", password="123")
    db.session.add(user)
    db.session.commit()
    assert user.role == "client"

def test_advisor_relationship(client):
    advisor = User(first_name="Adv", last_name="One", email="adv@test.com", password="123", role="advisor")
    client_user = User(first_name="Client", last_name="One", email="cli@test.com", password="123", advisor=advisor)
    db.session.add_all([advisor, client_user])
    db.session.commit()
    assert client_user.advisor.id == advisor.id
