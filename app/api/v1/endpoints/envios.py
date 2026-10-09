from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, desc

from app.api.deps import get_db, require_role
from app.models.usuario import Usuario
from app.models.envio import Envio, HistorialEnvio
from app.models.cliente import Cliente
from app.models.agencia import Agencia
from app.schemas.common import SuccessResponse
from app.schemas.envio import (
    EnvioListItem,
    EnvioDetalleResponse,
    ClienteDetalle,
    AgenciaDetalle,
    HistorialDetalle,
    RecepcionEnvioRequest,
    DespachoArriboRequest,
    EntregaEnvioRequest
)
from app.services.envio_service import EnvioService

router = APIRouter()



@router.get(
    "",
    response_model=SuccessResponse[List[EnvioListItem]],
    summary="Listar envíos y despachos",
    description="Permite buscar y filtrar encomiendas por estado logístico, agencia o texto libre."
)
def listar_envios(
    estado: Optional[str] = Query(None, description="Filtrar por estado: registrado, en_almacen_origen, en_transito, entregado"),
    busqueda: Optional[str] = Query(None, description="Buscar por código de tracking o nombre de remitente"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO", "ALMACEN", "COURIER", "TRANSPORTISTA"]))
):
    stmt = (
        select(Envio)
        .order_by(desc(Envio.creado_en))
    )

    if estado and estado.strip():
        stmt = stmt.where(Envio.estado == estado.strip().lower())

    if busqueda and busqueda.strip():
        term = f"%{busqueda.strip()}%"
        stmt = stmt.join(Envio.remitente).where(
            or_(
                Envio.codigo_tracking.ilike(term),
                Cliente.nombre_completo.ilike(term),
                Cliente.numero_documento.ilike(term)
            )
        )

    stmt = stmt.limit(limit).offset(offset)
    envios_db = list(db.execute(stmt).scalars().all())

    items: List[EnvioListItem] = []
    for e in envios_db:
        items.append(
            EnvioListItem(
                id=e.id,
                codigo_tracking=e.codigo_tracking,
                origen=e.agencia_origen.nombre if e.agencia_origen else "Origen N/D",
                destino=e.agencia_destino.nombre if e.agencia_destino else "Destino N/D",
                remitente=e.remitente.nombre_completo if e.remitente else "Sin remitente",
                destinatario=e.destinatario.nombre_completo if e.destinatario else "Sin destinatario",
                total=float(e.precio_envio or 0.0),
                estado=e.estado,
                estado_pago=e.estado_pago,
                tipo_envio=e.tipo_envio,
                tipo_paquete=e.tipo_paquete,
                peso_kg=float(e.peso_kg or 0.0),
                creado_en=e.creado_en
            )
        )

    return SuccessResponse(success=True, data=items)


@router.get(
    "/{identificador}",
    response_model=SuccessResponse[EnvioDetalleResponse],
    summary="Detalle completo de una encomienda",
    description="Obtiene la ficha técnica completa con remitente, destinatario, desglose tarifario y cronología."
)
def obtener_envio_detalle(
    identificador: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO", "ALMACEN", "COURIER", "TRANSPORTISTA"]))
):
    stmt = select(Envio)
    if identificador.isdigit():
        stmt = stmt.where(Envio.id == int(identificador))
    else:
        stmt = stmt.where(Envio.codigo_tracking == identificador.strip().upper())

    envio = db.execute(stmt).scalar_one_or_none()
    if not envio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la encomienda '{identificador}'."
        )

    remitente_data = ClienteDetalle(
        id=envio.remitente.id,
        tipo_documento=envio.remitente.tipo_documento,
        numero_documento=envio.remitente.numero_documento,
        nombre_completo=envio.remitente.nombre_completo,
        email=envio.remitente.email,
        telefono=envio.remitente.telefono,
        direccion=envio.direccion_recojo
    )

    destinatario_data = ClienteDetalle(
        id=envio.destinatario.id,
        tipo_documento=envio.destinatario.tipo_documento,
        numero_documento=envio.destinatario.numero_documento,
        nombre_completo=envio.destinatario.nombre_completo,
        email=envio.destinatario.email,
        telefono=envio.destinatario.telefono,
        direccion=envio.direccion_entrega
    )

    agencia_origen_data = AgenciaDetalle(
        id=envio.agencia_origen.id,
        codigo_agencia=envio.agencia_origen.codigo_agencia,
        nombre=envio.agencia_origen.nombre,
        departamento=envio.agencia_origen.departamento,
        provincia=envio.agencia_origen.provincia,
        distrito=envio.agencia_origen.distrito,
        direccion=envio.agencia_origen.direccion
    )

    agencia_destino_data = AgenciaDetalle(
        id=envio.agencia_destino.id,
        codigo_agencia=envio.agencia_destino.codigo_agencia,
        nombre=envio.agencia_destino.nombre,
        departamento=envio.agencia_destino.departamento,
        provincia=envio.agencia_destino.provincia,
        distrito=envio.agencia_destino.distrito,
        direccion=envio.agencia_destino.direccion
    )

    historial_items = [
        HistorialDetalle(
            id=h.id,
            estado=h.estado,
            descripcion=h.descripcion,
            ubicacion=h.ubicacion,
            creado_en=h.creado_en
        )
        for h in (envio.historial or [])
    ]

    detalle = EnvioDetalleResponse(
        id=envio.id,
        codigo_tracking=envio.codigo_tracking,
        tipo_envio=envio.tipo_envio,
        tipo_paquete=envio.tipo_paquete,
        peso_kg=float(envio.peso_kg or 0.0),
        peso_volumetrico=float(envio.peso_volumetrico) if envio.peso_volumetrico else None,
        alto_cm=float(envio.alto_cm) if envio.alto_cm else None,
        ancho_cm=float(envio.ancho_cm) if envio.ancho_cm else None,
        largo_cm=float(envio.largo_cm) if envio.largo_cm else None,
        descripcion=envio.descripcion,
        direccion_recojo=envio.direccion_recojo,
        direccion_entrega=envio.direccion_entrega,
        monto_subtotal=float(envio.monto_subtotal or 0.0),
        monto_igv=float(envio.monto_igv or 0.0),
        precio_envio=float(envio.precio_envio or 0.0),
        forma_pago=envio.forma_pago,
        estado_pago=envio.estado_pago,
        lugar_pago=envio.lugar_pago,
        estado=envio.estado,
        tipo_documento=envio.tipo_documento,
        numero_documento=envio.numero_documento,
        serie_documento=envio.serie_documento,
        remitente=remitente_data,
        destinatario=destinatario_data,
        agencia_origen=agencia_origen_data,
        agencia_destino=agencia_destino_data,
        historial=historial_items,
        creado_en=envio.creado_en,
        actualizado_en=envio.actualizado_en
    )

    return SuccessResponse(success=True, data=detalle)

@router.post(
    "/{identificador}/recepcionar",
    response_model=SuccessResponse[str],
    summary="Recepcionar paquete en Agencia",
    description="Permite al Cajero confirmar la recepción del bulto físico. Si estaba pendiente de pago, lo marca como pagado."
)
def recepcionar_envio(
    identificador: str,
    req: RecepcionEnvioRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["CAJERO", "ADMINISTRADOR", "SUPERVISOR", "ALMACEN"]))
):
    try:
        EnvioService.recepcionar(
            db=db,
            codigo_tracking=identificador,
            usuario_id=current_user.id,
            agencia_id=current_user.agencia_id,
            req=req
        )
        return SuccessResponse(success=True, data="El envío ha sido recepcionado correctamente.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/{identificador}/despachar",
    response_model=SuccessResponse[str],
    summary="Despachar paquete a ruta",
    description="Permite al Almacenero/Despachador subir el paquete al camión, pasando a estado en_ruta."
)
def despachar_envio(
    identificador: str,
    req: DespachoArriboRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "ALMACEN", "TRANSPORTISTA", "COURIER"]))
):
    try:
        EnvioService.despachar(
            db=db,
            codigo_tracking=identificador,
            usuario_id=current_user.id,
            agencia_id=current_user.agencia_id,
            notas=req.notas
        )
        return SuccessResponse(success=True, data="El envío ha sido despachado exitosamente (En Ruta).")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/{identificador}/arribar",
    response_model=SuccessResponse[str],
    summary="Recepcionar paquete en destino",
    description="Permite al personal destino recibir el camión, pasando el paquete a en_agencia_destino."
)
def arribar_envio(
    identificador: str,
    req: DespachoArriboRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "ALMACEN", "CAJERO"]))
):
    try:
        EnvioService.arribar(
            db=db,
            codigo_tracking=identificador,
            usuario_id=current_user.id,
            agencia_id=current_user.agencia_id,
            notas=req.notas
        )
        return SuccessResponse(success=True, data="El envío ha arribado a la agencia de destino correctamente.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{identificador}/entregar",
    response_model=SuccessResponse[str],
    summary="Entregar encomienda al destinatario",
    description="Permite registrar la entrega física exigiendo DNI de quien recoge, cerrando formalmente el ciclo del paquete."
)
def entregar_envio(
    identificador: str,
    req: EntregaEnvioRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["CAJERO", "ADMINISTRADOR", "SUPERVISOR", "COURIER", "ALMACEN"]))
):
    try:
        EnvioService.entregar(
            db=db,
            codigo_tracking=identificador,
            usuario_id=current_user.id,
            agencia_id=current_user.agencia_id,
            req=req
        )
        return SuccessResponse(success=True, data="La encomienda ha sido entregada exitosamente al destinatario.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



