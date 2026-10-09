import re
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class LoginRequestSchema(BaseModel):
    """Esquema de credenciales de entrada para iniciar sesión."""
    identificador: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="DNI (8 dígitos) o Correo Electrónico del empleado"
    )
    password: str = Field(
        ...,
        min_length=4,
        max_length=128,
        description="Contraseña del usuario"
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UserProfileData(BaseModel):
    """Datos de perfil de usuario sin exponer contraseñas ni secretos."""
    id: int
    codigo_trabajador: int
    dni: str
    nombres: str
    apellidos: str
    nombre_completo: str
    email: str
    tipo: str
    agencia_id: Optional[int] = None
    numero_caja: Optional[int] = None
    totp_configurado: bool
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class LoginResponseData(BaseModel):
    """Respuesta tras el paso 1 de autenticación."""
    mfa_requerido: bool
    temp_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    usuario: Optional[UserProfileData] = None
    qr_code: Optional[str] = None
    secret_manual: Optional[str] = None


class TwoFactorVerifySchema(BaseModel):
    """Esquema para verificar el código TOTP de 6 dígitos en el paso 2."""
    temp_token: str = Field(..., description="Token temporal de 5 minutos emitido en /auth/login")
    codigo_totp: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="Código numérico de 6 dígitos de Google Authenticator / Authy"
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TokenResponseData(BaseModel):
    """Par de tokens definitivos emitidos al completar la autenticación."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UserProfileData


class RefreshTokenSchema(BaseModel):
    """Solicitud de renovación de Access Token."""
    refresh_token: str = Field(..., description="Refresh Token válido emitido por la API")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SetupTwoFactorData(BaseModel):
    """Datos entregados al empleado para vincular su aplicación 2FA."""
    secret: str = Field(..., description="Clave secreta en Base32 para ingreso manual")
    qr_code: str = Field(..., description="Imagen del código QR en formato data:image/png;base64")
    otpauth_url: str


class ConfirmTwoFactorSchema(BaseModel):
    """Confirmación del primer código TOTP para activar 2FA de forma permanente."""
    codigo_totp: str = Field(..., pattern=r"^\d{6}$", description="Código de 6 dígitos generado por la app")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SolicitarRecuperacionSchema(BaseModel):
    """Solicitud de recuperación de contraseña vía DNI o Correo Electrónico."""
    identificador: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="DNI (8 dígitos) o Correo Electrónico registrado del empleado"
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RestablecerPasswordSchema(BaseModel):
    """Esquema para definir una nueva contraseña utilizando el token firmado."""
    token: str = Field(..., min_length=10, description="Token JWT de recuperación recibido por correo")
    nueva_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nueva contraseña segura para la cuenta"
    )
    codigo_totp: Optional[str] = Field(
        None,
        pattern=r"^\d{6}$",
        description="Código de 6 dígitos si la cuenta tiene 2FA configurado"
    )

    @field_validator("nueva_password")
    @classmethod
    def validar_complejidad_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe incluir al menos una letra mayúscula (A-Z).")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe incluir al menos una letra minúscula (a-z).")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe incluir al menos un número (0-9).")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\/~`]", v):
            raise ValueError("La contraseña debe incluir al menos un símbolo o carácter especial (!@#$%...).")
        return v

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
