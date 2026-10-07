from datetime import datetime, date
from typing import Optional
from sqlalchemy import Integer, String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.core.security import verify_password, get_password_hash


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_trabajador: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    dni: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(13), nullable=False)  # 'administrador', 'cajero', 'supervisor', 'almacen', 'courier', 'transportista'
    numero_caja: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    licencia_conducir: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Parámetros 2FA / TOTP
    totp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    totp_configurado: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    # Control de intentos y bloqueos (anti fuerza bruta)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    bloqueado_hasta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Mejoras de Seguridad y Auditoría
    agencia_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("agencias.id"), nullable=True, index=True)
    ultimo_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ultimo_cambio_password: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sesion_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    creado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    actualizado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relación con Agencia
    agencia = relationship("Agencia", foreign_keys=[agencia_id], lazy="joined")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    def check_password(self, plain_password: str) -> bool:
        """Verifica la contraseña contra el hash almacenado."""
        return verify_password(plain_password, self.password_hash)

    def set_password(self, plain_password: str) -> None:
        """Asigna una nueva contraseña con hash bcrypt seguro e invalida tokens previos."""
        self.password_hash = get_password_hash(plain_password)
        self.ultimo_cambio_password = datetime.utcnow()
        self.sesion_version += 1  # Invalida todas las sesiones JWT emitidas anteriormente

    def __repr__(self) -> str:
        return f"<Usuario {self.dni} - {self.tipo}>"
