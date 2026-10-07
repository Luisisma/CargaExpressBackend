from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_client_ip, get_user_agent
from app.models.usuario import Usuario
from app.schemas.common import EnvelopeResponse
from app.schemas.auth import (
    LoginRequestSchema,
    LoginResponseData,
    TwoFactorVerifySchema,
    TokenResponseData,
    RefreshTokenSchema,
    UserProfileData,
    SetupTwoFactorData,
    ConfirmTwoFactorSchema
)
from app.services.auth_service import (
    procesar_login,
    procesar_verificacion_2fa,
    procesar_renovacion_token,
    generar_configuracion_2fa,
    activar_2fa
)
from app.services.audit_service import registrar_auditoria_seguridad

router = APIRouter(prefix="/auth", tags=["Autenticación y Seguridad"])


@router.post(
    "/login",
    response_model=EnvelopeResponse[LoginResponseData],
    summary="Paso 1: Inicio de sesión con credenciales",
    description="Valida DNI/correo y contraseña. Si el usuario tiene 2FA habilitado, emite un token temporal de 5 minutos; caso contrario, emite tokens de sesión completos."
)
def login(
    payload: LoginRequestSchema,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    resultado = procesar_login(
        db=db,
        identificador=payload.identificador,
        password=payload.password,
        client_ip=ip,
        user_agent=user_agent
    )
    
    mensaje = "Se requiere verificación de segundo factor (2FA)." if resultado.mfa_requerido else "Inicio de sesión exitoso."
    return EnvelopeResponse(
        success=True,
        data=resultado,
        message=mensaje
    )


@router.post(
    "/2fa",
    response_model=EnvelopeResponse[TokenResponseData],
    summary="Paso 2: Verificación de código TOTP (Google Authenticator / Authy)",
    description="Valida el código de 6 dígitos del autenticador junto al token temporal de 5 minutos emitido en el login."
)
def verificar_2fa(
    payload: TwoFactorVerifySchema,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    resultado = procesar_verificacion_2fa(
        db=db,
        temp_token=payload.temp_token,
        codigo_totp=payload.codigo_totp,
        client_ip=ip,
        user_agent=user_agent
    )

    return EnvelopeResponse(
        success=True,
        data=resultado,
        message="Verificación de doble factor exitosa. Sesión iniciada."
    )


@router.post(
    "/refresh",
    response_model=EnvelopeResponse[TokenResponseData],
    summary="Renovación de Access Token",
    description="Emite un nuevo Access Token de 30 minutos utilizando un Refresh Token válido."
)
def renovar_token(
    payload: RefreshTokenSchema,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    resultado = procesar_renovacion_token(
        db=db,
        refresh_token=payload.refresh_token,
        client_ip=ip,
        user_agent=user_agent
    )

    return EnvelopeResponse(
        success=True,
        data=resultado,
        message="Tokens de sesión renovados exitosamente."
    )


@router.get(
    "/me",
    response_model=EnvelopeResponse[UserProfileData],
    summary="Perfil del usuario autenticado",
    description="Obtiene los datos de perfil, rol y sede asignada del empleado autenticado."
)
def obtener_perfil_actual(
    current_user: Usuario = Depends(get_current_user)
):
    return EnvelopeResponse(
        success=True,
        data=UserProfileData.model_validate(current_user),
        message="Perfil recuperado con éxito."
    )


@router.post(
    "/2fa/setup",
    response_model=EnvelopeResponse[SetupTwoFactorData],
    summary="Generar clave secreta y código QR para vincular 2FA",
    description="Genera el secreto en Base32 y el código QR visual para que el usuario configure su aplicación móvil de autenticación."
)
def setup_2fa(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resultado = generar_configuracion_2fa(current_user, db)
    return EnvelopeResponse(
        success=True,
        data=resultado,
        message="Código de configuración 2FA generado. Escanee el código QR con su aplicación autenticadora."
    )


@router.post(
    "/2fa/confirm",
    response_model=EnvelopeResponse[dict],
    summary="Confirmar y activar 2FA de forma permanente",
    description="Valida el primer código de 6 dígitos producido por la app vinculada y activa la bandera 2FA en el perfil del usuario."
)
def confirmar_2fa(
    payload: ConfirmTwoFactorSchema,
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    activar_2fa(
        usuario=current_user,
        codigo_totp=payload.codigo_totp,
        db=db,
        client_ip=ip,
        user_agent=user_agent
    )

    return EnvelopeResponse(
        success=True,
        data={"totp_configurado": True},
        message="Autenticación multifactor activada con éxito en su cuenta."
    )


@router.post(
    "/logout",
    response_model=EnvelopeResponse[dict],
    summary="Cierre de sesión y revocación global",
    description="Invalida de inmediato todos los tokens JWT emitidos previamente para este usuario incrementando su versión de sesión."
)
def logout(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    current_user.sesion_version += 1
    db.commit()

    registrar_auditoria_seguridad(
        db=db,
        evento="LOGOUT_EXITOSO_SESION_REVOCADA",
        usuario_id=current_user.id,
        direccion_ip=ip,
        user_agent=user_agent,
        nivel_riesgo="INFO"
    )

    return EnvelopeResponse(
        success=True,
        data={"sesion_revocada": True},
        message="Sesión cerrada correctamente. Tokens anteriores invalidados."
    )
