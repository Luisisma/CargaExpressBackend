from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Cliente(Base):
    """
    Modelo representativo de la tabla 'clientes' en cargaexpress_clean.sql.
    Soporta clientes tipo 'persona_natural' (DNI, CE, PAS) y 'empresa' (RUC).
    """
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tipo_documento: Mapped[str] = mapped_column(String(3), nullable=False)  # 'dni', 'ruc', 'ce', 'pas'
    numero_documento: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    persona_contacto: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tipo_cliente: Mapped[str] = mapped_column(String(15), default="persona_natural", nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    actualizado_por: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Cliente {self.tipo_documento}:{self.numero_documento} - {self.nombre_completo}>"
