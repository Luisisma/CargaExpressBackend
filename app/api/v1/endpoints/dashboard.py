import random
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, desc, case, cast, Date

from app.api.deps import get_db, require_role
from app.models.usuario import Usuario
from app.models.envio import Envio, HistorialEnvio
from app.models.agencia import Agencia
from app.models.cliente import Cliente
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import (
    DashboardResumenResponse,
    DashboardStats,
    UltimoEnvioItem,
    AdminStats,
    CajeroStats,
    AlmacenStats,
    DistribucionPagoItem,
    TopRutaItem,
    DashboardTendenciasResponse,
    TendenciaDiariaItem
)

router = APIRouter()


@router.get(
    "/resumen",
    response_model=SuccessResponse[DashboardResumenResponse],
    summary="Resumen ejecutivo y KPIs del Dashboard segregados por rol",
    description="Calcula estadísticas agregadas en tiempo real de facturación, medios de pago, embudo de estados y rutas operativas."
)
def obtener_resumen_dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO", "ALMACEN", "COURIER", "TRANSPORTISTA"]))
):
    ahora = datetime.now(timezone.utc)
    inicio_hoy = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0, tzinfo=timezone.utc)
    inicio_manana = inicio_hoy + timedelta(days=1)

    rol_usuario = (current_user.tipo or "colaborador").upper()

    # 1. KPIs Globales Base (Compatibilidad)
    envios_total = db.scalar(select(func.count(Envio.id))) or 0

    envios_hoy = db.scalar(
        select(func.count(Envio.id)).where(
            Envio.creado_en >= inicio_hoy,
            Envio.creado_en < inicio_manana
        )
    ) or 0

    ingresos_hoy_val = db.scalar(
        select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
            Envio.estado_pago == "pagado",
            Envio.creado_en >= inicio_hoy,
            Envio.creado_en < inicio_manana
        )
    ) or 0.0

    pendientes_pago = db.scalar(
        select(func.count(Envio.id)).where(Envio.estado_pago == "pendiente")
    ) or 0

    # 2. Últimos envíos recientes (para tabla de bitácora)
    stmt_ultimos = select(Envio).order_by(desc(Envio.creado_en)).limit(8)
    envios_db = list(db.execute(stmt_ultimos).scalars().all())

    ultimos_items: List[UltimoEnvioItem] = []
    for e in envios_db:
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

    # 3. Métricas Específicas de ADMINISTRADOR / SUPERVISOR
    stats_admin = None
    if rol_usuario in ["ADMINISTRADOR", "SUPERVISOR"]:
        recaudacion_total_val = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(Envio.estado_pago == "pagado")
        ) or 0.0)

        ticket_prom = round(recaudacion_total_val / envios_total, 2) if envios_total > 0 else 0.0

        # Distribución por medios de pago
        stmt_pagos = (
            select(
                Envio.forma_pago,
                func.count(Envio.id).label("cantidad"),
                func.coalesce(func.sum(Envio.precio_envio), 0.0).label("monto")
            )
            .where(Envio.forma_pago.is_not(None))
            .group_by(Envio.forma_pago)
        )
        pagos_raw = db.execute(stmt_pagos).all()

        total_monto_pagos = sum(float(p.monto) for p in pagos_raw) or 1.0
        distribucion_pagos: List[DistribucionPagoItem] = []
        for p in pagos_raw:
            monto_f = float(p.monto)
            porcentaje = round((monto_f / total_monto_pagos) * 100, 1)
            distribucion_pagos.append(
                DistribucionPagoItem(
                    medio=(p.forma_pago or "otro").upper(),
                    cantidad=int(p.cantidad),
                    monto=monto_f,
                    porcentaje=porcentaje
                )
            )

        # Embudo de Estados Logísticos
        stmt_estados = (
            select(Envio.estado, func.count(Envio.id).label("conteo"))
            .group_by(Envio.estado)
        )
        estados_raw = dict(db.execute(stmt_estados).all())
        estados_embudo = {
            "registrado": estados_raw.get("registrado", 0),
            "recepcionado": estados_raw.get("recepcionado", 0) + estados_raw.get("en_almacen_origen", 0),
            "en_ruta": estados_raw.get("en_ruta", 0) + estados_raw.get("en_transito", 0),
            "en_agencia_destino": estados_raw.get("en_agencia_destino", 0),
            "entregado": estados_raw.get("entregado", 0)
        }

        # Top 5 Rutas con mayor tráfico
        AgenciaOrig = aliased(Agencia)
        AgenciaDest = aliased(Agencia)
        stmt_top_rutas = (
            select(
                AgenciaOrig.departamento.label("origen_dep"),
                AgenciaDest.departamento.label("destino_dep"),
                func.count(Envio.id).label("total"),
                func.coalesce(func.sum(Envio.precio_envio), 0.0).label("ingresos")
            )
            .join(AgenciaOrig, Envio.agencia_origen_id == AgenciaOrig.id)
            .join(AgenciaDest, Envio.agencia_destino_id == AgenciaDest.id)
            .group_by(AgenciaOrig.departamento, AgenciaDest.departamento)
            .order_by(desc(func.count(Envio.id)))
            .limit(5)
        )
        rutas_raw = db.execute(stmt_top_rutas).all()
        top_rutas = [
            TopRutaItem(
                ruta=f"{r.origen_dep.title()} ➔ {r.destino_dep.title()}",
                total_envios=int(r.total),
                ingresos=float(r.ingresos)
            )
            for r in rutas_raw
        ]

        stats_admin = AdminStats(
            recaudacion_total=recaudacion_total_val,
            recaudacion_hoy=float(ingresos_hoy_val),
            envios_totales=int(envios_total),
            envios_hoy=int(envios_hoy),
            pendientes_pago=int(pendientes_pago),
            ticket_promedio=ticket_prom,
            distribucion_pagos=distribucion_pagos,
            estados_embudo=estados_embudo,
            top_rutas=top_rutas
        )

    # 4. Métricas Específicas de CAJERO
    stats_cajero = None
    if rol_usuario in ["CAJERO", "ADMINISTRADOR"]:
        agencia_id = current_user.agencia_id or 1
        rec_sede_hoy = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
                Envio.agencia_origen_id == agencia_id,
                Envio.estado_pago == "pagado",
                Envio.creado_en >= inicio_hoy
            )
        ) or 0.0)

        admitidos_hoy = db.scalar(
            select(func.count(Envio.id)).where(
                Envio.agencia_origen_id == agencia_id,
                Envio.creado_en >= inicio_hoy
            )
        ) or 0

        pend_cobro_sede = db.scalar(
            select(func.count(Envio.id)).where(
                Envio.agencia_origen_id == agencia_id,
                Envio.estado_pago == "pendiente"
            )
        ) or 0

        entregas_ventanilla_hoy = db.scalar(
            select(func.count(Envio.id)).where(
                Envio.agencia_destino_id == agencia_id,
                Envio.estado == "entregado"
            )
        ) or 0

        stmt_pagos_sede = (
            select(
                Envio.forma_pago,
                func.count(Envio.id).label("cantidad"),
                func.coalesce(func.sum(Envio.precio_envio), 0.0).label("monto")
            )
            .where(
                Envio.agencia_origen_id == agencia_id,
                Envio.forma_pago.is_not(None)
            )
            .group_by(Envio.forma_pago)
        )
        pagos_sede_raw = db.execute(stmt_pagos_sede).all()
        total_monto_sede = sum(float(p.monto) for p in pagos_sede_raw) or 1.0
        desglose_pagos_sede = [
            DistribucionPagoItem(
                medio=(p.forma_pago or "otro").upper(),
                cantidad=int(p.cantidad),
                monto=float(p.monto),
                porcentaje=round((float(p.monto) / total_monto_sede) * 100, 1)
            )
            for p in pagos_sede_raw
        ]

        stats_cajero = CajeroStats(
            recaudacion_sede_hoy=rec_sede_hoy,
            paquetes_admitidos_hoy=int(admitidos_hoy),
            pendientes_cobro_sede=int(pend_cobro_sede),
            entregas_ventanilla_hoy=int(entregas_ventanilla_hoy),
            desglose_pagos_sede=desglose_pagos_sede
        )

    # 5. Métricas Específicas de ALMACÉN / TRANSPORTISTA (Cero montos de dinero)
    stats_almacen = None
    if rol_usuario in ["ALMACEN", "TRANSPORTISTA", "ADMINISTRADOR"]:
        pend_despacho = db.scalar(
            select(func.count(Envio.id)).where(Envio.estado.in_(["recepcionado", "en_almacen_origen"]))
        ) or 0

        en_transito_carr = db.scalar(
            select(func.count(Envio.id)).where(Envio.estado.in_(["en_ruta", "en_transito"]))
        ) or 0

        en_bodega_dest = db.scalar(
            select(func.count(Envio.id)).where(Envio.estado == "en_agencia_destino")
        ) or 0

        kilos_hoy = float(db.scalar(
            select(func.coalesce(func.sum(Envio.peso_kg), 0.0)).where(Envio.creado_en >= inicio_hoy)
        ) or 0.0)

        stats_almacen = AlmacenStats(
            pendientes_despacho=int(pend_despacho),
            en_transito_carretera=int(en_transito_carr),
            en_bodega_destino=int(en_bodega_dest),
            kilos_movilizados_hoy=round(kilos_hoy, 1)
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
            rol=rol_usuario,
            stats=DashboardStats(
                envios_total=int(envios_total),
                envios_hoy=int(envios_hoy),
                ingresos_hoy=float(ingresos_hoy_val),
                pendientes_pago=int(pendientes_pago)
            ),
            stats_admin=stats_admin,
            stats_cajero=stats_cajero,
            stats_almacen=stats_almacen,
            ultimos_envios=ultimos_items,
            fecha_hoy=fecha_formateada
        )
    )


@router.get(
    "/tendencias",
    response_model=SuccessResponse[DashboardTendenciasResponse],
    summary="Serie temporal diaria de envíos y ventas para gráficos interactivos",
    description="Retorna el histórico día a día de órdenes e ingresos en Soles (PEN) para gráficos combinados, lineales y de barras."
)
def obtener_tendencias_dashboard(
    dias: int = 30,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO", "ALMACEN", "COURIER", "TRANSPORTISTA"]))
):
    if dias < 7:
        dias = 7
    elif dias > 90:
        dias = 90

    ahora = datetime.now(timezone.utc)
    inicio_hoy = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0, tzinfo=timezone.utc)
    inicio_rango = inicio_hoy - timedelta(days=dias - 1)
    inicio_manana = inicio_hoy + timedelta(days=1)

    # 1. Armar mapa continuo de días para no tener huecos en el gráfico
    dias_map: Dict[str, Dict] = {}
    for i in range(dias):
        f = inicio_rango + timedelta(days=i)
        f_str = f.strftime("%Y-%m-%d")
        label = f.strftime("%d/%m")
        dias_map[f_str] = {
            "fecha": f_str,
            "dia_label": label,
            "total_envios": 0,
            "ingresos": 0.0
        }

    # 2. Agrupación compatible universal (SQLite / PostgreSQL / MySQL)
    stmt = select(Envio.creado_en, Envio.precio_envio, Envio.estado_pago)
    filas = db.execute(stmt).all()

    for fila in filas:
        dt = fila.creado_en
        if not dt:
            continue

        if isinstance(dt, str):
            dia_key = dt[:10]
        elif hasattr(dt, "strftime"):
            dia_key = dt.strftime("%Y-%m-%d")
        else:
            dia_key = str(dt)[:10]

        if dia_key in dias_map:
            dias_map[dia_key]["total_envios"] += 1
            if (fila.estado_pago or "").lower() == "pagado":
                dias_map[dia_key]["ingresos"] = round(
                    dias_map[dia_key]["ingresos"] + float(fila.precio_envio or 0.0), 2
                )


    lista_resultado = [
        TendenciaDiariaItem(**item) for item in dias_map.values()
    ]

    return SuccessResponse(
        success=True,
        data=DashboardTendenciasResponse(
            dias=dias,
            fecha_inicio=inicio_rango.strftime("%d/%m/%Y"),
            fecha_fin=inicio_hoy.strftime("%d/%m/%Y"),
            datos=lista_resultado
        )
    )


@router.post(
    "/sembrar-demo",
    summary="Ingesta de datos coherentes para visualización del Dashboard",
    description="Inserta envíos representativos con historial de 14 días, métodos de pago balanceados y estados logísticos."
)
def sembrar_datos_demo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["ADMINISTRADOR", "SUPERVISOR"]))
):
    agencias = list(db.execute(select(Agencia)).scalars().all())
    if not agencias:
        return SuccessResponse(success=False, data={"mensaje": "No hay agencias disponibles para sembrar datos."})

    agencia_ids = [a.id for a in agencias]
    agencia_map = {a.id: f"{a.nombre} ({a.departamento})" for a in agencias}

    clientes_data = [
        ("dni", "10458923", "Juan Carlos Pérez Quispe", "jc.perez@gmail.com", "987654321", "persona_natural"),
        ("dni", "72345678", "Rosa María Benavides Alva", "rosa.benavides@outlook.com", "976543210", "persona_natural"),
        ("dni", "45678912", "Carlos Alberto Mendoza Ramos", "carlos.mendoza@yahoo.es", "965432109", "persona_natural"),
        ("ruc", "20601234567", "Distribuidora Textil Andina S.A.C.", "logistica@textilandina.pe", "954321098", "empresa"),
        ("dni", "78123456", "Lucía Valeria Paredes Cano", "lucia.paredes@hotmail.com", "943210987", "persona_natural"),
        ("ruc", "20554433221", "Comercializadora del Sur E.I.R.L.", "ventas@delsur.com.pe", "932109876", "empresa"),
        ("dni", "41239876", "Jorge Luis Huamán Ticona", "jorge.huaman@gmail.com", "921098765", "persona_natural"),
        ("dni", "70987654", "Patricia Sofía Morales Vega", "patricia.morales@gmail.com", "910987654", "persona_natural")
    ]

    clientes_db = []
    for c in clientes_data:
        cl = db.execute(select(Cliente).where(Cliente.numero_documento == c[1])).scalar_one_or_none()
        if not cl:
            cl = Cliente(
                tipo_documento=c[0],
                numero_documento=c[1],
                nombre_completo=c[2],
                email=c[3],
                telefono=c[4],
                tipo_cliente=c[5],
                activo=True
            )
            db.add(cl)
            db.flush()
        clientes_db.append(cl)

    ahora_utc = datetime.now(timezone.utc)
    envios_plan = [
        {"dias": 13, "tipo_p": "caja", "peso": 2.5, "precio": 25.00, "medio": "efectivo", "estado": "entregado", "pago": "pagado", "desc": "Repuestos electrónicos y cables"},
        {"dias": 12, "tipo_p": "sobre", "peso": 0.5, "precio": 7.50, "medio": "yape", "estado": "entregado", "pago": "pagado", "desc": "Contrato legal y testimonio notarial"},
        {"dias": 11, "tipo_p": "saco", "peso": 15.0, "precio": 52.50, "medio": "tarjeta", "estado": "entregado", "pago": "pagado", "desc": "Lote de ropa y casacas térmicas"},
        {"dias": 10, "tipo_p": "paquete", "peso": 4.0, "precio": 28.00, "medio": "yape", "estado": "entregado", "pago": "pagado", "desc": "Calzado deportivo y zapatillas"},
        {"dias": 9, "tipo_p": "caja", "peso": 3.0, "precio": 22.50, "medio": "plin", "estado": "entregado", "pago": "pagado", "desc": "Documentación técnica y catálogos"},
        {"dias": 8, "tipo_p": "sobre", "peso": 0.4, "precio": 7.50, "medio": "yape", "estado": "entregado", "pago": "pagado", "desc": "Certificados universitarios originales"},
        {"dias": 8, "tipo_p": "saco", "peso": 20.0, "precio": 68.00, "medio": "efectivo", "estado": "entregado", "pago": "pagado", "desc": "Prendas de lana y artesanía cusqueña"},
        {"dias": 7, "tipo_p": "caja", "peso": 6.5, "precio": 35.00, "medio": "yape", "estado": "entregado", "pago": "pagado", "desc": "Medicamentos y muestras de laboratorio"},
        {"dias": 6, "tipo_p": "paquete", "peso": 5.0, "precio": 30.50, "medio": "tarjeta", "estado": "entregado", "pago": "pagado", "desc": "Herramientas de ferretería y taladro"},
        {"dias": 6, "tipo_p": "sobre", "peso": 0.3, "precio": 7.50, "medio": "plin", "estado": "entregado", "pago": "pagado", "desc": "Póliza de seguro vehicular"},
        {"dias": 5, "tipo_p": "caja", "peso": 4.2, "precio": 26.50, "medio": "efectivo", "estado": "entregado", "pago": "pagado", "desc": "Insumos dentales y prótesis"},
        {"dias": 4, "tipo_p": "saco", "peso": 18.0, "precio": 62.00, "medio": "yape", "estado": "entregado", "pago": "pagado", "desc": "Mercadería textil Gamarra mayorista"},
        {"dias": 3, "tipo_p": "caja", "peso": 5.5, "precio": 32.00, "medio": "yape", "estado": "en_agencia_destino", "pago": "pagado", "desc": "Cámara fotográfica y accesorios"},
        {"dias": 3, "tipo_p": "sobre", "peso": 0.5, "precio": 7.50, "medio": "efectivo", "estado": "en_agencia_destino", "pago": "pagado", "desc": "Partidas de nacimiento apostilladas"},
        {"dias": 2, "tipo_p": "paquete", "peso": 3.8, "precio": 24.50, "medio": "plin", "estado": "en_agencia_destino", "pago": "pagado", "desc": "Libros de texto y manuales"},
        {"dias": 2, "tipo_p": "saco", "peso": 22.0, "precio": 74.00, "medio": "tarjeta", "estado": "en_ruta", "pago": "pagado", "desc": "Fardo de telas e hilos de alpaca"},
        {"dias": 1, "tipo_p": "caja", "peso": 8.0, "precio": 42.00, "medio": "yape", "estado": "en_ruta", "pago": "pagado", "desc": "Filtros de aceite y repuestos mecánicos"},
        {"dias": 1, "tipo_p": "paquete", "peso": 2.2, "precio": 18.50, "medio": "efectivo", "estado": "en_ruta", "pago": "pagado", "desc": "Prendas de vestir personalizadas"},
        {"dias": 1, "tipo_p": "sobre", "peso": 0.2, "precio": 7.50, "medio": "yape", "estado": "recepcionado", "pago": "pagado", "desc": "Pasaportes visados y tickets"},
        {"dias": 0, "tipo_p": "caja", "peso": 3.5, "precio": 23.50, "medio": "yape", "estado": "recepcionado", "pago": "pagado", "desc": "Equipos de sonido y micrófonos"},
        {"dias": 0, "tipo_p": "saco", "peso": 12.0, "precio": 45.00, "medio": "efectivo", "estado": "en_ruta", "pago": "pagado", "desc": "Zapatos de cuero arequipeño"},
        {"dias": 0, "tipo_p": "caja", "peso": 1.5, "precio": 15.50, "medio": "plin", "estado": "registrado", "pago": "pendiente", "desc": "Pre-registro web: Cosméticos y cremas"},
        {"dias": 0, "tipo_p": "sobre", "peso": 0.4, "precio": 7.50, "medio": "yape", "estado": "registrado", "pago": "pendiente", "desc": "Pre-registro web: Escrituras de inmueble"},
        {"dias": 0, "tipo_p": "paquete", "peso": 4.5, "precio": 27.00, "medio": "efectivo", "estado": "registrado", "pago": "pagado", "desc": "Artesanías y cerámicas decorativas"}
    ]

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    insertados = 0

    for idx, item in enumerate(envios_plan, start=301):
        sufijo = "".join(random.choices(alphabet, k=6))
        codigo_trk = f"CE-2026-D{sufijo}"
        fecha_reg = ahora_utc - timedelta(days=item["dias"], hours=random.randint(1, 6), minutes=random.randint(5, 50))

        rem_c = random.choice(clientes_db)
        dest_c = random.choice([c for c in clientes_db if c.id != rem_c.id])

        orig_id = agencia_ids[0] if (idx % 2 == 0) else (agencia_ids[1] if len(agencia_ids) > 1 else agencia_ids[0])
        dest_id = agencia_ids[2] if len(agencia_ids) > 2 else (agencia_ids[1] if len(agencia_ids) > 1 else agencia_ids[0])
        if orig_id == dest_id and len(agencia_ids) > 1:
            dest_id = [a for a in agencia_ids if a != orig_id][0]

        precio_dec = Decimal(str(item["precio"]))
        subtotal_dec = round(precio_dec / Decimal("1.18"), 2)
        igv_dec = round(precio_dec - subtotal_dec, 2)

        envio = Envio(
            codigo_tracking=codigo_trk,
            remitente_id=rem_c.id,
            destinatario_id=dest_c.id,
            agencia_origen_id=orig_id,
            agencia_destino_id=dest_id,
            tipo_envio="agencia_agencia" if item["tipo_p"] != "sobre" else "agencia_domicilio",
            tipo_paquete=item["tipo_p"],
            peso_kg=Decimal(str(item["peso"])),
            peso_volumetrico=Decimal(str(round(item["peso"] * 0.8, 2))),
            descripcion=item["desc"],
            monto_subtotal=subtotal_dec,
            monto_descuento=Decimal("0.00"),
            monto_igv=igv_dec,
            precio_envio=precio_dec,
            forma_pago=item["medio"],
            estado_pago=item["pago"],
            lugar_pago="origen",
            estado=item["estado"],
            tipo_documento="boleta" if rem_c.tipo_cliente == "persona_natural" else "factura",
            registrado_web=item["estado"] == "registrado",
            creado_en=fecha_reg,
            actualizado_en=fecha_reg + timedelta(minutes=random.randint(10, 120))
        )
        db.add(envio)
        db.flush()

        hitos = [
            HistorialEnvio(
                envio_id=envio.id,
                estado="REGISTRADO",
                descripcion="Pre-registro completado vía portal de autoservicio.",
                ubicacion=agencia_map.get(orig_id, "Sede Origen"),
                creado_en=fecha_reg
            )
        ]
        if item["estado"] in ["recepcionado", "en_ruta", "en_agencia_destino", "entregado"]:
            hitos.append(
                HistorialEnvio(
                    envio_id=envio.id,
                    estado="RECEPCIONADO",
                    descripcion="Paquete formalizado y pesado en balanza de mostrador.",
                    ubicacion=agencia_map.get(orig_id, "Sede Origen"),
                    creado_en=fecha_reg + timedelta(hours=random.randint(1, 2))
                )
            )
        if item["estado"] in ["en_ruta", "en_agencia_destino", "entregado"]:
            hitos.append(
                HistorialEnvio(
                    envio_id=envio.id,
                    estado="EN_RUTA",
                    descripcion="Carga despachada en camión de ruta interprovincial.",
                    ubicacion="En Carretera / Panamericana",
                    creado_en=fecha_reg + timedelta(hours=random.randint(3, 6))
                )
            )
        if item["estado"] in ["en_agencia_destino", "entregado"]:
            hitos.append(
                HistorialEnvio(
                    envio_id=envio.id,
                    estado="EN_AGENCIA_DESTINO",
                    descripcion="Carga arribada y lista en estantería para retiro.",
                    ubicacion=agencia_map.get(dest_id, "Sede Destino"),
                    creado_en=fecha_reg + timedelta(hours=random.randint(8, 16))
                )
            )
        if item["estado"] == "entregado":
            hitos.append(
                HistorialEnvio(
                    envio_id=envio.id,
                    estado="ENTREGADO",
                    descripcion="Entregado conforme en ventanilla tras verificar DNI físico.",
                    ubicacion=agencia_map.get(dest_id, "Sede Destino"),
                    creado_en=fecha_reg + timedelta(hours=random.randint(18, 30))
                )
            )
        db.add_all(hitos)
        insertados += 1

    db.commit()
    return SuccessResponse(
        success=True,
        data={
            "mensaje": f"Se sembraron {insertados} encomiendas y sus hitos de auditoría con éxito.",
            "total_envios_sembrados": insertados
        }
    )


