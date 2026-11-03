from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role, get_client_ip
from app.models.usuario import Usuario
from app.schemas.common import SuccessResponse
from app.schemas.caja import (
    ResumenCajaResponse,
    ArqueoCajaRequest,
    ArqueoCajaResponse,
    GestionSobrepagoRequest,
    GestionSobrepagoResponse
)
from app.services.caja_service import CajaService

router = APIRouter()


@router.get(
    "/resumen",
    response_model=SuccessResponse[ResumenCajaResponse],
    summary="Resumen operativo en tiempo real de la Caja",
    description="Calcula cobros en efectivo, billeteras digitales y arqueo teórico esperado para la sede y turno actual."
)
def obtener_resumen_caja(
    agencia_id: Optional[int] = Query(None, description="Filtrar por ID de agencia (solo para Administrador)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO"]))
):
    resumen = CajaService.obtener_resumen(
        db=db,
        current_user=current_user,
        agencia_id=agencia_id
    )
    return SuccessResponse(success=True, data=resumen)


@router.post(
    "/arqueo",
    response_model=SuccessResponse[ArqueoCajaResponse],
    summary="Registrar arqueo de caja y cierre de turno",
    description="Compara el efectivo físico declarado en el cajón contra el total teórico esperado y calcula descuadres."
)
def registrar_arqueo_caja(
    payload: ArqueoCajaRequest,
    request: Request,
    agencia_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO"])),
    client_ip: str = Depends(get_client_ip)
):
    resultado = CajaService.registrar_arqueo(
        db=db,
        current_user=current_user,
        payload=payload,
        agencia_id=agencia_id,
        client_ip=client_ip
    )
    return SuccessResponse(success=True, data=resultado)


@router.post(
    "/gestionar-sobrepago",
    response_model=SuccessResponse[GestionSobrepagoResponse],
    summary="Gestión de Sobrepagos Digitales y Prevención PLAFT (Yape/Plin)",
    description="Aplica el protocolo normativo SBS N° 789-2018 y Ley N° 28194. Bloquea devoluciones en efectivo superiores a S/ 20.00."
)
def gestionar_sobrepago(
    payload: GestionSobrepagoRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["CAJERO", "ADMINISTRADOR", "SUPERVISOR"])),
    client_ip: str = Depends(get_client_ip)
):
    resultado = CajaService.gestionar_sobrepago(
        db=db,
        current_user=current_user,
        payload=payload,
        client_ip=client_ip
    )
    return SuccessResponse(success=True, data=resultado)
