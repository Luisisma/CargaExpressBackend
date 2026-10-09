from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, require_role, get_client_ip
from app.models.usuario import Usuario
from app.models.agencia import Agencia
from app.schemas.common import SuccessResponse
from app.schemas.usuario import (
    UsuarioResponse,
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
    ToggleActivoResponse,
    Toggle2FAResponse
)
from app.services.audit_service import registrar_auditoria_operacion
from app.core.security import generate_totp_secret, get_totp_uri, generate_qr_base64

router = APIRouter()



def _mapear_usuario_response(u: Usuario) -> UsuarioResponse:
    """Helper para transformar el modelo SQLAlchemy a UsuarioResponse enriquecido."""
    return UsuarioResponse(
        id=u.id,
        codigo_trabajador=u.codigo_trabajador,
        dni=u.dni,
        nombres=u.nombres,
        apellidos=u.apellidos,
        nombre_completo=u.nombre_completo,
        email=u.email,
        tipo=u.tipo,
        agencia_id=u.agencia_id,
        agencia_nombre=u.agencia.nombre if u.agencia else None,
        numero_caja=u.numero_caja,
        licencia_conducir=u.licencia_conducir,
        activo=u.activo,
        bloqueado=u.bloqueado,
        totp_configurado=bool(u.totp_configurado),
        ultimo_login=u.ultimo_login,
        creado_en=u.creado_en
    )


@router.get(
    "",
    response_model=SuccessResponse[List[UsuarioResponse]],
    summary="Listar todos los colaboradores",
    description="Permite al administrador o supervisor consultar la lista de personal activo e inactivo."
)
def listar_usuarios(
    rol: Optional[str] = Query(None, description="Filtrar por rol: administrador, cajero, etc."),
    agencia_id: Optional[int] = Query(None, description="Filtrar por ID de agencia"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):

    stmt = select(Usuario).order_by(Usuario.id)
    if rol:
        stmt = stmt.where(Usuario.tipo == rol.strip().lower())
    if agencia_id:
        stmt = stmt.where(Usuario.agencia_id == agencia_id)

    usuarios = list(db.execute(stmt).scalars().all())
    return SuccessResponse(
        success=True,
        data=[_mapear_usuario_response(u) for u in usuarios]
    )


@router.post(
    "",
    response_model=SuccessResponse[UsuarioResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo colaborador",
    description="Registra un nuevo usuario con rol operativo específico (solo rol ADMINISTRADOR)."
)
def crear_usuario(
    req: UsuarioCreateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    # 1. Validar unicidad de DNI
    dni_existente = db.execute(select(Usuario).where(Usuario.dni == req.dni)).scalar_one_or_none()
    if dni_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un colaborador registrado con el DNI '{req.dni}'."
        )

    # 2. Validar unicidad de Email
    email_existente = db.execute(select(Usuario).where(func.lower(Usuario.email) == req.email.lower())).scalar_one_or_none()
    if email_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo electrónico '{req.email}' ya está en uso."
        )

    # 3. Validar agencia si fue especificada
    if req.agencia_id:
        agencia = db.get(Agencia, req.agencia_id)
        if not agencia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La agencia con ID {req.agencia_id} no existe en el sistema."
            )

    # 4. Generar código correlativo de trabajador
    max_codigo = db.execute(select(func.max(Usuario.codigo_trabajador))).scalar() or 0
    nuevo_codigo = max_codigo + 1

    # 5. Crear entidad
    nuevo_usuario = Usuario(
        codigo_trabajador=nuevo_codigo,
        dni=req.dni,
        nombres=req.nombres.strip().title(),
        apellidos=req.apellidos.strip().title(),
        email=req.email.lower().strip(),
        tipo=req.tipo,
        agencia_id=req.agencia_id,
        numero_caja=req.numero_caja if req.tipo == "cajero" else None,
        licencia_conducir=req.licencia_conducir.strip().upper() if req.licencia_conducir else None,
        activo=True,
        bloqueado=False,
        sesion_version=1,
        creado_por=current_user.id
    )
    nuevo_usuario.set_password(req.password)


    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Auditoría
    registrar_auditoria_operacion(
        db=db,
        tabla="usuarios",
        registro_id=nuevo_usuario.id,
        accion="CREAR_USUARIO",
        usuario_id=current_user.id,
        datos_nuevos={"dni": nuevo_usuario.dni, "email": nuevo_usuario.email, "rol": nuevo_usuario.tipo}
    )

    return SuccessResponse(
        success=True,
        data=_mapear_usuario_response(nuevo_usuario),
        message="Colaborador creado exitosamente con credenciales operativas."
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[UsuarioResponse],
    summary="Detalle de colaborador",
    description="Obtiene la ficha técnica de un colaborador."
)
def obtener_usuario(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):

    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Colaborador con ID {id} no encontrado."
        )
    return SuccessResponse(success=True, data=_mapear_usuario_response(usuario))


@router.put(
    "/{id}",
    response_model=SuccessResponse[UsuarioResponse],
    summary="Actualizar colaborador",
    description="Modifica datos de perfil, asignación de rol, agencia o resetea contraseña."
)
def actualizar_usuario(
    id: int,
    req: UsuarioUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Colaborador con ID {id} no encontrado."
        )

    # Validar email único si cambió
    if req.email and req.email.lower() != usuario.email.lower():
        email_dup = db.execute(select(Usuario).where(func.lower(Usuario.email) == req.email.lower())).scalar_one_or_none()
        if email_dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El correo electrónico '{req.email}' ya pertenece a otro colaborador."
            )
        usuario.email = req.email.lower().strip()

    if req.nombres:
        usuario.nombres = req.nombres.strip().title()
    if req.apellidos:
        usuario.apellidos = req.apellidos.strip().title()
    if req.tipo:
        usuario.tipo = req.tipo
    if req.agencia_id is not None:
        if req.agencia_id > 0:
            agencia = db.get(Agencia, req.agencia_id)
            if not agencia:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agencia no válida.")
        usuario.agencia_id = req.agencia_id
    if req.numero_caja is not None:
        usuario.numero_caja = req.numero_caja
    if req.licencia_conducir is not None:
        usuario.licencia_conducir = req.licencia_conducir.strip().upper() if req.licencia_conducir else None
    if req.activo is not None:
        usuario.activo = req.activo
    if req.password:
        usuario.set_password(req.password)

    db.commit()
    db.refresh(usuario)

    registrar_auditoria_operacion(
        db=db,
        tabla="usuarios",
        registro_id=usuario.id,
        accion="ACTUALIZAR_USUARIO",
        usuario_id=current_user.id,
        datos_nuevos={"rol": usuario.tipo, "activo": usuario.activo, "agencia_id": usuario.agencia_id}
    )

    return SuccessResponse(
        success=True,
        data=_mapear_usuario_response(usuario),
        message="Datos del colaborador actualizados correctamente."
    )


@router.patch(
    "/{id}/toggle-activo",
    response_model=SuccessResponse[ToggleActivoResponse],
    summary="Activar o desactivar usuario",
    description="Permite habilitar o deshabilitar rápidamente el acceso de un colaborador."
)
def toggle_activo(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    if id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta de administrador."
        )

    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Colaborador con ID {id} no encontrado."
        )

    usuario.activo = not usuario.activo
    # Si se desactiva, invalidamos sus tokens activos
    if not usuario.activo:
        usuario.sesion_version += 1

    db.commit()

    nuevo_estado_txt = "activado" if usuario.activo else "desactivado"
    return SuccessResponse(
        success=True,
        data=ToggleActivoResponse(
            id=usuario.id,
            nombres=usuario.nombre_completo,
            activo=usuario.activo,
            mensaje=f"Colaborador {usuario.nombre_completo} {nuevo_estado_txt} correctamente."
        )
    )


@router.patch(
    "/{id}/toggle-2fa",
    response_model=SuccessResponse[Toggle2FAResponse],
    summary="Activar o desactivar 2FA/MFA para un colaborador",
    description="Permite al Administrador activar MFA generando nuevo secreto y código QR, o desactivarlo para un usuario."
)
def toggle_2fa(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR"]))
):
    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Colaborador con ID {id} no encontrado."
        )

    if usuario.totp_configurado:
        # Desactivar MFA
        usuario.totp_configurado = False
        usuario.totp_secret = None
        db.commit()

        registrar_auditoria_operacion(
            db=db,
            tabla="usuarios",
            registro_id=usuario.id,
            accion="DESACTIVAR_2FA",
            usuario_id=current_user.id,
            datos_nuevos={"totp_configurado": False}
        )

        return SuccessResponse(
            success=True,
            data=Toggle2FAResponse(
                id=usuario.id,
                nombres=usuario.nombre_completo,
                totp_configurado=False,
                mensaje=f"Doble factor (2FA) desactivado para {usuario.nombre_completo}."
            )
        )
    else:
        # Activar MFA con nuevo secreto y QR
        secret = generate_totp_secret()
        usuario.totp_secret = secret
        usuario.totp_configurado = True
        db.commit()

        totp_uri = get_totp_uri(secret, usuario.email)
        qr_code = generate_qr_base64(totp_uri)

        registrar_auditoria_operacion(
            db=db,
            tabla="usuarios",
            registro_id=usuario.id,
            accion="ACTIVAR_2FA",
            usuario_id=current_user.id,
            datos_nuevos={"totp_configurado": True}
        )

        return SuccessResponse(
            success=True,
            data=Toggle2FAResponse(
                id=usuario.id,
                nombres=usuario.nombre_completo,
                totp_configurado=True,
                secret=secret,
                qr_code=qr_code,
                mensaje=f"Doble factor (2FA) activado para {usuario.nombre_completo}. Escanee el código QR con Google Authenticator."
            )
        )

