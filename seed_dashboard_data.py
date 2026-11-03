import os
import sqlite3
import random
from datetime import datetime, timezone, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "cargaexpress.db")

print(f"--> Conectando a Base de Datos SQLite directa: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

try:
    # 1. Verificar agencias disponibles
    cursor.execute("SELECT id, nombre, departamento FROM agencias WHERE estado = 'habilitado'")
    agencias = cursor.fetchall()
    if not agencias:
        print("[!] No hay agencias en la base de datos.")
        exit(1)

    agencia_ids = [a[0] for a in agencias]
    agencia_map = {a[0]: f"{a[1]} ({a[2]})" for a in agencias}
    print(f"[OK] {len(agencias)} Agencias operativas encontradas.")

    # 2. Clientes Semilla Variados
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

    cliente_ids = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for c in clientes_data:
        cursor.execute("SELECT id FROM clientes WHERE numero_documento = ?", (c[1],))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO clientes (tipo_documento, numero_documento, nombre_completo, email, telefono, tipo_cliente, activo, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (c[0], c[1], c[2], c[3], c[4], c[5], now_str, now_str))
            cliente_ids.append(cursor.lastrowid)
        else:
            cliente_ids.append(row[0])

    conn.commit()
    print(f"[OK] {len(cliente_ids)} Clientes verificados en la base de datos.")

    # 3. Plan de Ingesta Coherente: 24 Envíos distribuidos en los últimos 14 días
    ahora_utc = datetime.now(timezone.utc)

    envios_plan = [
        # Días pasados concluidos
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
        
        # Envíos en ciclo activo actual (Embudo Logístico en movimiento)
        {"dias": 3, "tipo_p": "caja", "peso": 5.5, "precio": 32.00, "medio": "yape", "estado": "en_agencia_destino", "pago": "pagado", "desc": "Cámara fotográfica y accesorios"},
        {"dias": 3, "tipo_p": "sobre", "peso": 0.5, "precio": 7.50, "medio": "efectivo", "estado": "en_agencia_destino", "pago": "pagado", "desc": "Partidas de nacimiento apostilladas"},
        {"dias": 2, "tipo_p": "paquete", "peso": 3.8, "precio": 24.50, "medio": "plin", "estado": "en_agencia_destino", "pago": "pagado", "desc": "Libros de texto y manuales"},
        
        {"dias": 2, "tipo_p": "saco", "peso": 22.0, "precio": 74.00, "medio": "tarjeta", "estado": "en_ruta", "pago": "pagado", "desc": "Fardo de telas e hilos de alpaca"},
        {"dias": 1, "tipo_p": "caja", "peso": 8.0, "precio": 42.00, "medio": "yape", "estado": "en_ruta", "pago": "pagado", "desc": "Filtros de aceite y repuestos mecánicos"},
        {"dias": 1, "tipo_p": "paquete", "peso": 2.2, "precio": 18.50, "medio": "efectivo", "estado": "en_ruta", "pago": "pagado", "desc": "Prendas de vestir personalizadas"},
        
        {"dias": 1, "tipo_p": "sobre", "peso": 0.2, "precio": 7.50, "medio": "yape", "estado": "recepcionado", "pago": "pagado", "desc": "Pasaportes visados y tickets"},
        {"dias": 0, "tipo_p": "caja", "peso": 3.5, "precio": 23.50, "medio": "yape", "estado": "recepcionado", "pago": "pagado", "desc": "Equipos de sonido y micrófonos"},
        
        # Envíos de HOY (Flujo vivo y pedidos web)
        {"dias": 0, "tipo_p": "saco", "peso": 12.0, "precio": 45.00, "medio": "efectivo", "estado": "en_ruta", "pago": "pagado", "desc": "Zapatos de cuero arequipeño"},
        {"dias": 0, "tipo_p": "caja", "peso": 1.5, "precio": 15.50, "medio": "plin", "estado": "registrado", "pago": "pendiente", "desc": "Pre-registro web: Cosméticos y cremas"},
        {"dias": 0, "tipo_p": "sobre", "peso": 0.4, "precio": 7.50, "medio": "yape", "estado": "registrado", "pago": "pendiente", "desc": "Pre-registro web: Escrituras de inmueble"},
        {"dias": 0, "tipo_p": "paquete", "peso": 4.5, "precio": 27.00, "medio": "efectivo", "estado": "registrado", "pago": "pagado", "desc": "Artesanías y cerámicas decorativas"}
    ]

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    total_insertados = 0

    for idx, item in enumerate(envios_plan, start=201):
        sufijo = "".join(random.choices(alphabet, k=6))
        codigo_trk = f"CE-2026-D{sufijo}"

        dt_registro = ahora_utc - timedelta(days=item["dias"], hours=random.randint(1, 6), minutes=random.randint(5, 50))
        dt_str = dt_registro.strftime("%Y-%m-%d %H:%M:%S")

        rem_id = random.choice(cliente_ids)
        dest_candidates = [c for c in cliente_ids if c != rem_id]
        dest_id = random.choice(dest_candidates) if dest_candidates else rem_id

        orig_id = agencia_ids[0] if (idx % 2 == 0) else (agencia_ids[1] if len(agencia_ids) > 1 else agencia_ids[0])
        dest_id_ag = agencia_ids[2] if len(agencia_ids) > 2 else (agencia_ids[1] if len(agencia_ids) > 1 else agencia_ids[0])
        if orig_id == dest_id_ag and len(agencia_ids) > 1:
            dest_id_ag = [a for a in agencia_ids if a != orig_id][0]

        precio = float(item["precio"])
        subtotal = round(precio / 1.18, 2)
        igv = round(precio - subtotal, 2)
        tipo_env = "agencia_agencia" if item["tipo_p"] != "sobre" else "agencia_domicilio"

        cursor.execute("""
            INSERT INTO envios (
                codigo_tracking, remitente_id, destinatario_id, agencia_origen_id, agencia_destino_id,
                tipo_envio, tipo_paquete, peso_kg, peso_volumetrico, descripcion,
                monto_subtotal, monto_descuento, monto_igv, precio_envio,
                forma_pago, estado_pago, lugar_pago, estado, tipo_documento,
                registrado_web, creado_en, actualizado_en
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.00, ?, ?, ?, ?, 'origen', ?, 'boleta', ?, ?, ?)
        """, (
            codigo_trk, rem_id, dest_id, orig_id, dest_id_ag,
            tipo_env, item["tipo_p"], item["peso"], round(item["peso"] * 0.8, 2), item["desc"],
            subtotal, igv, precio,
            item["medio"], item["pago"], item["estado"],
            1 if item["estado"] == "registrado" else 0, dt_str, dt_str
        ))
        envio_id = cursor.lastrowid

        # Hitos de historial consistentes
        cursor.execute("""
            INSERT INTO historial_envios (envio_id, estado, descripcion, ubicacion, creado_en)
            VALUES (?, 'REGISTRADO', 'Pre-registro completado vía portal de autoservicio.', ?, ?)
        """, (envio_id, agencia_map.get(orig_id, "Sede Origen"), dt_str))

        if item["estado"] in ["recepcionado", "en_ruta", "en_agencia_destino", "entregado"]:
            h_dt = (dt_registro + timedelta(hours=random.randint(1, 2))).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO historial_envios (envio_id, estado, descripcion, ubicacion, creado_en)
                VALUES (?, 'RECEPCIONADO', 'Paquete formalizado y pesado en balanza de mostrador.', ?, ?)
            """, (envio_id, agencia_map.get(orig_id, "Sede Origen"), h_dt))

        if item["estado"] in ["en_ruta", "en_agencia_destino", "entregado"]:
            h_dt = (dt_registro + timedelta(hours=random.randint(3, 6))).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO historial_envios (envio_id, estado, descripcion, ubicacion, creado_en)
                VALUES (?, 'EN_RUTA', 'Carga despachada en camión de ruta interprovincial.', 'En Carretera / Panamericana', ?)
            """, (envio_id, h_dt))

        if item["estado"] in ["en_agencia_destino", "entregado"]:
            h_dt = (dt_registro + timedelta(hours=random.randint(8, 16))).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO historial_envios (envio_id, estado, descripcion, ubicacion, creado_en)
                VALUES (?, 'EN_AGENCIA_DESTINO', 'Descargado del camión y listo en estantería para retiro.', ?, ?)
            """, (envio_id, agencia_map.get(dest_id_ag, "Sede Destino"), h_dt))

        if item["estado"] == "entregado":
            h_dt = (dt_registro + timedelta(hours=random.randint(18, 30))).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO historial_envios (envio_id, estado, descripcion, ubicacion, creado_en)
                VALUES (?, 'ENTREGADO', 'Entregado conforme en ventanilla tras verificar DNI físico.', ?, ?)
            """, (envio_id, agencia_map.get(dest_id_ag, "Sede Destino"), h_dt))

        total_insertados += 1

    conn.commit()
    print(f"\n[ÉXITO TOTAL] {total_insertados} Envíos y sus hitos de auditoría insertados directamente.")
    print("El Dashboard Administrativo ya cuenta con volumen histórico, curvas de tendencia y métricas activas.")

finally:
    conn.close()
