import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.auditoria import AuditoriaSeguridad, AuditoriaOperaciones

logger = logging.getLogger("security.audit")


def registrar_auditoria_seguridad(
    db: Session,
    evento: str,
    direccion_ip: str,
    usuario_id: Optional[int] = None,
    user_agent: Optional[str] = None,
    detalles: Optional[Dict[str, Any]] = None,
    nivel_riesgo: str = "INFO"
) -> AuditoriaSeguridad:
    """
    Registra un evento inmutable en la tabla de auditoría de seguridad.
    (OWASP A09:2021 Security Logging and Monitoring)
    """
    registro = AuditoriaSeguridad(
        usuario_id=usuario_id,
        evento=evento,
        direccion_ip=direccion_ip,
        user_agent=user_agent,
        detalles=detalles or {},
        nivel_riesgo=nivel_riesgo
    )
    db.add(registro)
    try:
        db.commit()
        db.refresh(registro)
    except Exception as e:
        logger.error(f"Error al persistir auditoría de seguridad: {e}")
        db.rollback()
    return registro


def registrar_auditoria_operacion(
    db: Session,
    tabla_afectada: str,
    registro_id: int,
    accion: str,
    direccion_ip: str,
    valores_previos: Optional[Dict[str, Any]] = None,
    valores_nuevos: Optional[Dict[str, Any]] = None,
    usuario_id: Optional[int] = None,
    request_id: Optional[str] = None
) -> AuditoriaOperaciones:
    """
    Registra una alteración de datos de negocio (INSERT, UPDATE, DELETE).
    """
    registro = AuditoriaOperaciones(
        tabla_afectada=tabla_afectada,
        registro_id=registro_id,
        accion=accion,
        valores_previos=valores_previos,
        valores_nuevos=valores_nuevos,
        usuario_id=usuario_id,
        direccion_ip=direccion_ip,
        request_id=request_id
    )
    db.add(registro)
    try:
        db.commit()
        db.refresh(registro)
    except Exception as e:
        logger.error(f"Error al persistir auditoría de operación: {e}")
        db.rollback()
    return registro
