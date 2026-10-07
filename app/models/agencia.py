from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Agencia(Base):
    __tablename__ = "agencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_agencia: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    departamento: Mapped[str] = mapped_column(String(100), nullable=False)
    departamento_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    provincia: Mapped[str] = mapped_column(String(100), nullable=False)
    distrito: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[str] = mapped_column(String(250), nullable=False)
    estado: Mapped[Optional[str]] = mapped_column(String(13), default="ACTIVO")
    creado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    actualizado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Agencia {self.codigo_agencia} - {self.nombre}>"
