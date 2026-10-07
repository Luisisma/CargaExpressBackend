import random
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.agencia import Agencia
from app.models.cliente import Cliente
from app.models.envio import Envio, HistorialEnvio
from app.schemas.publico import (
    CotizacionRequest,
    CotizacionResponse,
    TrackingPublicoResponse,
    TrackingHitoResponse,
    ClientePublicoResponse,
    RegistroPedidoPublicoRequest,
    PedidoCreadoResponse
)


def enmascarar_nombre(nombre: str) -> str:
    """Enmascara nombres protegiendo la identidad (OWASP API1 / PII). Ej: Juan Carlos -> J*** C*****"""
    if not nombre:
        return "Anónimo"
    partes = nombre.strip().split()
    enmascaradas = []
    for p in partes:
        if len(p) <= 2:
            enmascaradas.append(p[0] + "*")
        else:
            enmascaradas.append(p[0] + "*" * (len(p) - 1))
    return " ".join(enmascaradas)


def enmascarar_telefono(tel: Optional[str]) -> Optional[str]:
    """Enmascara teléfono mostrando solo los últimos 3 dígitos."""
    if not tel or len(tel.strip()) < 4:
        return None
    limpio = tel.strip()
    return "*" * (len(limpio) - 3) + limpio[-3:]


def enmascarar_email(email: Optional[str]) -> Optional[str]:
    """Enmascara correo electrónico. Ej: j***z@dominio.com"""
    if not email or "@" not in email:
        return None
    usuario, dominio = email.split("@", 1)
    if len(usuario) <= 2:
        usuario_mask = usuario[0] + "*"
    else:
        usuario_mask = usuario[0] + "*" * (len(usuario) - 2) + usuario[-1]
    return f"{usuario_mask}@{dominio}"


class PublicoService:

    @staticmethod
    def listar_agencias_activas(db: Session) -> List[Agencia]:
        """Obtiene todas las agencias activas en el sistema."""
        stmt = select(Agencia).where(
            func.lower(Agencia.estado).in_(["habilitado", "activo"])
        ).order_by(Agencia.departamento, Agencia.nombre)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def cotizar(req: CotizacionRequest) -> CotizacionResponse:
        """
        Motor oficial de cotización de CargaExpress Perú.
        Cálculo seguro en backend sin manipulación de tarifas en cliente.
        """
        peso_vol = round((req.largo_cm * req.ancho_cm * req.alto_cm) / 6000.0, 2)
        peso_liquidable = max(round(req.peso_kg, 2), peso_vol)

        tarifa_base = 8.00
        tarifa_peso = round(peso_liquidable * 2.50, 2)
        recargo_dom = 12.00 if req.tipo_envio == "agencia_domicilio" else 0.00
        total = round(tarifa_base + tarifa_peso + recargo_dom, 2)

        return CotizacionResponse(
            peso_fisico=round(req.peso_kg, 2),
            peso_volumetrico=peso_vol,
            peso_liquidable=peso_liquidable,
            tarifa_base=tarifa_base,
            tarifa_peso_adicional=tarifa_peso,
            recargo_domicilio=recargo_dom,
            precio_total=total
        )

    @staticmethod
    def tracking(db: Session, codigo: str) -> Optional[TrackingPublicoResponse]:
        """Busca un envío por código y entrega su línea de tiempo protegiendo datos personales."""
        codigo_limpio = codigo.strip().upper()
        stmt = select(Envio).where(Envio.codigo_tracking == codigo_limpio)
        envio = db.execute(stmt).scalar_one_or_none()

        if not envio:
            return None

        # Línea de tiempo
        hitos = [
            TrackingHitoResponse(
                estado=h.estado.upper(),
                descripcion=h.descripcion,
                ubicacion=h.ubicacion or (envio.agencia_origen.nombre if envio.agencia_origen else "Almacén Central"),
                fecha=h.creado_en
            )
            for h in envio.historial
        ]

        origen_txt = f"{envio.agencia_origen.departamento} ({envio.agencia_origen.nombre})" if envio.agencia_origen else "Sede Origen"
        destino_txt = f"{envio.agencia_destino.departamento} ({envio.agencia_destino.nombre})" if envio.agencia_destino else "Sede Destino"

        return TrackingPublicoResponse(
            codigo_tracking=envio.codigo_tracking,
            estado=envio.estado.upper(),
            tipo_envio=envio.tipo_envio,
            tipo_paquete=envio.tipo_paquete,
            remitente=enmascarar_nombre(envio.remitente.nombre_completo if envio.remitente else ""),
            destinatario=enmascarar_nombre(envio.destinatario.nombre_completo if envio.destinatario else ""),
            origen=origen_txt,
            destino=destino_txt,
            fecha_estimada=envio.fecha_estimada,
            creado_en=envio.creado_en,
            historial=hitos
        )

    @staticmethod
    def buscar_cliente(db: Session, doc: str) -> ClientePublicoResponse:
        """Autocompleta nombre del cliente protegiendo teléfonos y correos completos."""
        doc_limpio = doc.strip()
        stmt = select(Cliente).where(Cliente.numero_documento == doc_limpio)
        cliente = db.execute(stmt).scalar_one_or_none()

        if not cliente:
            return ClientePublicoResponse(encontrado=False)

        return ClientePublicoResponse(
            encontrado=True,
            tipo_documento=cliente.tipo_documento,
            numero_documento=cliente.numero_documento,
            nombre_completo=cliente.nombre_completo,
            telefono_enmascarado=enmascarar_telefono(cliente.telefono),
            email_enmascarado=enmascarar_email(cliente.email)
        )

    @classmethod
    def _obtener_o_crear_cliente(
        cls,
        db: Session,
        tipo_doc: str,
        num_doc: str,
        nombre: str,
        email: Optional[str],
        tel: Optional[str]
    ) -> Cliente:
        """Obtiene o actualiza un cliente en la tabla clientes."""
        stmt = select(Cliente).where(Cliente.numero_documento == num_doc.strip())
        cliente = db.execute(stmt).scalar_one_or_none()

        tipo_cliente = "empresa" if tipo_doc == "ruc" else "persona_natural"

        if cliente:
            # Actualizar datos de contacto si fueron provistos
            if email:
                cliente.email = email.strip()
            if tel:
                cliente.telefono = tel.strip()
            return cliente
        else:
            nuevo = Cliente(
                tipo_documento=tipo_doc,
                numero_documento=num_doc.strip(),
                nombre_completo=nombre.strip(),
                email=email.strip() if email else None,
                telefono=tel.strip() if tel else None,
                tipo_cliente=tipo_cliente,
                activo=True
            )
            db.add(nuevo)
            db.flush()
            return nuevo

    @classmethod
    def registrar_pedido_web(
        cls,
        db: Session,
        req: RegistroPedidoPublicoRequest
    ) -> PedidoCreadoResponse:
        """
        Transacción atómica de registro de pedido web.
        Cumple con desglose contable 3NF y tabla de auditoría de hitos.
        """
        # 1. Validar agencias
        origen = db.get(Agencia, req.agencia_origen_id)
        destino = db.get(Agencia, req.agencia_destino_id)
        if not origen or not destino:
            raise ValueError("Las agencias de origen o destino especificadas no son válidas.")

        # 2. Gestionar clientes
        remitente = cls._obtener_o_crear_cliente(
            db, req.rem_tipo_doc, req.rem_num_doc, req.rem_nombre, req.rem_email, req.rem_telefono
        )
        destinatario = cls._obtener_o_crear_cliente(
            db, req.dest_tipo_doc, req.dest_num_doc, req.dest_nombre, req.dest_email, req.dest_telefono
        )

        # 3. Calcular tarifas de forma oficial
        cotizacion = cls.cotizar(
            CotizacionRequest(
                agencia_origen_id=req.agencia_origen_id,
                agencia_destino_id=req.agencia_destino_id,
                tipo_envio=req.tipo_envio,
                peso_kg=req.peso_kg,
                largo_cm=req.largo_cm or 20.0,
                ancho_cm=req.ancho_cm or 20.0,
                alto_cm=req.alto_cm or 20.0
            )
        )

        precio_total = Decimal(str(cotizacion.precio_total))
        # Desglose contable (IGV 18% Perú)
        subtotal = round(precio_total / Decimal("1.18"), 2)
        igv = round(precio_total - subtotal, 2)

        # 4. Generar código correlativo de tracking seguro: CE-YYYY-NNNNN
        anio_actual = datetime.now(timezone.utc).year
        total_envios_anio = db.execute(select(func.count(Envio.id))).scalar() or 0
        correlativo = f"CE-{anio_actual}-{total_envios_anio + 1:05d}"

        # 5. Crear el registro del envío
        nuevo_envio = Envio(
            codigo_tracking=correlativo,
            remitente_id=remitente.id,
            destinatario_id=destinatario.id,
            agencia_origen_id=origen.id,
            agencia_destino_id=destino.id,
            tipo_envio=req.tipo_envio,
            tipo_paquete=req.tipo_paquete,
            peso_kg=Decimal(str(round(req.peso_kg, 2))),
            alto_cm=Decimal(str(req.alto_cm)) if req.alto_cm else None,
            ancho_cm=Decimal(str(req.ancho_cm)) if req.ancho_cm else None,
            largo_cm=Decimal(str(req.largo_cm)) if req.largo_cm else None,
            peso_volumetrico=Decimal(str(cotizacion.peso_volumetrico)),
            descripcion=req.descripcion,
            direccion_entrega=req.direccion_entrega,
            monto_subtotal=subtotal,
            monto_descuento=Decimal("0.00"),
            monto_igv=igv,
            precio_envio=precio_total,
            forma_pago="pendiente",
            estado_pago="pendiente",
            lugar_pago="origen",
            estado="registrado",
            tipo_documento="boleta" if req.rem_tipo_doc != "ruc" else "factura",
            registrado_web=True
        )
        db.add(nuevo_envio)
        db.flush()

        # 6. Registrar hito inicial en historial_envios
        hito_inicial = HistorialEnvio(
            envio_id=nuevo_envio.id,
            estado="registrado",
            descripcion="Pre-registro de envío completado vía portal web de autoservicio.",
            ubicacion=f"{origen.nombre} ({origen.departamento})"
        )
        db.add(hito_inicial)
        db.commit()

        return PedidoCreadoResponse(
            codigo_tracking=correlativo,
            precio_estimado=float(precio_total),
            monto_subtotal=float(subtotal),
            monto_igv=float(igv),
            estado="REGISTRADO",
            mensaje="Envío pre-registrado con éxito. Acérquese a la agencia de origen para despacharlo."
        )
