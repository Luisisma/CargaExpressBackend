from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.api.deps import get_db, require_role
from app.models.usuario import Usuario
from app.models.envio import Envio
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import DashboardResumenResponse, DashboardStats, UltimoEnvioItem

router = APIRouter()


@router.get(
    "/resumen",
    response_model=SuccessResponse[DashboardResumenResponse],
    summary="Resumen ejecutivo y KPIs del Dashboard",
    description="Calcula estadísticas reales de envíos, recaudación e historial reciente desde la base de datos."
)
def obtener_resumen_dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO", "ALMACEN", "COURIER", "TRANSPORTISTA"]))
):
    ahora = datetime.now(timezone.utc)
    inicio_hoy = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0, tzinfo=timezone.utc)
    inicio_manana = inicio_hoy + timedelta(days=1)

    # 1. Total Envíos
    envios_total = db.scalar(select(func.count(Envio.id))) or 0

    # 2. Envíos creados hoy
    envios_hoy = db.scalar(
        select(func.count(Envio.id)).where(
            Envio.creado_en >= inicio_hoy,
            Envio.creado_en < inicio_manana
        )
    ) or 0

    # 3. Ingresos recaudados hoy (en soles)
    ingresos_hoy_val = db.scalar(
        select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
            Envio.estado_pago == "pagado",
            Envio.creado_en >= inicio_hoy,
            Envio.creado_en < inicio_manana
        )
    ) or 0.0

    # 4. Pendientes de pago
    pendientes_pago = db.scalar(
        select(func.count(Envio.id)).where(Envio.estado_pago == "pendiente")
    ) or 0

    # 5. Últimos envíos
    stmt_ultimos = (
        select(Envio)
        .order_by(desc(Envio.creado_en))
        .limit(8)
    )
    envios_db = list(db.execute(stmt_ultimos).scalars().all())

    ultimos_items: List[UltimoEnvioItem] = []
    for e in envios_db:
        # Formato fecha: "08/10 17:30"
        fecha_str = e.creado_en.strftime("%d/%m %H:%M") if e.creado_en else "N/A"
        remitente_nombre = e.remitente.nombre_completo if e.remitente else "Sin remitente"
        destino_nombre = (
            f"AGENCIA {e.agencia_destino.departamento.upper()} - {e.agencia_destino.nombre.upper()}"
            if e.agencia_destino else "Agencia Destino"
        )
        
        ultimos_items.append(
            UltimoEnvioItem(
                id=e.id,
                codigo_tracking=e.codigo_tracking,
                remitente=remitente_nombre,
                destino=destino_nombre,
                estado=e.estado.replace("_", " ").title(),
                estado_pago=e.estado_pago,
                precio_envio=float(e.precio_envio or 0.0),
                fecha=fecha_str
            )
        )

    # Nombres de meses en español
    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]
    dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    dia_semana = dias_es[ahora.weekday()]
    mes_str = meses_es[ahora.month - 1]
    fecha_formateada = f"{dia_semana} {ahora.day:02d} de {mes_str}, {ahora.year}"

    return SuccessResponse(
        success=True,
        data=DashboardResumenResponse(
            stats=DashboardStats(
                envios_total=int(envios_total),
                envios_hoy=int(envios_hoy),
                ingresos_hoy=float(ingresos_hoy_val),
                pendientes_pago=int(pendientes_pago)
            ),
            ultimos_envios=ultimos_items,
            fecha_hoy=fecha_formateada
        )
    )
