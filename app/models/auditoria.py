from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AuditoriaSeguridad(Base):
    """
    Tabla inmutable que registra eventos de autenticación, fallos, bloqueos
    y transiciones de segundo factor (OWASP A09:2021).
    """
    __tablename__ = "auditoria_seguridad"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    evento: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    direccion_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detalles: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    nivel_riesgo: Mapped[str] = mapped_column(String(10), default="INFO", nullable=False)  # 'INFO', 'WARN', 'CRITICAL'
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id], lazy="select")

    def __repr__(self) -> str:
        return f"<AuditoriaSeguridad {self.evento} - IP: {self.direccion_ip}>"


class AuditoriaOperaciones(Base):
    """
    Tabla inmutable que registra modificaciones (INSERT, UPDATE, DELETE) en datos críticos
    con valores previos y nuevos para trazabilidad completa.
    """
    __tablename__ = "auditoria_operaciones"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    tabla_afectada: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    registro_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(10), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    valores_previos: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    valores_nuevos: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    direccion_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id], lazy="select")

    def __repr__(self) -> str:
        return f"<AuditoriaOperaciones {self.accion} en {self.tabla_afectada} ID {self.registro_id}>"
