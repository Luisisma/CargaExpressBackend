from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import SuccessResponse
from app.schemas.publico import (
    AgenciaPublicaResponse,
    CotizacionRequest,
    CotizacionResponse,
    TrackingPublicoResponse,
    ClientePublicoResponse,
    RegistroPedidoPublicoRequest,
    PedidoCreadoResponse,
    CancelarPedidoRequest,
    CancelarPedidoResponse
)
from app.services.publico_service import PublicoService

router = APIRouter()


@router.get(
    "/agencias",
    response_model=SuccessResponse[List[AgenciaPublicaResponse]],
    summary="Listado público de agencias operativas",
    description="Retorna las sedes y agencias habilitadas para selectores de cotización y despacho."
)
def listar_agencias(db: Session = Depends(get_db)):
    agencias = PublicoService.listar_agencias_activas(db)
    return SuccessResponse(
        success=True,
        data=[AgenciaPublicaResponse.model_validate(a) for a in agencias]
    )


@router.post(
    "/cotizar",
    response_model=SuccessResponse[CotizacionResponse],
    summary="Cotizador oficial de envíos",
    description="Calcula el flete total considerando peso físico, peso volumétrico y recargo a domicilio en servidor."
)
def cotizar_envio(req: CotizacionRequest):
    resultado = PublicoService.cotizar(req)
    return SuccessResponse(success=True, data=resultado)


@router.get(
    "/tracking/{codigo}",
    response_model=SuccessResponse[TrackingPublicoResponse],
    summary="Rastreo de envíos en tiempo real",
    description="Consulta el estado de una encomienda por su código de tracking con enmascaramiento estricto de PII."
)
def rastrear_envio(codigo: str, db: Session = Depends(get_db)):
    resultado = PublicoService.tracking(db, codigo)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún envío asociado al código '{codigo.upper()}'."
        )
    return SuccessResponse(success=True, data=resultado)


@router.get(
    "/buscar-cliente/{documento}",
    response_model=SuccessResponse[ClientePublicoResponse],
    summary="Consulta rápida de cliente por DNI/RUC",
    description="Permite el autocompletado de clientes recurrentes en formularios web protegiendo datos sensibles."
)
def buscar_cliente(documento: str, db: Session = Depends(get_db)):
    resultado = PublicoService.buscar_cliente(db, documento)
    return SuccessResponse(success=True, data=resultado)


@router.post(
    "/pedidos/registrar",
    response_model=SuccessResponse[PedidoCreadoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Pre-registro web de encomienda",
    description="Registra un nuevo envío de encomienda desde el portal público con cálculo contable en servidor."
)
def registrar_pedido(
    req: RegistroPedidoPublicoRequest,
    db: Session = Depends(get_db)
):
    try:
        resultado = PublicoService.registrar_pedido_web(db, req)
        return SuccessResponse(success=True, data=resultado)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

@router.post(
    "/pedidos/{codigo}/cancelar",
    response_model=SuccessResponse[CancelarPedidoResponse],
    summary="Cancelación de Pre-registro Web",
    description="Permite al remitente cancelar voluntariamente un envío no pagado ni despachado."
)
def cancelar_pedido(
    codigo: str,
    req: CancelarPedidoRequest,
    db: Session = Depends(get_db)
):
    try:
        resultado = PublicoService.cancelar_pedido_web(db, codigo, req)
        return SuccessResponse(success=True, data=resultado)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

