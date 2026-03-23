"""Batería de 30 pruebas simples de validación usando lógica de app.py."""

from types import SimpleNamespace

import pytest
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash


# Evita que app.py intente crear tablas remotas al importarse.
_original_create_all = SQLAlchemy.create_all
SQLAlchemy.create_all = lambda self: None
import app as app_module  # noqa: E402
SQLAlchemy.create_all = _original_create_all


class FakeUserQuery:
    def __init__(self, users_by_email):
        self.users_by_email = users_by_email
        self._last_email = None

    def filter_by(self, email):
        self._last_email = email
        return self

    def first(self):
        return self.users_by_email.get(self._last_email)


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("doc.pdf", True),
        ("doc.PDF", True),
        ("imagen.jpg", True),
        ("imagen.jpeg", True),
        ("imagen.png", True),
        ("carta.doc", True),
        ("carta.docx", True),
        ("nota.txt", True),
        ("sin_extension", False),
        ("archivo.exe", False),
        ("archivo.zip", False),
        ("archivo", False),
        (".env", False),
        ("doble.nombre.pdf", True),
        ("espacio final .pdf", True),
        ("mayusculas.JPEG", True),
        ("mal.jpg.exe", False),
        ("solo_punto.", False),
        ("/ruta/foto.png", True),
        ("CAPS.DOCX", True),
    ],
)
def test_allowed_file_bateria(filename, expected):
    assert app_module.allowed_file(filename) is expected


@pytest.mark.parametrize(
    "email,password,users_by_email,expected_redirect",
    [
        (
            "cliente@test.com",
            "1234",
            {
                "cliente@test.com": SimpleNamespace(
                    id=1,
                    role="client",
                    password=generate_password_hash("1234"),
                )
            },
            "/dashboard",
        ),
        (
            "admin@test.com",
            "admin123",
            {
                "admin@test.com": SimpleNamespace(
                    id=2,
                    role="admin",
                    password=generate_password_hash("admin123"),
                )
            },
            "/admin/dashboard",
        ),
        (
            "cliente@test.com",
            "mala",
            {
                "cliente@test.com": SimpleNamespace(
                    id=1,
                    role="client",
                    password=generate_password_hash("1234"),
                )
            },
            "/login",
        ),
        ("noexiste@test.com", "1234", {}, "/login"),
        ("", "1234", {}, "/login"),
        ("cliente@test.com", "", {}, "/login"),
        (
            "CLIENTE@test.com",
            "1234",
            {
                "cliente@test.com": SimpleNamespace(
                    id=1,
                    role="client",
                    password=generate_password_hash("1234"),
                )
            },
            "/login",
        ),
        (
            " cliente@test.com",
            "1234",
            {
                "cliente@test.com": SimpleNamespace(
                    id=1,
                    role="client",
                    password=generate_password_hash("1234"),
                )
            },
            "/login",
        ),
        (
            "cliente@test.com ",
            "1234",
            {
                "cliente@test.com": SimpleNamespace(
                    id=1,
                    role="client",
                    password=generate_password_hash("1234"),
                )
            },
            "/login",
        ),
        (
            "cliente@test.com",
            "1234 ",
            {
                "cliente@test.com": SimpleNamespace(
                    id=1,
                    role="client",
                    password=generate_password_hash("1234"),
                )
            },
            "/login",
        ),
    ],
)
def test_login_bateria(monkeypatch, client, email, password, users_by_email, expected_redirect):
    monkeypatch.setattr(app_module, "User", SimpleNamespace(query=FakeUserQuery(users_by_email)))

    response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert expected_redirect in response.headers["Location"]
