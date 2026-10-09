from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from app.models.envio import Envio, HistorialEnvio
from app.schemas.envio import RecepcionEnvioRequest, EntregaEnvioRequest
from decimal import Decimal

class EnvioService:
    @classmethod
    def recepcionar(cls, db: Session, codigo_tracking: str, usuario_id: int, agencia_id: int, req: RecepcionEnvioRequest):
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

        # Si ya había pagado online pero hay diferencia en contra del cliente
        if envio.estado_pago == "pagado" and diferencia > 0.50:
            mensaje_historial += f" Se cobró reintegro por S/ {diferencia:.2f} debido a mayor peso/volumen verificado en balanza."
            # Mantenemos el estado como pagado, asumiendo que el cajero le acaba de cobrar la diferencia
            
        # Si estaba pendiente, se asume que el cajero acaba de cobrar el nuevo total
        if envio.estado_pago == "pendiente":
            envio.estado_pago = "pagado"
            envio.lugar_pago = "agencia"
            envio.forma_pago = "efectivo" 

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
            ubicacion=f"Agencia ID: {agencia_id}" if agencia_id else "Agencia Origen"
        )
        
        db.add(hito)
        db.commit()
        db.refresh(envio)
        return envio
        
    @classmethod
    def despachar(cls, db: Session, codigo_tracking: str, usuario_id: int, agencia_id: int, notas: str = None):
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
            ubicacion=f"Agencia (Origen) ID: {agencia_id}" if agencia_id else "Ruta"
        ))
        db.commit()
        db.refresh(envio)
        return envio

    @classmethod
    def arribar(cls, db: Session, codigo_tracking: str, usuario_id: int, agencia_id: int, notas: str = None):
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
            ubicacion=f"Agencia (Destino) ID: {agencia_id}" if agencia_id else "Agencia Destino"
        ))
        db.commit()
        db.refresh(envio)
        return envio

    @classmethod
    def entregar(cls, db: Session, codigo_tracking: str, usuario_id: int, agencia_id: int, req: EntregaEnvioRequest):
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
        return envio
