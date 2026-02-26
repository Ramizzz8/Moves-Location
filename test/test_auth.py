def test_register_success(client):
    response = client.post('/register', data={
        'first_name': 'Juan',
        'last_name': 'Perez',
        'email': 'juan@test.com',
        'country': 'Spain',
        'password': '1234',
        'confirm_password': '1234'
    }, follow_redirects=True)

    assert response.status_code == 200

def test_register_password_mismatch(client):
    response = client.post('/register', data={
        'first_name': 'Juan',
        'last_name': 'Perez',
        'email': 'juan2@test.com',
        'country': 'Spain',
        'password': '1234',
        'confirm_password': '9999'
    }, follow_redirects=True)

    assert b'Las contrase' in response.data

def test_login_success(client, init_database):
    response = client.post('/login', data={
        'email': 'test@test.com',
        'password': '1234'
    }, follow_redirects=True)

    assert response.status_code == 200

def test_login_wrong_password(client, init_database):
    response = client.post('/login', data={
        'email': 'test@test.com',
        'password': 'wrong'
    }, follow_redirects=True)

    assert b'Credenciales incorrectas' in response.data

def test_login_required_redirect(client):
    response = client.get('/dashboard')
    assert response.status_code == 302
