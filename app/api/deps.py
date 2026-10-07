from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.usuario import Usuario

# Esquema Bearer estándar de FastAPI (OpenAPI Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True
)


def get_db() -> Generator[Session, None, None]:
    """Generador de sesión SQLAlchemy para inyección en endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente considerando proxies inversos o balanceadores."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_user_agent(request: Request) -> Optional[str]:
    """Extrae la cabecera User-Agent de la solicitud."""
    return request.headers.get("user-agent")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Inyección de dependencia para autenticar y recuperar al usuario activo.
    Valida firma criptográfica, expiración y correspondencia de versión de sesión.
    (OWASP API2:2023 / A01:2021)
    """
    credenciales_invalidas_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas o sesión expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_scope="access")
        user_id_str = payload.get("sub")
        token_sesion_version = payload.get("sesion_version")
        if user_id_str is None:
            raise credenciales_invalidas_exception
        user_id = int(user_id_str)
    except Exception:
        raise credenciales_invalidas_exception

    usuario = db.get(Usuario, user_id)
    if usuario is None or not usuario.activo or usuario.bloqueado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o bloqueado en el sistema."
        )

    # Verificación de invalidación global de sesión (cambio de password o logout)
    if token_sesion_version is not None and usuario.sesion_version != token_sesion_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha sido revocada. Inicie sesión nuevamente."
        )

    return usuario


def require_role(allowed_roles: List[str]):
    """
    Control de autorización basado en roles a nivel de función (OWASP API5:2023 / BFLA).
    Ejemplo de uso:
        @router.get("/admin/envios", dependencies=[Depends(require_role(["ADMIN", "CAJERO"]))])
    """
    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        rol_usuario = (current_user.tipo or "").upper()
        roles_permitidos_normalizados = [r.upper() for r in allowed_roles]

        if "ADMINISTRADOR" in roles_permitidos_normalizados and rol_usuario == "ADMINISTRADOR":
            return current_user
        if "ADMIN" in roles_permitidos_normalizados and rol_usuario in ("ADMINISTRADOR", "ADMIN"):
            return current_user

        if rol_usuario not in roles_permitidos_normalizados:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}."
            )
        return current_user

    return role_checker
