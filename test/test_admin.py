import pytest
from app import db, User
from werkzeug.security import generate_password_hash

def login_admin(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'admin'

def test_admin_dashboard_requires_login(client):
    response = client.get('/admin/dashboard')
    assert response.status_code == 302

def test_admin_dashboard_wrong_role(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'client'

    response = client.get('/admin/dashboard', follow_redirects=True)
    assert b'Acceso no autorizado' in response.data

def test_create_advisor(client):
    login_admin(client)

    response = client.post('/admin/add_advisor', data={
        'first_name': 'Adv',
        'last_name': 'Test',
        'email': 'advisor@test.com',
        'password': '1234'
    }, follow_redirects=True)

    advisor = User.query.filter_by(email='advisor@test.com').first()
    assert advisor is not None
    assert advisor.role == 'advisor'

def test_assign_advisor_to_client(client):
    login_admin(client)

    advisor = User(first_name="Adv", last_name="One",
                   email="a@test.com",
                   password=generate_password_hash("1234"),
                   role="advisor")

    client_user = User(first_name="Client", last_name="One",
                       email="c@test.com",
                       password=generate_password_hash("1234"),
                       role="client")

    db.session.add_all([advisor, client_user])
    db.session.commit()

    response = client.post(
        f'/admin/assign_advisor/{client_user.id}',
        data={'advisor_id': advisor.id},
        follow_redirects=True
    )

    updated_client = User.query.get(client_user.id)
    assert updated_client.advisor_id == advisor.id

def test_change_document_status_requires_admin(client):
    response = client.post('/admin/document/1/status', data={'status': 'approved'})
    assert response.status_code == 302
