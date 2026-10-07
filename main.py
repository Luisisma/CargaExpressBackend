from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.middlewares import SecurityHeadersMiddleware
from app.api.v1.router import api_router
from app.schemas.common import ErrorResponse, ErrorPayload, ErrorDetail

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend REST API seguro con arquitectura modular por capas para CargaExpress Perú.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 1. Middleware de CORS restrictivo (OWASP API8:2023)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# 2. Middleware de Encabezados de Seguridad y Correlation ID
app.add_middleware(SecurityHeadersMiddleware)


# 3. Manejadores de Excepciones Globales con Esquema Envelope
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Normaliza errores HTTP bajo el estándar ErrorResponse."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=ErrorPayload(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail)
            )
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Captura errores de validación de esquemas Pydantic v2."""
    detalles = []
    for err in exc.errors():
        campo = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        detalles.append(ErrorDetail(field=campo or "body", issue=err["msg"]))

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error=ErrorPayload(
                code="VALIDATION_ERROR",
                message="Los datos suministrados no superaron la validación de formato requerida.",
                details=detalles
            )
        ).model_dump()
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Evita fugas de información interna o trazas de código en errores 500 (OWASP A05:2021)."""
    request_id = getattr(request.state, "request_id", "sin-id")
    # En desarrollo local mostramos la causa si DEBUG=True
    mensaje = str(exc) if settings.DEBUG else "Ocurrió un error inesperado al procesar la solicitud. Contacte a soporte."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error=ErrorPayload(
                code="INTERNAL_SERVER_ERROR",
                message=f"{mensaje} (Ref: {request_id})"
            )
        ).model_dump()
    )


# 4. Enrutamiento Principal
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Salud del Sistema"])
def health_check():
    """Endpoint de monitoreo y health check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
