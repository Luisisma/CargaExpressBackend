from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.api.deps import get_db, require_role
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.envio import Envio
from app.schemas.common import SuccessResponse
from app.schemas.cliente import ClienteListItem

router = APIRouter()


@router.get(
    "",
    response_model=SuccessResponse[List[ClienteListItem]],
    summary="Listar directorio de clientes remitentes y destinatarios",
    description="Permite buscar clientes registrados y ver su historial de encomiendas."
)
def listar_clientes(
    busqueda: Optional[str] = Query(None, description="Buscar por DNI/RUC o nombre"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO"]))
):
    stmt = select(Cliente).order_by(Cliente.id.desc())

    if busqueda and busqueda.strip():
        term = f"%{busqueda.strip()}%"
        stmt = stmt.where(
            or_(
                Cliente.numero_documento.ilike(term),
                Cliente.nombre_completo.ilike(term),
                Cliente.email.ilike(term)
            )
        )

    stmt = stmt.limit(limit).offset(offset)
    clientes_db = list(db.execute(stmt).scalars().all())

    items: List[ClienteListItem] = []
    for c in clientes_db:
        # Calcular total de envíos donde este cliente fue remitente o destinatario
        count_envios = db.scalar(
            select(func.count(Envio.id)).where(
                or_(
                    Envio.remitente_id == c.id,
                    Envio.destinatario_id == c.id
                )
            )
        ) or 0

        items.append(
            ClienteListItem(
                id=c.id,
                tipo_documento=c.tipo_documento.upper(),
                numero_documento=c.numero_documento,
                nombre_completo=c.nombre_completo,
                email=c.email,
                telefono=c.telefono,
                tipo_cliente=c.tipo_cliente,
                activo=c.activo,
                total_envios=int(count_envios),
                creado_en=c.creado_en
            )
        )

    return SuccessResponse(success=True, data=items)
