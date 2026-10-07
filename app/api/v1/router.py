from fastapi import APIRouter
from app.api.v1.endpoints import auth, publico

api_router = APIRouter()

# Inclusión de sub-routers v1
api_router.include_router(auth.router)
api_router.include_router(publico.router, prefix="/publico", tags=["Portal Público y Clientes"])
