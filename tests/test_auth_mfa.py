import pytest
import pyotp
from sqlalchemy import select
from app.models.auditoria import AuditoriaSeguridad
from app.models.usuario import Usuario


def test_security_headers(client):
    """Verifica que el middleware inyecte encabezados HTTP de seguridad y correlation ID."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Request-ID" in response.headers


def test_login_directo_sin_2fa(client, test_seed_data, db_session):
    """Usuario sin 2FA (ej. cajera) obtiene tokens definitivos de inmediato."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "70809020",
            "password": "CajeroPass123!"
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["mfa_requerido"] is False
    assert body["data"]["access_token"] is not None
    assert body["data"]["refresh_token"] is not None
    assert body["data"]["usuario"]["dni"] == "70809020"


def test_login_legacy_hash_compatibility(client, test_seed_data):
    """Usuario con hash heredado de Werkzeug en cargaexpress.sql puede autenticarse."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "legacy@cargaexpress.pe",
            "password": "LegacyPass123!"
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"] is not None


def test_login_con_2fa_requerido(client, test_seed_data):
    """Usuario con 2FA activo recibe temp_token y mfa_requerido=True."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "admin@cargaexpress.pe",
            "password": "AdminPass123!"
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["mfa_requerido"] is True
    assert body["data"]["temp_token"] is not None
    assert body["data"]["access_token"] is None


def test_verificacion_2fa_exitosa(client, test_seed_data):
    """El paso 2 valida el código TOTP de 6 dígitos y emite tokens de sesión."""
    # 1. Login inicial
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "admin@cargaexpress.pe",
            "password": "AdminPass123!"
        }
    )
    temp_token = login_resp.json()["data"]["temp_token"]

    # 2. Generar código TOTP real con el secreto configurado
    totp = pyotp.TOTP(test_seed_data["totp_secret"])
    codigo_valido = totp.now()

    # 3. Validar en /api/v1/auth/2fa
    verify_resp = client.post(
        "/api/v1/auth/2fa",
        json={
            "temp_token": temp_token,
            "codigo_totp": codigo_valido
        }
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"] is not None
    assert body["data"]["refresh_token"] is not None
    assert body["data"]["usuario"]["email"] == "admin@cargaexpress.pe"


def test_verificacion_2fa_codigo_invalido(client, test_seed_data):
    """Un código TOTP incorrecto devuelve HTTP 400 y registra auditoría."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "admin@cargaexpress.pe",
            "password": "AdminPass123!"
        }
    )
    temp_token = login_resp.json()["data"]["temp_token"]

    verify_resp = client.post(
        "/api/v1/auth/2fa",
        json={
            "temp_token": temp_token,
            "codigo_totp": "000000"
        }
    )
    assert verify_resp.status_code == 400
    assert "incorrecto" in verify_resp.json()["error"]["message"]


def test_proteccion_fuerza_bruta_bloqueo(client, test_seed_data, db_session):
    """5 intentos errados de contraseña activan el bloqueo temporal (anti-brute force)."""
    for _ in range(5):
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "identificador": "70809020",
                "password": "ClaveIncorrecta!"
            }
        )
        assert resp.status_code == 401

    # El sexto intento debe ser rechazado por bloqueo (HTTP 423)
    resp_bloqueado = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "70809020",
            "password": "ClaveIncorrecta!"
        }
    )
    assert resp_bloqueado.status_code == 423
    assert "bloqueada" in resp_bloqueado.json()["error"]["message"]


def test_endpoint_perfil_autenticado_me(client, test_seed_data):
    """Acceso a /auth/me usando token Bearer."""
    # Obtener token de login directo
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "70809020",
            "password": "CajeroPass123!"
        }
    )
    token = login_resp.json()["data"]["access_token"]

    # Consultar perfil
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    data = me_resp.json()["data"]
    assert data["dni"] == "70809020"
    assert data["tipo"] == "cajero"
    assert "password_hash" not in data  # Información sensible protegida


def test_logout_y_revocacion_global(client, test_seed_data):
    """El cierre de sesión incrementa sesion_version e invalida tokens previos inmediatamente."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "70809020",
            "password": "CajeroPass123!"
        }
    )
    token = login_resp.json()["data"]["access_token"]

    # Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["data"]["sesion_revocada"] is True

    # Intentar usar el token previo debe fallar con 401
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 401
    assert "revocada" in me_resp.json()["error"]["message"]


def test_registro_en_auditoria_seguridad(client, test_seed_data, db_session):
    """Verifica que los eventos queden grabados inmutablemente en la tabla auditoria_seguridad."""
    client.post(
        "/api/v1/auth/login",
        json={
            "identificador": "admin@cargaexpress.pe",
            "password": "ClaveErronea1!"
        }
    )

    eventos = db_session.scalars(select(AuditoriaSeguridad)).all()
    nombres_eventos = [e.evento for e in eventos]
    assert any("LOGIN_FALLIDO" in ev for ev in nombres_eventos)
