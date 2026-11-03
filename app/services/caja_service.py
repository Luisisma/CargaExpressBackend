from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.usuario import Usuario
from app.models.envio import Envio
from app.models.agencia import Agencia
from app.schemas.caja import (
    ResumenCajaResponse,
    MovimientoCajaItem,
    ArqueoCajaRequest,
    ArqueoCajaResponse,
    GestionSobrepagoRequest,
    GestionSobrepagoResponse
)
from app.services.audit_service import registrar_auditoria_seguridad


class CajaService:
    """
    Servicio de Dominio Financiero para Control y Arqueo de Caja.
    Encapsula el cálculo de ingresos por método de pago, arqueo ciego,
    conciliación de descuadres y prevención de lavado de activos (PLAFT).
    """

    @classmethod
    def obtener_resumen(
        cls,
        db: Session,
        current_user: Usuario,
        agencia_id: Optional[int] = None
    ) -> ResumenCajaResponse:
        rol_usuario = (current_user.tipo or "cajero").upper()
        
        # Restricción RBAC: Cajeros solo acceden a su propia agencia asignada
        if rol_usuario == "CAJERO":
            sede_id = current_user.agencia_id or 1
        else:
            # Administrador o Supervisor pueden consultar una sede específica o su defecto
            sede_id = agencia_id or current_user.agencia_id or 1

        agencia = db.get(Agencia, sede_id)
        agencia_nombre = f"Agencia {agencia.departamento.title()} - {agencia.nombre.title()}" if agencia else "Agencia Principal"

        # Rango de tiempo: Jornada de hoy (UTC)
        ahora = datetime.now(timezone.utc)
        inicio_hoy = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0, tzinfo=timezone.utc)
        inicio_manana = inicio_hoy + timedelta(days=1)

        # Base de consulta para envíos cobrados en la agencia de origen hoy
        condiciones = [
            Envio.agencia_origen_id == sede_id,
            Envio.estado_pago == "pagado",
            Envio.creado_en >= inicio_hoy,
            Envio.creado_en < inicio_manana
        ]

        # Cobros en Efectivo (Dinero físico en ventanilla)
        efectivo_val = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
                *condiciones,
                Envio.forma_pago == "efectivo"
            )
        ) or 0.0)

        # Cobros Digitales (Yape, Plin, Transferencias -> Van directo a la cuenta bancaria)
        digital_val = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
                *condiciones,
                Envio.forma_pago.in_(["yape", "plin", "transferencia"])
            )
        ) or 0.0)

        # Cobros por Tarjeta / POS
        tarjeta_val = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
                *condiciones,
                Envio.forma_pago == "tarjeta"
            )
        ) or 0.0)

        total_recaudado = round(efectivo_val + digital_val + tarjeta_val, 2)
        total_transacciones = int(db.scalar(
            select(func.count(Envio.id)).where(*condiciones)
        ) or 0)

        # Fondo inicial de caja chica para sencillo / cambio
        saldo_inicial = 150.00
        efectivo_esperado_cajon = round(saldo_inicial + efectivo_val, 2)

        # Movimientos recientes cobrados hoy en esta sede
        stmt_movs = (
            select(Envio)
            .where(*condiciones)
            .order_by(desc(Envio.creado_en))
            .limit(20)
        )
        envios_db = list(db.execute(stmt_movs).scalars().all())

        movimientos: List[MovimientoCajaItem] = []
        for e in envios_db:
            hora_str = e.creado_en.strftime("%I:%M %p") if e.creado_en else "N/A"
            reg_usr = getattr(e, 'registrado_por', None)
            cajero_nombre = reg_usr.nombre_completo if reg_usr else current_user.nombre_completo
            remitente_nombre = e.remitente.nombre_completo if e.remitente else "Cliente Varios"

            movimientos.append(
                MovimientoCajaItem(
                    id=e.id,
                    hora=hora_str,
                    codigo_tracking=e.codigo_tracking,
                    remitente=remitente_nombre,
                    tipo_documento=e.tipo_documento.upper(),
                    forma_pago=e.forma_pago.upper(),
                    monto=float(e.precio_envio or 0.0),
                    cajero=cajero_nombre,
                    estado=e.estado.replace("_", " ").title()
                )
            )

        cajero_display = current_user.nombre_completo or f"{current_user.nombres} {current_user.apellidos}".strip()

        return ResumenCajaResponse(
            agencia_id=sede_id,
            agencia_nombre=agencia_nombre,
            cajero_nombre=cajero_display,
            cajero_rol=rol_usuario,
            saldo_inicial=saldo_inicial,
            efectivo_cobrado=round(efectivo_val, 2),
            digital_cobrado=round(digital_val, 2),
            tarjeta_cobrado=round(tarjeta_val, 2),
            total_recaudado=total_recaudado,
            efectivo_esperado_cajon=efectivo_esperado_cajon,
            total_transacciones=total_transacciones,
            estado_turno="abierto",
            apertura_hora="08:00 AM",
            movimientos=movimientos
        )

    @classmethod
    def registrar_arqueo(
        cls,
        db: Session,
        current_user: Usuario,
        payload: ArqueoCajaRequest,
        agencia_id: Optional[int] = None,
        client_ip: str = "127.0.0.1"
    ) -> ArqueoCajaResponse:
        rol_usuario = (current_user.tipo or "cajero").upper()
        sede_id = current_user.agencia_id or 1 if rol_usuario == "CAJERO" else (agencia_id or current_user.agencia_id or 1)

        ahora = datetime.now(timezone.utc)
        inicio_hoy = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0, tzinfo=timezone.utc)
        inicio_manana = inicio_hoy + timedelta(days=1)

        condiciones = [
            Envio.agencia_origen_id == sede_id,
            Envio.estado_pago == "pagado",
            Envio.creado_en >= inicio_hoy,
            Envio.creado_en < inicio_manana
        ]

        efectivo_val = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
                *condiciones,
                Envio.forma_pago == "efectivo"
            )
        ) or 0.0)

        digital_val = float(db.scalar(
            select(func.coalesce(func.sum(Envio.precio_envio), 0.0)).where(
                *condiciones,
                Envio.forma_pago.in_(["yape", "plin", "transferencia"])
            )
        ) or 0.0)

        saldo_inicial = 150.00
        efectivo_esperado = round(saldo_inicial + efectivo_val, 2)
        diferencia = round(payload.efectivo_contado - efectivo_esperado, 2)

        if abs(diferencia) < 0.01:
            cuadre = "cuadrado"
            mensaje = "Arqueo de caja perfecto. El efectivo en cajón coincide exactamente con las ventas."
        elif diferencia > 0:
            cuadre = "sobrante"
            mensaje = f"Arqueo finalizado con sobrante de S/ {abs(diferencia):.2f} en cajón."
        else:
            cuadre = "faltante"
            mensaje = f"Arqueo finalizado con faltante de S/ {abs(diferencia):.2f} en cajón."

        # Registrar evento de auditoría de seguridad
        registrar_auditoria_seguridad(
            db=db,
            evento="ARQUEO_CIERRE_CAJA_REGISTRADO",
            usuario_id=current_user.id,
            direccion_ip=client_ip,
            detalles={
                "sede_id": sede_id,
                "efectivo_esperado": efectivo_esperado,
                "efectivo_contado": payload.efectivo_contado,
                "diferencia": diferencia,
                "cuadre": cuadre,
                "observaciones": payload.observaciones
            },
            nivel_riesgo="INFO" if cuadre == "cuadrado" else "WARN"
        )

        return ArqueoCajaResponse(
            cuadre=cuadre,
            efectivo_esperado=efectivo_esperado,
            efectivo_contado=payload.efectivo_contado,
            diferencia=diferencia,
            digital_esperado=digital_val,
            digital_verificado=payload.digital_verificado or digital_val,
            mensaje=mensaje,
            fecha_cierre=ahora.strftime("%d/%m/%Y %I:%M %p")
        )

    @classmethod
    def gestionar_sobrepago(
        cls,
        db: Session,
        current_user: Usuario,
        payload: GestionSobrepagoRequest,
        client_ip: str = "127.0.0.1"
    ) -> GestionSobrepagoResponse:
        exceso = round(payload.monto_transferido - payload.monto_real_flete, 2)
        if exceso <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No existe sobrepago. El monto transferido es menor o igual al flete real."
            )

        tipo = payload.tipo_resolucion.lower().strip()
        if tipo not in ["vuelto_efectivo", "re_yapeo_digital", "saldo_a_favor"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de resolución '{payload.tipo_resolucion}' no válido. Use 'vuelto_efectivo', 're_yapeo_digital' o 'saldo_a_favor'."
            )

        # REGLA BR-COB-04 / BR-CAJ-05: Bloqueo estricto de efectivo mayor a S/ 20.00 (Prevención de Lavado UIF)
        if tipo == "vuelto_efectivo" and exceso > 20.00:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Por política de prevención de lavado de activos (Resolución SBS N° 789-2018 y Ley N° 28194), "
                    f"está terminantemente prohibido entregar más de S/ 20.00 en efectivo por abonos digitales. "
                    f"El sobrepago de S/ {exceso:.2f} debe resolverse vía 're_yapeo_digital' a la misma cuenta de origen o 'saldo_a_favor'."
                )
            )

        # Evaluación de riesgo PLAFT
        nivel_riesgo = "CRITICAL" if exceso > 500.00 else ("WARN" if exceso > 20.00 else "INFO")

        ahora = datetime.now(timezone.utc)
        cod_auth = f"AUT-SOB-{ahora.strftime('%Y%m%d%H%M')}-{current_user.id}"

        # Registro de auditoría forense
        registrar_auditoria_seguridad(
            db=db,
            evento="GESTION_SOBREPAGO_DIGITAL",
            usuario_id=current_user.id,
            direccion_ip=client_ip,
            detalles={
                "tracking": payload.codigo_tracking,
                "numero_operacion": payload.numero_operacion,
                "monto_real": payload.monto_real_flete,
                "monto_transferido": payload.monto_transferido,
                "exceso": exceso,
                "tipo_resolucion": tipo,
                "cuenta_destino": payload.cuenta_o_telefono_destino,
                "codigo_autorizacion": cod_auth,
                "observaciones": payload.observaciones
            },
            nivel_riesgo=nivel_riesgo
        )

        if tipo == "vuelto_efectivo":
            mensaje = f"Vuelto menor de S/ {exceso:.2f} entregado en efectivo y registrado como egreso en caja chica."
            estado = "liquidado_efectivo"
        elif tipo == "re_yapeo_digital":
            dest = payload.cuenta_o_telefono_destino or "titular de origen"
            mensaje = f"Extorno digital de S/ {exceso:.2f} autorizado vía re-yapeo hacia {dest}."
            estado = "extorno_digital_procesado"
        else:
            mensaje = f"Exceso de S/ {exceso:.2f} acreditado como saldo a favor en cuenta de cliente para futuros envíos."
            estado = "saldo_acreditado"

        return GestionSobrepagoResponse(
            codigo_tracking=payload.codigo_tracking,
            diferencia_exceso=exceso,
            tipo_resolucion=tipo,
            estado=estado,
            mensaje=mensaje,
            codigo_autorizacion=cod_auth,
            fecha_registro=ahora.strftime("%d/%m/%Y %I:%M %p")
        )

