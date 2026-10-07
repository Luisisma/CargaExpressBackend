from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    generate_qr_base64,
    verify_totp_code
)
from app.models.usuario import Usuario
from app.schemas.auth import (
    LoginResponseData,
    TokenResponseData,
    UserProfileData,
    SetupTwoFactorData
)
from app.services.audit_service import registrar_auditoria_seguridad


def buscar_usuario_por_identificador(db: Session, identificador: str) -> Optional[Usuario]:
    """Busca un usuario activo en el sistema por su DNI o por su Correo Electrónico."""
    identificador_limpio = identificador.strip().lower()
    stmt = select(Usuario).where(
        or_(
            Usuario.dni == identificador.strip(),
            Usuario.email.ilike(identificador_limpio)
        )
    )
    return db.scalar(stmt)


def procesar_login(
    db: Session,
    identificador: str,
    password: str,
    client_ip: str,
    user_agent: Optional[str]
) -> LoginResponseData:
    """
    Ejecuta el paso 1 de autenticación:
    - Valida existencia de usuario y estado de bloqueo.
    - Comprueba contraseña con soporte de hashing seguro y legacy.
    - Registra evento de auditoría de seguridad.
    - Emite temp_token (si requiere 2FA) o tokens definitivos.
    """
    usuario = buscar_usuario_por_identificador(db, identificador)

    # Mitigación de enumeración de usuarios: error genérico ante credencial errónea
    credenciales_invalidas_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de acceso incorrectas o usuario no registrado."
    )

    if not usuario or not usuario.activo:
        registrar_auditoria_seguridad(
            db=db,
            evento="LOGIN_FALLIDO_USUARIO_INEXISTENTE",
            direccion_ip=client_ip,
            user_agent=user_agent,
            detalles={"identificador": identificador[:4] + "***"},
            nivel_riesgo="WARN"
        )
        raise credenciales_invalidas_exception

    # Verificar si la cuenta está bloqueada temporalmente por fuerza bruta
    ahora = datetime.utcnow()
    if usuario.bloqueado:
        registrar_auditoria_seguridad(
            db=db,
            evento="LOGIN_RECHAZADO_CUENTA_BLOQUEADA",
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            detalles={"motivo": "Cuenta bloqueada permanentemente por administración"},
            nivel_riesgo="WARN"
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Su cuenta ha sido bloqueada. Por favor, contacte con el Administrador del Sistema."
        )

    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        minutos_restantes = int((usuario.bloqueado_hasta - ahora).total_seconds() // 60) + 1
        registrar_auditoria_seguridad(
            db=db,
            evento="LOGIN_RECHAZADO_BLOQUEO_TEMPORAL",
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            detalles={"minutos_restantes": minutos_restantes},
            nivel_riesgo="WARN"
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Cuenta bloqueada temporalmente por reiterados intentos fallidos. Intente nuevamente en {minutos_restantes} minuto(s)."
        )

    # Comprobación de contraseña
    if not usuario.check_password(password):
        usuario.intentos_fallidos += 1
        
        # Bloquear temporalmente si supera el umbral configurado
        if usuario.intentos_fallidos >= settings.MAX_LOGIN_ATTEMPTS:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=settings.LOCKOUT_MINUTES)
            evento = "BLOQUEO_TEMPORAL_FUERZA_BRUTA"
            nivel = "CRITICAL"
        else:
            evento = "LOGIN_FALLIDO_PASSWORD_INCORRECTO"
            nivel = "WARN"

        db.commit()
        registrar_auditoria_seguridad(
            db=db,
            evento=evento,
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            detalles={"intentos": usuario.intentos_fallidos},
            nivel_riesgo=nivel
        )
        raise credenciales_invalidas_exception

    # Contraseña correcta: resetear contadores y registrar acceso exitoso
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_login = ahora
    db.commit()

    user_profile = UserProfileData.model_validate(usuario)

    # Si tiene 2FA configurado, se emite un temp_token de 5 minutos
    if usuario.totp_configurado and usuario.totp_secret:
        registrar_auditoria_seguridad(
            db=db,
            evento="LOGIN_PASO_1_EXITOSO_REQUIERE_2FA",
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            detalles={"totp_configurado": True},
            nivel_riesgo="INFO"
        )
        temp_token = create_temp_token(usuario.id)
        totp_uri = get_totp_uri(usuario.totp_secret, usuario.email)
        qr_code = generate_qr_base64(totp_uri)
        return LoginResponseData(
            mfa_requerido=True,
            temp_token=temp_token,
            usuario=user_profile,
            qr_code=qr_code,
            secret_manual=usuario.totp_secret
        )

    # Si no tiene 2FA configurado (por ejemplo primer acceso o rol no forzado)
    registrar_auditoria_seguridad(
        db=db,
        evento="LOGIN_COMPLETO_SIN_2FA",
        usuario_id=usuario.id,
        direccion_ip=client_ip,
        user_agent=user_agent,
        detalles={"totp_configurado": False},
        nivel_riesgo="WARN"
    )
    access_token = create_access_token(
        user_id=usuario.id,
        rol=usuario.tipo,
        agencia_id=usuario.agencia_id,
        sesion_version=usuario.sesion_version
    )
    refresh_token = create_refresh_token(
        user_id=usuario.id,
        sesion_version=usuario.sesion_version
    )
    return LoginResponseData(
        mfa_requerido=False,
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=user_profile
    )


def procesar_verificacion_2fa(
    db: Session,
    temp_token: str,
    codigo_totp: str,
    client_ip: str,
    user_agent: Optional[str]
) -> TokenResponseData:
    """
    Ejecuta el paso 2 de autenticación:
    - Valida temp_token con scope 'mfa_pending'.
    - Verifica el código numérico TOTP contra el secreto del usuario.
    - Emite access_token y refresh_token definitivos.
    """
    try:
        payload = decode_token(temp_token, expected_scope="mfa_pending")
        user_id = int(payload.get("sub"))
    except Exception:
        registrar_auditoria_seguridad(
            db=db,
            evento="2FA_RECHAZADO_TOKEN_TEMPORAL_INVALIDO",
            direccion_ip=client_ip,
            user_agent=user_agent,
            nivel_riesgo="WARN"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión temporal ha expirado o es inválida. Inicie sesión nuevamente."
        )

    usuario = db.get(Usuario, user_id)
    if not usuario or not usuario.activo or not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido para autenticación multifactor."
        )

    # Validar código TOTP
    if not verify_totp_code(usuario.totp_secret, codigo_totp):
        registrar_auditoria_seguridad(
            db=db,
            evento="2FA_FALLIDO_CODIGO_INCORRECTO",
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            nivel_riesgo="WARN"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de autenticación 2FA incorrecto o expirado."
        )

    # 2FA Exitoso
    registrar_auditoria_seguridad(
        db=db,
        evento="2FA_EXITOSO_SESION_INICIADA",
        usuario_id=usuario.id,
        direccion_ip=client_ip,
        user_agent=user_agent,
        detalles={"metodo": "TOTP"},
        nivel_riesgo="INFO"
    )

    access_token = create_access_token(
        user_id=usuario.id,
        rol=usuario.tipo,
        agencia_id=usuario.agencia_id,
        sesion_version=usuario.sesion_version
    )
    refresh_token = create_refresh_token(
        user_id=usuario.id,
        sesion_version=usuario.sesion_version
    )

    return TokenResponseData(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=UserProfileData.model_validate(usuario)
    )


def procesar_renovacion_token(
    db: Session,
    refresh_token: str,
    client_ip: str,
    user_agent: Optional[str]
) -> TokenResponseData:
    """Renueva el Access Token utilizando un Refresh Token válido y no revocado."""
    try:
        payload = decode_token(refresh_token, expected_scope="refresh")
        user_id = int(payload.get("sub"))
        token_sesion_version = payload.get("sesion_version")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado."
        )

    usuario = db.get(Usuario, user_id)
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario no se encuentra activo."
        )

    # Control de revocación global de sesiones (cambio de password o logout)
    if usuario.sesion_version != token_sesion_version:
        registrar_auditoria_seguridad(
            db=db,
            evento="REFRESH_RECHAZADO_SESION_REVOCADA",
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            detalles={"version_token": token_sesion_version, "version_actual": usuario.sesion_version},
            nivel_riesgo="WARN"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha sido revocada debido a un cambio de contraseña o cierre de sesión global."
        )

    nuevo_access_token = create_access_token(
        user_id=usuario.id,
        rol=usuario.tipo,
        agencia_id=usuario.agencia_id,
        sesion_version=usuario.sesion_version
    )
    nuevo_refresh_token = create_refresh_token(
        user_id=usuario.id,
        sesion_version=usuario.sesion_version
    )

    registrar_auditoria_seguridad(
        db=db,
        evento="TOKEN_RENOVADO_EXITOSO",
        usuario_id=usuario.id,
        direccion_ip=client_ip,
        user_agent=user_agent,
        nivel_riesgo="INFO"
    )

    return TokenResponseData(
        access_token=nuevo_access_token,
        refresh_token=nuevo_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=UserProfileData.model_validate(usuario)
    )


def generar_configuracion_2fa(usuario: Usuario, db: Session) -> SetupTwoFactorData:
    """Genera nuevo secreto TOTP y código QR para vincular el autenticador del usuario."""
    secret = generate_totp_secret()
    usuario.totp_secret = secret
    db.commit()

    otpauth_url = get_totp_uri(secret, usuario.email)
    qr_code_base64 = generate_qr_base64(otpauth_url)

    return SetupTwoFactorData(
        secret=secret,
        qr_code=qr_code_base64,
        otpauth_url=otpauth_url
    )


def activar_2fa(
    usuario: Usuario,
    codigo_totp: str,
    db: Session,
    client_ip: str,
    user_agent: Optional[str]
) -> bool:
    """Valida el primer código TOTP generado por el usuario y activa su 2FA permanentemente."""
    if not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha iniciado una solicitud de vinculación 2FA previa."
        )

    if not verify_totp_code(usuario.totp_secret, codigo_totp):
        registrar_auditoria_seguridad(
            db=db,
            evento="ACTIVACION_2FA_FALLIDA",
            usuario_id=usuario.id,
            direccion_ip=client_ip,
            user_agent=user_agent,
            nivel_riesgo="WARN"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificación incorrecto. No se pudo confirmar la activación de 2FA."
        )

    usuario.totp_configurado = True
    db.commit()

    registrar_auditoria_seguridad(
        db=db,
        evento="ACTIVACION_2FA_EXITOSA",
        usuario_id=usuario.id,
        direccion_ip=client_ip,
        user_agent=user_agent,
        nivel_riesgo="INFO"
    )
    return True
