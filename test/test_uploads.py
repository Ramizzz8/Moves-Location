import io

def login_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'client'

def test_upload_without_file(client):
    login_client(client)

    response = client.post('/upload_document', data={}, follow_redirects=True)
    assert b'Por favor selecciona un archivo' in response.data

def test_upload_invalid_extension(client):
    login_client(client)

    data = {
        'type_id': '1',
        'file': (io.BytesIO(b"fake content"), "file.exe")
    }

    response = client.post('/upload_document',
                           data=data,
                           content_type='multipart/form-data',
                           follow_redirects=True)

    assert b'Tipo de archivo no permitido' in response.data

def test_upload_valid_file(client):
    login_client(client)

    data = {
        'type_id': '1',
        'file': (io.BytesIO(b"fake content"), "file.pdf")
    }

    response = client.post('/upload_document',
                           data=data,
                           content_type='multipart/form-data',
                           follow_redirects=True)

    assert b'Documento subido correctamente' in response.data

def test_allowed_file_function():
    from app import allowed_file
    assert allowed_file("test.pdf") is True
    assert allowed_file("test.exe") is False
