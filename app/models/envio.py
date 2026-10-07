from datetime import datetime, date, timezone
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import Integer, String, Boolean, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Envio(Base):
    """
    Modelo representativo de la tabla 'envios' en cargaexpress_clean.sql.
    Núcleo operativo y financiero de la encomienda.
    """
    __tablename__ = "envios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_tracking: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    remitente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False)
    destinatario_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False)
    agencia_origen_id: Mapped[int] = mapped_column(Integer, ForeignKey("agencias.id"), nullable=False)
    agencia_destino_id: Mapped[int] = mapped_column(Integer, ForeignKey("agencias.id"), nullable=False)
    
    tipo_envio: Mapped[str] = mapped_column(String(19), nullable=False)  # 'agencia_agencia', 'agencia_domicilio'
    tipo_paquete: Mapped[str] = mapped_column(String(10), nullable=False)  # 'caja', 'sobre', 'paquete', 'saco'
    peso_kg: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    alto_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    ancho_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    largo_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    peso_volumetrico: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    direccion_recojo: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    direccion_entrega: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Desglose Contable y Tarifario
    monto_subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    monto_descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    monto_igv: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    precio_envio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    forma_pago: Mapped[str] = mapped_column(String(15), default="efectivo", nullable=False)
    estado_pago: Mapped[str] = mapped_column(String(10), default="pendiente", nullable=False)
    lugar_pago: Mapped[str] = mapped_column(String(10), default="origen", nullable=False)
    estado: Mapped[str] = mapped_column(String(15), default="registrado", nullable=False)
    
    fecha_estimada: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_entrega_real: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    imagen_recepcion: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    imagen_evidencia: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    tipo_documento: Mapped[str] = mapped_column(String(10), default="boleta", nullable=False)
    numero_documento: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    serie_documento: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    registrado_por_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    registrado_web: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    apertura_caja_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    courier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relaciones
    remitente = relationship("Cliente", foreign_keys=[remitente_id])
    destinatario = relationship("Cliente", foreign_keys=[destinatario_id])
    agencia_origen = relationship("Agencia", foreign_keys=[agencia_origen_id])
    agencia_destino = relationship("Agencia", foreign_keys=[agencia_destino_id])
    historial: Mapped[List["HistorialEnvio"]] = relationship("HistorialEnvio", back_populates="envio", cascade="all, delete-orphan", order_by="HistorialEnvio.creado_en")

    def __repr__(self) -> str:
        return f"<Envio {self.codigo_tracking} - {self.estado} (S/ {self.precio_envio})>"


class HistorialEnvio(Base):
    """
    Modelo representativo de la tabla 'historial_envios' en cargaexpress_clean.sql.
    Pistas de auditoría y tracking de hitos de la encomienda.
    """
    __tablename__ = "historial_envios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    envio_id: Mapped[int] = mapped_column(Integer, ForeignKey("envios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    ubicacion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    envio = relationship("Envio", back_populates="historial")

    def __repr__(self) -> str:
        return f"<HistorialEnvio {self.envio_id} [{self.estado}] {self.creado_en}>"
