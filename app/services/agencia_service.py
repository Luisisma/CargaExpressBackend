import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.models.agencia import Agencia
from app.schemas.agencia import AgenciaCreateRequest, AgenciaUpdateRequest
from app.services.audit_service import registrar_auditoria_operacion

logger = logging.getLogger(__name__)

DEPARTAMENTOS_MAP = {
    "amazonas": 1, "ancash": 2, "apurimac": 3, "apurímac": 3, "arequipa": 4,
    "ayacucho": 5, "cajamarca": 6, "callao": 7, "cusco": 8, "huancavelica": 9,
    "huanuco": 10, "huánuco": 10, "ica": 11, "junin": 12, "junín": 12,
    "la libertad": 13, "lambayeque": 14, "lima": 15, "loreto": 16,
    "madre de dios": 17, "moquegua": 18, "pasco": 19, "piura": 20,
    "puno": 21, "san martin": 22, "san martín": 22, "tacna": 23,
    "tumbes": 24, "ucayali": 25
}


class AgenciaService:
    """
    Servicio de Dominio para la Gestión de Sedes y Agencias Nacionales.
    Permite el mantenimiento de sedes operativas, validación de Ubigeos
    y auditoría inmutable de altas y modificaciones.
    """

    @classmethod
    def listar(
        cls,
        db: Session,
        busqueda: Optional[str] = None,
        departamento: Optional[str] = None,
        estado: Optional[str] = None
    ) -> List[Agencia]:
        stmt = select(Agencia).order_by(Agencia.id.asc())

        if estado and estado.strip():
            stmt = stmt.where(Agencia.estado.ilike(estado.strip()))

        if departamento and departamento.strip():
            stmt = stmt.where(Agencia.departamento.ilike(f"%{departamento.strip()}%"))

        if busqueda and busqueda.strip():
            term = f"%{busqueda.strip()}%"
            stmt = stmt.where(
                or_(
                    Agencia.nombre.ilike(term),
                    Agencia.provincia.ilike(term),
                    Agencia.distrito.ilike(term),
                    Agencia.direccion.ilike(term)
                )
            )

        return list(db.scalars(stmt).all())

    @classmethod
    def obtener_por_id(cls, db: Session, agencia_id: int) -> Agencia:
        agencia = db.get(Agencia, agencia_id)
        if not agencia:
            raise ValueError(f"No se encontró la agencia con ID {agencia_id}.")
        return agencia

    @classmethod
    def crear(
        cls,
        db: Session,
        req: AgenciaCreateRequest,
        usuario_id: int
    ) -> Agencia:
        # 1. Determinar o validar código de agencia
        if req.codigo_agencia:
            existente = db.scalar(select(Agencia).where(Agencia.codigo_agencia == req.codigo_agencia))
            if existente:
                raise ValueError(f"El código de agencia '{req.codigo_agencia}' ya se encuentra registrado.")
            codigo = req.codigo_agencia
        else:
            max_cod = db.scalar(select(func.max(Agencia.codigo_agencia))) or 1000
            codigo = max_cod + 1

        # 2. Asignar departamento_id si no vino
        dep_id = req.departamento_id
        if not dep_id:
            dep_clean = req.departamento.strip().lower()
            dep_id = DEPARTAMENTOS_MAP.get(dep_clean, 15)

        # 3. Crear entidad
        ahora = datetime.now(timezone.utc)
        nueva = Agencia(
            codigo_agencia=codigo,
            nombre=req.nombre.strip().upper(),
            departamento=req.departamento.strip().title(),
            departamento_id=dep_id,
            provincia=req.provincia.strip().title(),
            distrito=req.distrito.strip().title(),
            direccion=req.direccion.strip(),
            estado=req.estado or "habilitado",
            creado_por=usuario_id,
            creado_en=ahora,
            actualizado_en=ahora
        )

        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        # 4. Auditoría
        registrar_auditoria_operacion(
            db=db,
            usuario_id=usuario_id,
            accion="CREAR_AGENCIA",
            tabla_afectada="agencias",
            registro_id=nueva.id,
            valores_nuevos={
                "codigo_agencia": nueva.codigo_agencia,
                "nombre": nueva.nombre,
                "departamento": nueva.departamento,
                "provincia": nueva.provincia,
                "distrito": nueva.distrito,
                "estado": nueva.estado
            }
        )

        return nueva

    @classmethod
    def actualizar(
        cls,
        db: Session,
        agencia_id: int,
        req: AgenciaUpdateRequest,
        usuario_id: int
    ) -> Agencia:
        agencia = cls.obtener_por_id(db, agencia_id)
        valores_previos = {
            "nombre": agencia.nombre,
            "direccion": agencia.direccion,
            "distrito": agencia.distrito,
            "estado": agencia.estado
        }

        if req.nombre is not None:
            agencia.nombre = req.nombre.strip().upper()
        if req.departamento is not None:
            agencia.departamento = req.departamento.strip().title()
            dep_clean = agencia.departamento.lower()
            agencia.departamento_id = req.departamento_id or DEPARTAMENTOS_MAP.get(dep_clean, agencia.departamento_id)
        if req.provincia is not None:
            agencia.provincia = req.provincia.strip().title()
        if req.distrito is not None:
            agencia.distrito = req.distrito.strip().title()
        if req.direccion is not None:
            agencia.direccion = req.direccion.strip()
        if req.estado is not None:
            agencia.estado = req.estado

        agencia.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agencia)

        registrar_auditoria_operacion(
            db=db,
            usuario_id=usuario_id,
            accion="ACTUALIZAR_AGENCIA",
            tabla_afectada="agencias",
            registro_id=agencia.id,
            valores_previos=valores_previos,
            valores_nuevos={
                "nombre": agencia.nombre,
                "direccion": agencia.direccion,
                "distrito": agencia.distrito,
                "estado": agencia.estado
            }
        )

        return agencia

    @classmethod
    def toggle_estado(
        cls,
        db: Session,
        agencia_id: int,
        usuario_id: int
    ) -> Agencia:
        agencia = cls.obtener_por_id(db, agencia_id)
        estado_previo = agencia.estado
        nuevo_estado = "deshabilitado" if estado_previo == "habilitado" else "habilitado"
        agencia.estado = nuevo_estado
        agencia.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agencia)

        registrar_auditoria_operacion(
            db=db,
            usuario_id=usuario_id,
            accion="TOGGLE_ESTADO_AGENCIA",
            tabla_afectada="agencias",
            registro_id=agencia.id,
            valores_previos={"estado": estado_previo},
            valores_nuevos={"estado": nuevo_estado}
        )

        return agencia

