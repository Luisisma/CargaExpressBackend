from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.usuario import Usuario
from app.schemas.common import SuccessResponse
from app.schemas.agencia import (
    AgenciaResponse,
    AgenciaCreateRequest,
    AgenciaUpdateRequest
)
from app.services.agencia_service import AgenciaService

router = APIRouter()


@router.get(
    "",
    response_model=SuccessResponse[List[AgenciaResponse]],
    summary="Listado administrativo de agencias",
    description="Permite buscar y filtrar sedes por nombre, departamento o estado operativo."
)
def listar_agencias(
    busqueda: Optional[str] = Query(None, description="Buscar por nombre, distrito o dirección"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (habilitado/deshabilitado)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO", "ALMACEN"]))
):
    agencias = AgenciaService.listar(
        db=db,
        busqueda=busqueda,
        departamento=departamento,
        estado=estado
    )
    return SuccessResponse(
        success=True,
        data=[AgenciaResponse.model_validate(a) for a in agencias]
    )


@router.get(
    "/{agencia_id}",
    response_model=SuccessResponse[AgenciaResponse],
    summary="Detalle de una agencia",
    description="Obtiene información detallada de una sede específica por su identificador."
)
def obtener_agencia(
    agencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR"]))
):
    try:
        agencia = AgenciaService.obtener_por_id(db=db, agencia_id=agencia_id)
        return SuccessResponse(success=True, data=AgenciaResponse.model_validate(agencia))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=SuccessResponse[AgenciaResponse],
    summary="Crear nueva sede o agencia",
    description="Exclusivo para ADMINISTRADOR. Registra una nueva sucursal con validación de Ubigeo y auditoría."
)
def crear_agencia(
    req: AgenciaCreateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    try:
        nueva = AgenciaService.crear(db=db, req=req, usuario_id=current_user.id)
        return SuccessResponse(success=True, data=AgenciaResponse.model_validate(nueva))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{agencia_id}",
    response_model=SuccessResponse[AgenciaResponse],
    summary="Actualizar información de agencia",
    description="Exclusivo para ADMINISTRADOR. Modifica nombre, dirección o Ubigeo de una sede existente."
)
def actualizar_agencia(
    agencia_id: int,
    req: AgenciaUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    try:
        actualizada = AgenciaService.actualizar(
            db=db,
            agencia_id=agencia_id,
            req=req,
            usuario_id=current_user.id
        )
        return SuccessResponse(success=True, data=AgenciaResponse.model_validate(actualizada))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{agencia_id}/toggle-estado",
    response_model=SuccessResponse[AgenciaResponse],
    summary="Habilitar o Deshabilitar agencia",
    description="Exclusivo para ADMINISTRADOR. Alterna el estado operativo de una agencia."
)
def toggle_estado_agencia(
    agencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    try:
        modificada = AgenciaService.toggle_estado(
            db=db,
            agencia_id=agencia_id,
            usuario_id=current_user.id
        )
        return SuccessResponse(success=True, data=AgenciaResponse.model_validate(modificada))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

