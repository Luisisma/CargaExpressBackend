import re
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


RolUsuarioLiteral = Literal[
    "administrador",
    "cajero",
    "supervisor",
    "almacen",
    "courier",
    "transportista"
]


class UsuarioResponse(BaseModel):
    id: int
    codigo_trabajador: int
    dni: str
    nombres: str
    apellidos: str
    nombre_completo: str
    email: str
    tipo: str
    agencia_id: Optional[int] = None
    agencia_nombre: Optional[str] = None
    numero_caja: Optional[int] = None
    licencia_conducir: Optional[str] = None
    activo: bool
    bloqueado: bool
    totp_configurado: Optional[bool] = False
    ultimo_login: Optional[datetime] = None
    creado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreateRequest(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8, description="DNI de 8 dígitos numéricos")
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=150)
    password: str = Field(..., min_length=8, max_length=100, description="Contraseña inicial del usuario (mínimo 8 caracteres)")
    tipo: RolUsuarioLiteral = Field(..., description="Rol operativo asignado")
    agencia_id: Optional[int] = Field(None, gt=0, description="ID de la agencia a la que pertenece")
    numero_caja: Optional[int] = Field(None, gt=0, description="Número de caja si es cajero")
    licencia_conducir: Optional[str] = Field(None, max_length=20, description="Brevete si es courier/transportista")

    model_config = ConfigDict(extra="forbid")

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v: str) -> str:
        v_limpio = v.strip()
        if not v_limpio.isdigit() or len(v_limpio) != 8:
            raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        return v_limpio

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        v_limpio = v.strip().lower()
        patron = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(patron, v_limpio):
            raise ValueError("El correo electrónico no tiene un formato válido.")
        return v_limpio

    @field_validator("password")
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


class UsuarioUpdateRequest(BaseModel):
    nombres: Optional[str] = Field(None, min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=150)
    tipo: Optional[RolUsuarioLiteral] = None
    agencia_id: Optional[int] = Field(None, gt=0)
    numero_caja: Optional[int] = None
    licencia_conducir: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="Nueva contraseña si se desea resetear")

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_limpio = v.strip().lower()
        patron = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(patron, v_limpio):
            raise ValueError("El correo electrónico no tiene un formato válido.")
        return v_limpio

    @field_validator("password")
    @classmethod
    def validar_password_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
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



class ToggleActivoResponse(BaseModel):
    id: int
    nombres: str
    activo: bool
    mensaje: str


class Toggle2FAResponse(BaseModel):
    id: int
    nombres: str
    totp_configurado: bool
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    mensaje: str

