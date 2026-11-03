from typing import List, Optional
from datetime import datetime, timezone
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, desc

from app.models.envio import Envio, HistorialEnvio
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.schemas.envio import (
    CourierEntregaItem,
    IniciarRepartoRequest,
    EntregaCourierRequest
)
from app.services.audit_service import registrar_auditoria_operacion
from app.services.email_service import enviar_correo_cambio_estado


def _notificar_clientes_cambio_estado(
    envio: Envio,
    nuevo_estado: str,
    descripcion: str,
    ubicacion: str = None,
    background_tasks: Optional[BackgroundTasks] = None
):
    """Notifica por correo a remitente y destinatario sobre el nuevo estado del envío en segundo plano."""
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


import os
import base64
import time
import re

def _guardar_evidencia_fisica(data_base64: Optional[str], codigo_tracking: str, sufijo: str) -> Optional[str]:
    """
    Decodifica una imagen en Base64 (firma o foto en puerta) y la persiste en disco local.
    Retorna la URL relativa servible (/uploads/evidencias/...) para guardarla en BD (VARCHAR 300).
    """
    if not data_base64 or not str(data_base64).strip():
        return None
    try:
        # Si ya es una URL o ruta estática corta, retornarla directamente
        if data_base64.startswith("/uploads/") or data_base64.startswith("http"):
            return data_base64[:300]

        # Extraer formato (png o jpg)
        extension = "png" if "image/png" in data_base64 else "jpg"
        if "," in data_base64:
            header, base64_str = data_base64.split(",", 1)
            if "png" in header:
                extension = "png"
            elif "jpeg" in header or "jpg" in header:
                extension = "jpg"
        else:
            base64_str = data_base64

        tracking_limpio = re.sub(r'[^A-Za-z0-9_-]', '', codigo_tracking)
        timestamp = int(time.time())
        filename = f"{tracking_limpio}_{sufijo}_{timestamp}.{extension}"

        # Directorio base en CargaExpressBackend/uploads/evidencias
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        carpeta = os.path.join(base_dir, "uploads", "evidencias")
        os.makedirs(carpeta, exist_ok=True)

        filepath = os.path.join(carpeta, filename)
        file_bytes = base64.b64decode(base64_str)
        with open(filepath, "wb") as f:
            f.write(file_bytes)

        return f"/uploads/evidencias/{filename}"
    except Exception:
        # Fallback de seguridad en caso de error de decodificación
        return data_base64[:300]


class CourierService:
    """
    Servicio especializado y desacoplado para la gestión de Última Milla (Reparto Urbano).
    Responsable de:
    - Listar asignaciones de delivery para el personal motorizado.
    - Transicionar estados a 'en_reparto' con asignación del courier_id.
    - Liquidar entregas domiciliarias con captura de firma y evidencia fotográfica Base64.
    """

    @classmethod
    def listar_entregas(
        cls,
        db: Session,
        usuario_actual: Usuario,
        filtro_estado: Optional[str] = None
    ) -> List[CourierEntregaItem]:
        rol = (usuario_actual.tipo or "courier").upper()

        stmt = (
            select(Envio)
            .where(Envio.tipo_envio.in_(["agencia_domicilio", "domicilio_domicilio"]))
            .order_by(desc(Envio.creado_en))
        )

        # Regla RBAC:
        # Si es COURIER / TRANSPORTISTA, ve encomiendas de su agencia en espera de reparto ('en_agencia_destino')
        # o aquellas que ya le fueron asignadas directamente a él (courier_id == su id).
        if rol in ["COURIER", "TRANSPORTISTA"]:
            condiciones_rol = [Envio.courier_id == usuario_actual.id]
            if usuario_actual.agencia_id:
                condiciones_rol.append(
                    and_(
                        Envio.agencia_destino_id == usuario_actual.agencia_id,
                        Envio.estado == "en_agencia_destino"
                    )
                )
            stmt = stmt.where(or_(*condiciones_rol))
        else:
            # ADMINISTRADOR / SUPERVISOR: pueden consultar la carga de su agencia o todo
            if usuario_actual.agencia_id and rol != "ADMINISTRADOR":
                stmt = stmt.where(Envio.agencia_destino_id == usuario_actual.agencia_id)

        if filtro_estado and filtro_estado.strip():
            stmt = stmt.where(Envio.estado == filtro_estado.strip().lower())
        else:
            # Por defecto en la vista operativa mostramos lo activo: en bodega de destino o en reparto
            stmt = stmt.where(Envio.estado.in_(["en_agencia_destino", "en_reparto", "entregado"]))

        envios_db = list(db.execute(stmt).scalars().all())

        items: List[CourierEntregaItem] = []
        for e in envios_db:
            courier_usr = db.get(Usuario, e.courier_id) if e.courier_id else None
            courier_nom = courier_usr.nombre_completo if courier_usr else None

            dest_nombre = e.destinatario.nombre_completo if e.destinatario else "Destinatario N/D"
            dest_tel = e.destinatario.telefono if e.destinatario else None
            agencia_dest = e.agencia_destino.nombre if e.agencia_destino else "Sede Destino"

            items.append(
                CourierEntregaItem(
                    id=e.id,
                    codigo_tracking=e.codigo_tracking,
                    destinatario=dest_nombre,
                    telefono=dest_tel,
                    direccion_entrega=e.direccion_entrega,
                    agencia_destino=agencia_dest,
                    tipo_envio=e.tipo_envio,
                    tipo_paquete=e.tipo_paquete,
                    peso_kg=float(e.peso_kg or 0.0),
                    estado=e.estado,
                    estado_pago=e.estado_pago,
                    precio_envio=float(e.precio_envio or 0.0),
                    courier_id=e.courier_id,
                    courier_nombre=courier_nom,
                    imagen_evidencia=e.imagen_evidencia,
                    creado_en=e.creado_en
                )
            )

        return items

    @classmethod
    def iniciar_reparto(
        cls,
        db: Session,
        identificador: str,
        usuario_actual: Usuario,
        req: IniciarRepartoRequest,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Envio:
        codigo_limpio = identificador.strip().upper()
        stmt = select(Envio)
        if identificador.isdigit():
            stmt = stmt.where(Envio.id == int(identificador))
        else:
            stmt = stmt.where(Envio.codigo_tracking == codigo_limpio)

        envio = db.execute(stmt).scalar_one_or_none()
        if not envio:
            raise ValueError(f"No se encontró la encomienda '{identificador}'.")

        # Validar tipo de envío
        if envio.tipo_envio not in ["agencia_domicilio", "domicilio_domicilio"]:
            raise ValueError(
                f"El envío '{envio.codigo_tracking}' tiene modalidad '{envio.tipo_envio}', "
                "la cual se entrega exclusivamente en ventanilla de agencia."
            )

        # Validar máquina de estados: debe estar disponible en agencia de destino
        if envio.estado not in ["en_agencia_destino", "en_reparto"]:
            raise ValueError(
                f"El envío se encuentra en estado '{envio.estado}'. "
                "Debe estar en 'en_agencia_destino' para iniciar la ruta de reparto."
            )

        # Determinar el courier asignado
        courier_id_asignar = req.courier_id
        if not courier_id_asignar:
            rol = (usuario_actual.tipo or "").upper()
            if rol in ["COURIER", "TRANSPORTISTA", "ADMINISTRADOR", "SUPERVISOR"]:
                courier_id_asignar = usuario_actual.id
            else:
                raise ValueError("Debe especificar el ID del courier que realizará la entrega.")

        courier_usr = db.get(Usuario, courier_id_asignar)
        if not courier_usr:
            raise ValueError(f"No existe ningún colaborador registrado con ID {courier_id_asignar}.")

        # Transición de estado
        envio.courier_id = courier_id_asignar
        envio.estado = "en_reparto"
        envio.actualizado_en = datetime.now(timezone.utc)

        detalle_historial = f"Paquete retirado de bodega e iniciado en ruta de reparto a domicilio con el courier {courier_usr.nombre_completo}."
        if req.notas:
            detalle_historial += f" Observaciones: {req.notas}"

        ubicacion_str = f"En Reparto Domiciliario - {envio.agencia_destino.departamento if envio.agencia_destino else 'Ciudad Destino'}"

        db.add(
            HistorialEnvio(
                envio_id=envio.id,
                estado="en_reparto",
                descripcion=detalle_historial,
                ubicacion=ubicacion_str,
                usuario_id=usuario_actual.id
            )
        )

        registrar_auditoria_operacion(
            db=db,
            usuario_id=usuario_actual.id,
            accion="INICIAR_REPARTO_DOMICILIARIO",
            tabla_afectada="envios",
            registro_id=envio.id,
            valores_previos={"estado": "en_agencia_destino", "courier_id": None},
            valores_nuevos={"estado": "en_reparto", "courier_id": courier_id_asignar}
        )

        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="en_reparto",
            descripcion=detalle_historial,
            ubicacion=ubicacion_str,
            background_tasks=background_tasks
        )

        return envio

    @classmethod
    def entregar_domicilio(
        cls,
        db: Session,
        identificador: str,
        usuario_actual: Usuario,
        req: EntregaCourierRequest,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Envio:
        codigo_limpio = identificador.strip().upper()
        stmt = select(Envio)
        if identificador.isdigit():
            stmt = stmt.where(Envio.id == int(identificador))
        else:
            stmt = stmt.where(Envio.codigo_tracking == codigo_limpio)

        envio = db.execute(stmt).scalar_one_or_none()
        if not envio:
            raise ValueError(f"No se encontró la encomienda '{identificador}'.")

        if envio.estado not in ["en_reparto", "en_agencia_destino"]:
            raise ValueError(
                f"El envío se encuentra en estado '{envio.estado}'. "
                "Debe estar 'en_reparto' para registrar la entrega a domicilio."
            )

        # Validación contable de pago contraentrega
        if envio.estado_pago != "pagado":
            if req.cobro_contraentrega_confirmado:
                envio.estado_pago = "pagado"
                envio.lugar_pago = "destino"
                envio.forma_pago = "efectivo"
            else:
                raise ValueError(
                    f"El envío {envio.codigo_tracking} tiene un saldo pendiente de S/ {envio.precio_envio:.2f}. "
                    "Debe confirmar la recepción del cobro contraentrega en puerta para liquidar la entrega."
                )

        ahora = datetime.now(timezone.utc)
        envio.estado = "entregado"
        envio.fecha_entrega_real = ahora
        envio.actualizado_en = ahora

        # Almacenamiento seguro de evidencias en disco y persistencia de URL en DB
        if req.firma_base64:
            envio.imagen_evidencia = _guardar_evidencia_fisica(req.firma_base64, envio.codigo_tracking, "firma")
        if req.foto_evidencia_base64:
            envio.imagen_recepcion = _guardar_evidencia_fisica(req.foto_evidencia_base64, envio.codigo_tracking, "foto")

        detalle_historial = (
            f"Entrega domiciliaria exitosa en {envio.direccion_entrega or 'dirección consignada'}. "
            f"Recibió: {req.nombre_receptor.strip()} (Doc: {req.dni_receptor.strip()}) - "
            f"Condición: {req.parentesco_o_relacion or 'Titular'}."
        )
        if req.observaciones:
            detalle_historial += f" Detalle: {req.observaciones}"

        db.add(
            HistorialEnvio(
                envio_id=envio.id,
                estado="entregado",
                descripcion=detalle_historial,
                ubicacion=f"Domicilio Destinatario - {envio.direccion_entrega or 'Puerta Destino'}",
                usuario_id=usuario_actual.id
            )
        )

        registrar_auditoria_operacion(
            db=db,
            usuario_id=usuario_actual.id,
            accion="ENTREGA_DOMICILIARIA_COMPLETADA",
            tabla_afectada="envios",
            registro_id=envio.id,
            valores_previos={"estado": "en_reparto", "estado_pago": envio.estado_pago},
            valores_nuevos={
                "estado": "entregado",
                "receptor": req.nombre_receptor,
                "dni_receptor": req.dni_receptor,
                "con_firma": bool(req.firma_base64),
                "con_foto": bool(req.foto_evidencia_base64)
            }
        )

        db.commit()
        db.refresh(envio)

        _notificar_clientes_cambio_estado(
            envio=envio,
            nuevo_estado="entregado",
            descripcion=detalle_historial,
            ubicacion=f"Domicilio Destinatario - {envio.direccion_entrega or 'Puerta Destino'}",
            background_tasks=background_tasks
        )

        return envio
