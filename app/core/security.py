import base64
from io import BytesIO
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
import bcrypt
from werkzeug.security import check_password_hash as werkzeug_check_password
import pyotp
import qrcode
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra su hash almacenado.
    Soporta bcrypt nativo (con truncamiento seguro a 72 bytes) y hashes heredados
    de Werkzeug (scrypt / pbkdf2) para permitir la migración transparente de usuarios existentes.
    """
    if not hashed_password or not plain_password:
        return False

    # 1. Si el hash proviene de Werkzeug (scrypt:... o pbkdf2:...)
    if hashed_password.startswith(("scrypt:", "pbkdf2:")):
        return werkzeug_check_password(hashed_password, plain_password)

    # 2. Verificación estándar Bcrypt nativo
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        # Fallback a Werkzeug por si el prefijo difiere
        try:
            return werkzeug_check_password(hashed_password, plain_password)
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """Genera hash bcrypt seguro con factor de coste de 12 rondas."""
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_token(
    payload_data: Dict[str, Any],
    expires_delta: timedelta,
    scope: str = "access"
) -> str:
    """Genera un JWT firmado con HS256 conteniendo claims de seguridad."""
    now = datetime.now(timezone.utc)
    to_encode = payload_data.copy()
    to_encode.update({
        "exp": now + expires_delta,
        "iat": now,
        "scope": scope
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_temp_token(user_id: int) -> str:
    """Emite un token temporal de 5 minutos exclusivo para la verificación 2FA."""
    expires = timedelta(minutes=settings.TEMP_TOKEN_EXPIRE_MINUTES)
    return create_token({"sub": str(user_id)}, expires_delta=expires, scope="mfa_pending")


def create_access_token(
    user_id: int,
    rol: str,
    agencia_id: Optional[int],
    sesion_version: int
) -> str:
    """Emite Access Token con claims completos de rol y control de sesión (30 min)."""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "rol": rol,
        "agencia_id": agencia_id,
        "sesion_version": sesion_version
    }
    return create_token(payload, expires_delta=expires, scope="access")


def create_refresh_token(user_id: int, sesion_version: int) -> str:
    """Emite Refresh Token para renovar sesión sin volver a solicitar credenciales (7 días)."""
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "sesion_version": sesion_version
    }
    return create_token(payload, expires_delta=expires, scope="refresh")


def decode_token(token: str, expected_scope: Optional[str] = None) -> Dict[str, Any]:
    """
    Decodifica y valida un JWT. Lanza jwt.PyJWTError si el token es inválido,
    ha expirado o no coincide con el scope esperado.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    if expected_scope and payload.get("scope") != expected_scope:
        raise jwt.InvalidTokenError(f"Scope inválido. Se esperaba '{expected_scope}'.")
    return payload


# ==============================================================================
# 2FA / TOTP (Time-based One-Time Password)
# ==============================================================================

def generate_totp_secret() -> str:
    """Genera una clave secreta aleatoria en Base32 para TOTP."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Genera la URI otpauth para vincular en Google Authenticator o Authy."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="CargaExpress Peru")


def generate_qr_base64(totp_uri: str) -> str:
    """Genera el código QR de configuración 2FA en formato imagen Base64 PNG."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{qr_base64}"


def verify_totp_code(secret: str, code: str) -> bool:
    """Verifica el código de 6 dígitos considerando una ventana de tolerancia de ±30 segundos."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)
