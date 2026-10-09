from fastapi import APIRouter
from app.api.v1.endpoints import auth, publico, usuarios, dashboard, envios, clientes, pagos

api_router = APIRouter()

# Inclusión de sub-routers v1
api_router.include_router(auth.router)
api_router.include_router(publico.router, prefix="/publico", tags=["Portal Público y Clientes"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Gestión de Usuarios y Personal"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard Operativo y KPIs"])
api_router.include_router(envios.router, prefix="/envios", tags=["Gestión de Envíos y Encomiendas"])
api_router.include_router(clientes.router, prefix="/clientes", tags=["Directorio de Clientes"])
api_router.include_router(pagos.router, prefix="/pagos", tags=["Motor de Pagos y Webhooks"])

