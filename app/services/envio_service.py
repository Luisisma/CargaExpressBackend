from typing import Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from app.models.envio import Envio, HistorialEnvio
from app.models.usuario import Usuario
from app.schemas.envio import RecepcionEnvioRequest, EntregaEnvioRequest, DeclararSiniestroRequest
from decimal import Decimal
from app.services.email_service import enviar_correo_cambio_estado


def _notificar_clientes_cambio_estado(
    envio: Envio,
    nuevo_estado: str,
    descripcion: str,
    ubicacion: str = None,
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Notifica por correo a remitente y destinatario sobre el nuevo estado del envío.
    Si se suministra background_tasks, se despacha asíncronamente en segundo plano
    sin bloquear la transacción HTTP principal.
    """
    destinatarios_notificados = set()
    notificaciones = []

    if envio.remitente and envio.remitente.email and envio.remitente.email.strip():
        email_rem = envio.remitente.email.strip()
        destinatarios_notificados.add(email_rem.lower())
        notificaciones.append({
            "email": email_rem,
            "nombre": envio.remitente.nombre_completo,
            "tracking": envio.codigo_tracking,
            "nuevo_estado": nuevo_estado,
            "descripcion": descripcion,
            "ubicacion": ubicacion
        })

    if envio.destinatario and envio.destinatario.email and envio.destinatario.email.strip():
        email_dest = envio.destinatario.email.strip()
        if email_dest.lower() not in destinatarios_notificados:
            notificaciones.append({
                "email": email_dest,
                "nombre": envio.destinatario.nombre_completo,
                "tracking": envio.codigo_tracking,
                "nuevo_estado": nuevo_estado,
                "descripcion": descripcion,
                "ubicacion": ubicacion
            })

    for notif in notificaciones:
        if background_tasks:
            background_tasks.add_task(
                enviar_correo_cambio_estado,
                destinatario_email=notif["email"],
                destinatario_nombre=notif["nombre"],
                codigo_tracking=notif["tracking"],
                nuevo_estado=notif["nuevo_estado"],
                descripcion=notif["descripcion"],
                ubicacion=notif["ubicacion"]
            )
        else:
            try:
                enviar_correo_cambio_estado(
                    destinatario_email=notif["email"],
                    destinatario_nombre=notif["nombre"],
                    codigo_tracking=notif["tracking"],
                    nuevo_estado=notif["nuevo_estado"],
                    descripcion=notif["descripcion"],
                    ubicacion=notif["ubicacion"]
                )
            except Exception:
                pass


class EnvioService:
    @classmethod
    def recepcionar(
        cls,
        db: Session,
        codigo_tracking: str,
        usuario_id: int,
        agencia_id: int,
        req: RecepcionEnvioRequest,
        background_tasks: Optional[BackgroundTasks] = None
    ):
        codigo_limpio = codigo_tracking.strip().upper()
        envio = db.execute(
            select(Envio).where(Envio.codigo_tracking == codigo_limpio)
        ).scalar_one_or_none()
        
        if not envio:
            raise ValueError(f"No se encontró el envío {codigo_limpio}.")
            
        if envio.estado != "registrado":
            raise ValueError(f"El envío se encuentra en estado '{envio.estado}', no puede ser recepcionado.")
            
        # Recalcular precio oficial (similar al cotizador público)
        peso_vol = round((req.largo_real_cm * req.ancho_real_cm * req.alto_real_cm) / 6000, 2)
        peso_liquidable = max(req.peso_real_kg, peso_vol)

        tarifa_base = 8.00
        tarifa_peso = round(peso_liquidable * 2.50, 2)
        recargo_dom = 12.00 if envio.tipo_envio in ["agencia_domicilio", "domicilio_domicilio"] else 0.00
        recargo_recojo = 15.00 if envio.tipo_envio in ["domicilio_agencia", "domicilio_domicilio"] else 0.00
        nuevo_total = round(tarifa_base + tarifa_peso + recargo_dom + recargo_recojo, 2)

        diferencia = nuevo_total - float(envio.precio_envio)
        mensaje_historial = "Recepcionado en agencia origen."
        medio_cobro = (getattr(req, "forma_pago", None) or "efectivo").lower()

        # Si ya había pagado online pero hay diferencia en contra del cliente
        if envio.estado_pago == "pagado" and diferencia > 0.50:
            mensaje_historial += f" Se cobró reintegro por S/ {diferencia:.2f} ({medio_cobro.upper()}) debido a mayor peso/volumen verificado en balanza."
            # Mantenemos el estado como pagado, asumiendo que el cajero le acaba de cobrar la diferencia
            
        # Si estaba pendiente, se asume que el cajero acaba de cobrar el nuevo total
        if envio.estado_pago == "pendiente":
            envio.estado_pago = "pagado"
            envio.lugar_pago = "agencia"
            envio.forma_pago = medio_cobro 

        # Actualizar la DB con las dimensiones físicas reales comprobadas
        envio.estado = "recepcionado"
        envio.peso_kg = Decimal(str(req.peso_real_kg))
        envio.largo_cm = Decimal(str(req.largo_real_cm))
        envio.ancho_cm = Decimal(str(req.ancho_real_cm))
        envio.alto_cm = Decimal(str(req.alto_real_cm))
        envio.peso_volumetrico = Decimal(str(peso_vol))
        
        # Actualizar precios
        if envio.estado_pago == "pagado" and diferencia < -0.50:
            mensaje_historial += f" Cliente sobre-declaró el peso/volumen en web. El precio original (S/ {envio.precio_envio}) se mantiene por política de empresa sin devolución parcial."
        else:
            envio.precio_envio = Decimal(str(nuevo_total))
            envio.monto_subtotal = Decimal(str(round(nuevo_total / 1.18, 2)))
            envio.monto_igv = Decimal(str(round(nuevo_total - float(envio.monto_subtotal), 2)))
        
        envio.actualizado_en = datetime.now(timezone.utc)
        
        if req.observaciones:
            mensaje_historial += f" Observaciones: {req.observaciones}"
            
        hito = HistorialEnvio(
            envio_id=envio.id,
            estado="recepcionado",
            descripcion=mensaje_historial,
            ubicacion=f"Agencia ID: {agencia_id}" if agencia_id else "Agencia Origen",
            usuario_id=usuario_id
        )
        
        db.add(hito)
        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="recepcionado",
            descripcion=mensaje_historial,
            ubicacion=f"Agencia ID: {agencia_id}" if agencia_id else "Agencia Origen",
            background_tasks=background_tasks
        )

        return envio
        
    @classmethod
    def despachar(
        cls,
        db: Session,
        codigo_tracking: str,
        usuario_id: int,
        agencia_id: int,
        notas: str = None,
        background_tasks: Optional[BackgroundTasks] = None
    ):
        codigo_limpio = codigo_tracking.strip().upper()
        envio = db.execute(select(Envio).where(Envio.codigo_tracking == codigo_limpio)).scalar_one_or_none()
        if not envio: 
            raise ValueError(f"No se encontró el envío {codigo_limpio}.")
            
        if envio.estado != "recepcionado":
            raise ValueError(f"El envío se encuentra en estado '{envio.estado}'. Debe estar 'recepcionado' para ser despachado.")
            
        envio.estado = "en_ruta"
        envio.actualizado_en = datetime.now(timezone.utc)
        
        desc = "Despachado y en tránsito hacia la agencia destino."
        if notas: 
            desc += f" Notas: {notas}"
            
        db.add(HistorialEnvio(
            envio_id=envio.id,
            estado="en_ruta",
            descripcion=desc,
            ubicacion=f"Agencia (Origen) ID: {agencia_id}" if agencia_id else "Ruta",
            usuario_id=usuario_id
        ))
        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="en_ruta",
            descripcion=desc,
            ubicacion=f"Agencia (Origen) ID: {agencia_id}" if agencia_id else "Ruta Interprovincial",
            background_tasks=background_tasks
        )

        return envio

    @classmethod
    def arribar(
        cls,
        db: Session,
        codigo_tracking: str,
        usuario_id: int,
        agencia_id: int,
        notas: str = None,
        background_tasks: Optional[BackgroundTasks] = None
    ):
        codigo_limpio = codigo_tracking.strip().upper()
        envio = db.execute(select(Envio).where(Envio.codigo_tracking == codigo_limpio)).scalar_one_or_none()
        if not envio: 
            raise ValueError(f"No se encontró el envío {codigo_limpio}.")
            
        if envio.estado != "en_ruta":
            raise ValueError(f"El envío está en estado '{envio.estado}'. Debe estar 'en_ruta' para recibirlo en destino.")
            
        envio.estado = "en_agencia_destino"
        envio.actualizado_en = datetime.now(timezone.utc)
        
        desc = "Arribó a la ciudad destino y está bajo custodia de la agencia destino."
        if notas: 
            desc += f" Notas: {notas}"
            
        db.add(HistorialEnvio(
            envio_id=envio.id,
            estado="en_agencia_destino",
            descripcion=desc,
            ubicacion=f"Agencia (Destino) ID: {agencia_id}" if agencia_id else "Agencia Destino",
            usuario_id=usuario_id
        ))
        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="en_agencia_destino",
            descripcion=desc,
            ubicacion=f"Agencia (Destino) ID: {agencia_id}" if agencia_id else "Agencia Destino",
            background_tasks=background_tasks
        )

        return envio

    @classmethod
    def entregar(
        cls,
        db: Session,
        codigo_tracking: str,
        usuario_id: int,
        agencia_id: int,
        req: EntregaEnvioRequest,
        background_tasks: Optional[BackgroundTasks] = None
    ):
        codigo_limpio = codigo_tracking.strip().upper()
        envio = db.execute(select(Envio).where(Envio.codigo_tracking == codigo_limpio)).scalar_one_or_none()
        if not envio: 
            raise ValueError(f"No se encontró el envío {codigo_limpio}.")
            
        if envio.estado not in ["en_agencia_destino", "en_reparto"]:
            raise ValueError(f"El envío se encuentra en estado '{envio.estado}'. Debe estar 'en_agencia_destino' o 'en_reparto' para ser entregado.")
            
        # Si era contraentrega y aún no estaba pagado, se formaliza el pago en destino
        if envio.estado_pago != "pagado":
            envio.estado_pago = "pagado"
            envio.lugar_pago = "destino"
            envio.forma_pago = "efectivo"

        ahora = datetime.now(timezone.utc)
        envio.estado = "entregado"
        envio.fecha_entrega_real = ahora
        envio.actualizado_en = ahora
        
        desc = f"Entregado exitosamente a {req.nombre_receptor} (DNI/Doc: {req.dni_receptor}). Condición: {req.parentesco_o_relacion}."
        if req.observaciones:
            desc += f" Observaciones: {req.observaciones}"
            
        db.add(HistorialEnvio(
            envio_id=envio.id,
            estado="entregado",
            descripcion=desc,
            ubicacion=f"Agencia ID: {agencia_id}" if agencia_id else "Ventanilla Destino",
            usuario_id=usuario_id
        ))
        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="entregado",
            descripcion=desc,
            ubicacion=f"Agencia ID: {agencia_id}" if agencia_id else "Ventanilla Destino",
            background_tasks=background_tasks
        )

        return envio

    @classmethod
    def declarar_siniestro(
        cls,
        db: Session,
        codigo_tracking: str,
        usuario_actual: Usuario,
        req: DeclararSiniestroRequest,
        background_tasks: Optional[BackgroundTasks] = None
    ):
        codigo_limpio = codigo_tracking.strip().upper()
        envio = db.execute(select(Envio).where(Envio.codigo_tracking == codigo_limpio)).scalar_one_or_none()
        if not envio:
            raise ValueError(f"No se encontró el envío {codigo_limpio}.")

        if envio.estado == "siniestrado":
            raise ValueError("El envío ya ha sido declarado previamente en estado 'siniestrado'.")

        ahora = datetime.now(timezone.utc)
        envio.estado = "siniestrado"
        envio.actualizado_en = ahora

        tipo_fmt = req.tipo_siniestro.replace("_", " ").title()
        desc = f"INCIDENCIA GRAVE / SINIESTRO DECLARADO ({tipo_fmt}). Detalle: {req.descripcion}."
        if req.numero_denuncia_policial:
            desc += f" Denuncia Policial PNP: {req.numero_denuncia_policial}."
        if req.responsable_reporte:
            desc += f" Reportado por: {req.responsable_reporte}."
        desc += f" Autorizado por Administrador/Supervisor #{usuario_actual.id} ({usuario_actual.nombre_completo}). Carga congelada para liquidación de seguro."

        ubicacion_hito = f"Agencia {usuario_actual.agencia.nombre}" if (usuario_actual.agencia and hasattr(usuario_actual.agencia, 'nombre')) else "Operaciones / En Tránsito"

        db.add(HistorialEnvio(
            envio_id=envio.id,
            estado="siniestrado",
            descripcion=desc,
            ubicacion=ubicacion_hito,
            usuario_id=usuario_actual.id
        ))
        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="siniestrado",
            descripcion=desc,
            ubicacion=ubicacion_hito,
            background_tasks=background_tasks
        )

        return envio
