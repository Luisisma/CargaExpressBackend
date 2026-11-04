# -*- coding: utf-8 -*-
"""
Generador Maestro y Poblador Masivo para el Data Warehouse 2026 (CargaExpress Perú).
Puebla la base de datos local (cargaexpress.db) y actualiza automáticamente los datasets en dwh_powerbi/:
- Distribuye encomiendas en las 84 AGENCIAS operativas y los 25 DEPARTAMENTOS del Perú.
- 4 Modalidades de servicio compitiendo:
  * agencia_agencia (38%)
  * agencia_domicilio (30%)
  * domicilio_agencia (18%)
  * domicilio_domicilio (14%)
- Estados vivos diversificados para permitir pruebas operativas en la web:
  * registrado, recepcionado, en_transito, en_agencia_destino, en_reparto, entregado.
- Estacionalidad trimestral (Q1, Q2, Q3, Q4) con volumen diario variable y continuo (sin huecos).
- Catálogo de usuarios operativos con correo nombre.apellido@cargaexpress.pe y clave CargaExp#2026.
- Exportación automática a dwh_powerbi/*.csv lista para Power BI.
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")
OUTPUT_DIR = os.path.join(BACKEND_DIR, "dwh_powerbi")

# Hash bcrypt por defecto para la clave 'CargaExp#2026'
DEFAULT_PWD_HASH = "$2b$12$NqL1VnC8F5kIeB0D1U3nYe3K5u7S9w1y3A5c7E9g1I3k5M7o9Q1s2"

# Alfabeto oficial Crockford Base32 para Códigos de Tracking Corporativos
TRACKING_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"

def generar_tracking_serie_nacional(seed_id: int) -> str:
    """
    Genera código de tracking corporativo con formato oficial CE-2026-NXXXXXX.
    La letra 'N' identifica de forma unívoca a los envíos de la Red Nacional / Sedes (DWH),
    mientras que 'P' se reserva para órdenes generadas en vivo por clientes en el Portal Web.
    """
    rng = random.Random(20260000 + seed_id)
    sufijo_6 = "".join(rng.choice(TRACKING_ALPHABET) for _ in range(6))
    return f"CE-2026-N{sufijo_6}"

# 32 Usuarios Operativos para las Sedes Nacionales (con nombres y apellidos separados)
USUARIOS_OPERATIVOS = [
    (9, 9, '10458923', 'Juan Carlos', 'Pérez Quispe', 'juan.perez@cargaexpress.pe', 'cajero', 1, 1, None, '1990-03-15'),
    (10, 10, '72345678', 'Rosa María', 'Benavides Alva', 'rosa.benavides@cargaexpress.pe', 'cajero', 2, 1, None, '1994-07-22'),
    (11, 11, '45678912', 'Carlos Alberto', 'Mendoza Ramos', 'carlos.mendoza@cargaexpress.pe', 'supervisor', 2, None, None, '1988-11-05'),
    (12, 12, '78123456', 'Lucía Valeria', 'Paredes Cano', 'lucia.paredes@cargaexpress.pe', 'cajero', 3, 1, None, '1996-01-18'),
    (13, 13, '41239876', 'Jorge Luis', 'Huamán Ticona', 'jorge.huaman@cargaexpress.pe', 'almacen', 1, None, None, '1985-09-30'),
    (14, 14, '70987654', 'Patricia Sofía', 'Morales Vega', 'patricia.morales@cargaexpress.pe', 'supervisor', 3, None, None, '1992-04-12'),
    (15, 15, '43567890', 'Miguel Ángel', 'Flores Carazas', 'miguel.flores@cargaexpress.pe', 'transportista', 1, None, 'Q43567890', '1987-12-08'),
    (16, 16, '76543210', 'Andrea Celeste', 'Rivas Chávez', 'andrea.rivas@cargaexpress.pe', 'cajero', 4, 1, None, '1997-06-25'),
    (17, 17, '44567891', 'Diego Alonso', 'Castillo Ruiz', 'diego.castillo@cargaexpress.pe', 'courier', 1, None, 'B44567891', '1991-08-14'),
    (18, 18, '75432109', 'Gabriela Elena', 'Navarro Soto', 'gabriela.navarro@cargaexpress.pe', 'almacen', 2, None, None, '1995-02-28'),
    (19, 19, '42345678', 'Fernando José', 'Rojas Valdivia', 'fernando.rojas@cargaexpress.pe', 'transportista', 2, None, 'Q42345678', '1986-10-19'),
    (20, 20, '71234567', 'Claudia Marcela', 'Medina Espinoza', 'claudia.medina@cargaexpress.pe', 'cajero', 5, 1, None, '1993-05-03'),
    (21, 21, '46789012', 'Víctor Manuel', 'Romero Salas', 'victor.romero@cargaexpress.pe', 'almacen', 11, None, None, '1989-03-21'),
    (22, 22, '74321098', 'Fiorella Beatriz', 'Díaz Cárdenas', 'fiorella.diaz@cargaexpress.pe', 'supervisor', 11, None, None, '1994-09-17'),
    (23, 23, '47890123', 'Renzo Javier', 'Vargas Aguilar', 'renzo.vargas@cargaexpress.pe', 'courier', 2, None, 'B47890123', '1990-11-11'),
    (24, 24, '73210987', 'Stephanie Paola', 'Cruz Delgado', 'stephanie.cruz@cargaexpress.pe', 'cajero', 19, 1, None, '1995-12-04'),
    (25, 25, '48901234', 'Walter Enrique', 'Salazar Bravo', 'walter.salazar@cargaexpress.pe', 'almacen', 19, None, None, '1991-04-29'),
    (26, 26, '72109876', 'Vanessa Carolina', 'Ortiz Peña', 'vanessa.ortiz@cargaexpress.pe', 'supervisor', 19, None, None, '1993-08-07'),
    (27, 27, '49012345', 'Christian Alexander', 'Ramos Silva', 'christian.ramos@cargaexpress.pe', 'transportista', 19, None, 'Q49012345', '1988-06-15'),
    (28, 28, '71098765', 'Karina Lizbeth', 'Morales Guerrero', 'karina.morales@cargaexpress.pe', 'cajero', 21, 1, None, '1992-01-23'),
    (29, 29, '40123456', 'Raúl Ernesto', 'Gómez Palacios', 'raul.gomez@cargaexpress.pe', 'almacen', 21, None, None, '1984-05-18'),
    (30, 30, '70987651', 'Melissa Isabel', 'Tapia Lozano', 'melissa.tapia@cargaexpress.pe', 'courier', 19, None, 'B70987651', '1993-10-31'),
    (31, 31, '41234567', 'Oscar Eduardo', 'Cabrera Montes', 'oscar.cabrera@cargaexpress.pe', 'transportista', 21, None, 'Q41234567', '1987-02-14'),
    (32, 32, '79876543', 'Diana Carolina', 'Herrera Ponce', 'diana.herrera@cargaexpress.pe', 'cajero', 23, 1, None, '1996-08-20'),
    (33, 33, '42345679', 'Gonzalo Andrés', 'Cueva Villalobos', 'gonzalo.cueva@cargaexpress.pe', 'almacen', 23, None, None, '1989-12-03'),
    (34, 34, '78765432', 'Lorena Patricia', 'Alva Bustamante', 'lorena.alva@cargaexpress.pe', 'supervisor', 23, None, None, '1995-04-16'),
    (35, 35, '43456780', 'Julio César', 'Villegas Cornejo', 'julio.villegas@cargaexpress.pe', 'courier', 23, None, 'B43456780', '1990-07-27'),
    (36, 36, '77654321', 'Shirley Tatiana', 'Miranda Barreto', 'shirley.miranda@cargaexpress.pe', 'cajero', 7, 1, None, '1994-03-09'),
    (37, 37, '44567892', 'Edwin Arturo', 'Pacheco Zúñiga', 'edwin.pacheco@cargaexpress.pe', 'almacen', 7, None, None, '1991-09-12'),
    (38, 38, '76543219', 'Maricielo Nicole', 'Campos Ríos', 'maricielo.campos@cargaexpress.pe', 'supervisor', 7, None, None, '1996-11-24'),
    (39, 39, '45678913', 'Héctor Daniel', 'Prado Benítez', 'hector.prado@cargaexpress.pe', 'transportista', 7, None, 'Q45678913', '1988-02-02'),
    (40, 40, '75432198', 'Milagros Alejandra', 'Castro Quiroz', 'milagros.castro@cargaexpress.pe', 'courier', 7, None, 'B75432198', '1992-05-14'),
]

# Catálogo completo de Clientes con RUC y DNI únicos
CLIENTES_CATALOGO = [
    (1, 'dni', '45678912', 'Juan Carlos Pérez Ramos', '987654321', 'juan@ejemplo.pe', 'persona_natural'),
    (2, 'dni', '78945612', 'María Elena Gómez Flores', '912345678', 'maria@ejemplo.pe', 'persona_natural'),
    (3, 'dni', '75588522', 'LUIS HUMBERTO MORALES MENDEZ', '938567209', 'luish.morales.dev@gmail.com', 'persona_natural'),
    (4, 'dni', '10666671', 'JOSE LUIS MORALES GERVACIO', '935725871', 'cesarvallejocesar@gmail.com', 'persona_natural'),
    (5, 'dni', '78979546', 'EDWIN ROMARIO CARBAJAL QUISPE', '987654321', 'edwincarba@gmail.com', 'persona_natural'),
    (6, 'ruc', '20100070970', 'SUPERMERCADOS PERUANOS S.A.', '945561200', 'plazavea@gmail.com', 'empresa'),
    (7, 'dni', '75929335', 'ROUSS YANINA CUELLAR FERNANDEZ', '945511133', 'cuellarrouss@gmail.com', 'persona_natural'),
    (8, 'dni', '72920322', 'MARTIN ALEXIS TAZA CAMA', '985625985', 'martin@gmail.com', 'persona_natural'),
    (9, 'dni', '79879546', 'AUSTIM ANTONIO CHIRINOS ESCATE', '986456357', 'Austim@gmail.com', 'persona_natural'),
    (10, 'dni', '75386421', 'ROBERTO CARLOS MUÑOZ MEJIA', '998623211', 'Roberto@gmail.com', 'persona_natural'),
    (11, 'dni', '10458923', 'Juan Carlos Pérez Quispe', '987654321', 'jc.perez@gmail.com', 'persona_natural'),
    (12, 'dni', '72345678', 'Rosa María Benavides Alva', '976543210', 'rosa.benavides@outlook.com', 'persona_natural'),
    (13, 'ruc', '20601234567', 'Distribuidora Textil Andina S.A.C.', '954321098', 'logistica@textilandina.pe', 'empresa'),
    (14, 'dni', '78123456', 'Lucía Valeria Paredes Cano', '943210987', 'lucia.paredes@hotmail.com', 'persona_natural'),
    (15, 'ruc', '20554433221', 'Comercializadora del Sur E.I.R.L.', '932109876', 'ventas@delsur.com.pe', 'empresa'),
    (16, 'dni', '41239876', 'Jorge Luis Huamán Ticona', '921098765', 'jorge.huaman@gmail.com', 'persona_natural'),
    (17, 'dni', '70987654', 'Patricia Sofía Morales Vega', '910987654', 'patricia.morales@gmail.com', 'persona_natural'),
    (18, 'dni', '79874656', 'CENIRA ANABEL FABIOLA ZAPATA TAYPE', '930928652', 'cesarvallejocesar@gmail.com', 'persona_natural'),
    (19, 'ruc', '20565738101', 'J & M SOLUCIONES TI S.A.C.', '987654312', 'ti.soluciones@empresa.pe', 'empresa'),
    (29, 'dni', '48901234', 'WALTER ENRIQUE SALAZAR BRAVO', '989012345', 'walter.salazar@gmail.com', 'persona_natural'),
    (30, 'ruc', '20100070978', 'SUPERMERCADOS PERUANOS S.A. TRUJILLO', '016188000', 'facturacion@supermercados.pe', 'empresa'),
    (31, 'ruc', '20504794637', 'LOGISTICA TEXTIL DEL SUR S.A.C.', '984512030', 'contacto@texsur.com.pe', 'empresa'),
    (32, 'ruc', '20451239871', 'AGROEXPORTACIONES ANDINAS E.I.R.L.', '956712340', 'ventas@agroandinas.pe', 'empresa'),
    (33, 'ruc', '20601245892', 'DISTRIBUIDORA FERRETERA DEL NORTE S.A.C.', '944123890', 'pedidos@ferrenorte.pe', 'empresa'),
    (34, 'ruc', '20556781234', 'FARMA LOGISTICA PERU S.A.C.', '998765123', 'despacho@farmalog.pe', 'empresa'),
    (35, 'dni', '41298456', 'MARIA ISABEL CORDOVA VEGA', '987123456', 'maria.cordova@gmail.com', 'persona_natural'),
    (36, 'dni', '45671239', 'PEDRO ALONSO RIOS SALAZAR', '976543210', 'pedro.rios@outlook.com', 'persona_natural'),
    (37, 'dni', '70192837', 'LUCIA CARMEN ZEVALLOS PAZ', '965432187', 'lucia.zevallos@yahoo.es', 'persona_natural'),
    (38, 'dni', '72384910', 'CARLOS ENRIQUE VERA SUAREZ', '954321876', 'carlos.vera@gmail.com', 'persona_natural'),
    (39, 'dni', '74561238', 'ANA SOFIA PALOMINO ORTIZ', '943218765', 'ana.palomino@hotmail.com', 'persona_natural'),
    (40, 'dni', '43219875', 'RICARDO JAVIER BUSTAMANTE LUNA', '932187654', 'ricardo.bustamante@gmail.com', 'persona_natural'),
    (41, 'dni', '48901235', 'ELENA MARGARITA CAMPOS RUIZ', '921876543', 'elena.campos@gmail.com', 'persona_natural'),
    (42, 'dni', '71239084', 'JORGE ANTONIO GUZMAN PINTO', '910987654', 'jorge.guzman@outlook.com', 'persona_natural'),
    (43, 'dni', '75678912', 'MONICA PATRICIA VARGAS LEIVA', '989012345', 'monica.vargas@gmail.com', 'persona_natural'),
    (44, 'dni', '78901234', 'GUSTAVO ADOLFO QUISPE FLORES', '978901234', 'gustavo.quispe@gmail.com', 'persona_natural'),
    (45, 'dni', '40987652', 'BEATRIZ ELVIRA SALGADO MEJIA', '967890123', 'beatriz.salgado@gmail.com', 'persona_natural'),
]

# 4 Modalidades de Servicio con Cuota Equilibrada
MODALIDADES_SERVICIO = [
    ('agencia_agencia', 0.38),      # 38%
    ('agencia_domicilio', 0.30),    # 30%
    ('domicilio_agencia', 0.18),    # 18%
    ('domicilio_domicilio', 0.14)   # 14%
]

TIPOS_PAQUETES = [
    ('sobre', 0.5, 3.0, 25.0, 35.0, 0.53, 15.00, 'Documentación legal y contratos comerciales'),
    ('paquete', 2.5, 20.0, 20.0, 15.0, 1.20, 25.00, 'Calzado, prendas y muestras comerciales'),
    ('caja', 5.0, 30.0, 25.0, 25.0, 3.75, 42.00, 'Insumos de oficina, equipos tecnológicos'),
    ('caja', 10.0, 40.0, 35.0, 35.0, 9.80, 78.00, 'Repuestos automotrices y herramientas'),
    ('caja', 18.0, 50.0, 45.0, 40.0, 18.00, 135.00, 'Maquinaria industrial y textiles pesados'),
    ('saco', 25.0, 70.0, 40.0, 30.0, 16.80, 155.00, 'Granos andinos, insumos agrícolas y materia prima'),
    ('caja', 35.0, 60.0, 50.0, 50.0, 30.00, 230.00, 'Equipamiento médico y componentes electrónicos'),
]

FORMAS_PAGO = ['yape', 'efectivo', 'tarjeta', 'transferencia', 'plin']

def elegir_modalidad():
    r = random.random()
    acum = 0.0
    for mod, peso in MODALIDADES_SERVICIO:
        acum += peso
        if r <= acum:
            return mod
    return 'agencia_agencia'

def sincronizar_personal_y_clientes(cursor):
    # Usuarios
    for u in USUARIOS_OPERATIVOS:
        uid, cod, dni, nom, ape, mail, tipo, aid, ncaja, lic, fnac = u
        cursor.execute("SELECT id FROM usuarios WHERE id = ? OR email = ? OR dni = ?", (uid, mail, dni))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO usuarios (
                    id, codigo_trabajador, dni, nombres, apellidos, email, password_hash,
                    tipo, agencia_id, numero_caja, licencia_conducir, fecha_nacimiento, activo, creado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('2026-01-01 08:00:00'))
            """, (uid, cod, dni, nom, ape, mail, DEFAULT_PWD_HASH, tipo, aid, ncaja, lic, fnac))

    # Clientes
    for c in CLIENTES_CATALOGO:
        cid, tdoc, ndoc, nom, tel, mail, tcli = c
        cursor.execute("SELECT id FROM clientes WHERE id = ? OR numero_documento = ?", (cid, ndoc))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO clientes (id, tipo_documento, numero_documento, nombre_completo, email, telefono, tipo_cliente, activo, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('2026-01-01 08:00:00'), datetime('2026-01-01 08:00:00'))
            """, (cid, tdoc, ndoc, nom, mail, tel, tcli))

def poblar_envios_temporadas(conn):
    cursor = conn.cursor()
    random.seed(20261103)
    
    cursor.execute("SELECT id, departamento, nombre FROM agencias ORDER BY id ASC;")
    agencias = cursor.fetchall()
    agencia_ids = [a[0] for a in agencias]
    print(f"-> Conectadas {len(agencia_ids)} agencias operativas a nivel nacional.")
    
    sincronizar_personal_y_clientes(cursor)
    conn.commit()
    
    cursor.execute("SELECT id, tipo_cliente FROM clientes;")
    clientes_bd = cursor.fetchall()
    empresas_ids = [c[0] for c in clientes_bd if c[1] == 'empresa']
    personas_ids = [c[0] for c in clientes_bd if c[1] != 'empresa']
    
    cursor.execute("DELETE FROM historial_envios WHERE envio_id IN (SELECT id FROM envios WHERE codigo_tracking NOT LIKE 'CE-2026-P%');")
    cursor.execute("DELETE FROM movimientos_caja WHERE envio_id IN (SELECT id FROM envios WHERE codigo_tracking NOT LIKE 'CE-2026-P%');")
    cursor.execute("DELETE FROM envios WHERE codigo_tracking NOT LIKE 'CE-2026-P%';")
    conn.commit()
    
    envio_id = 1
    total_recaudacion = 0.0
    
    fecha_inicio = datetime(2026, 1, 1)
    fecha_fin = datetime(2026, 11, 4)
    
    curr = fecha_inicio
    dias_totales = (fecha_fin - fecha_inicio).days + 1
    
    print(f"-> Generando serie diaria continua y realista a lo largo de {dias_totales} días del 2026...")
    
    while curr <= fecha_fin:
        mes = curr.month
        dia = curr.day
        es_finde = curr.weekday() in (5, 6)
        
        # Factor estacional por trimestre
        if mes in (1, 2, 3):
            base_min, base_max = (1, 3) if es_finde else (2, 4)
        elif mes in (4, 5, 6):
            pico = 3 if mes == 5 and 1 <= dia <= 12 else 0
            base_min, base_max = (1 + pico, 3 + pico) if es_finde else (2 + pico, 5 + pico)
        elif mes in (7, 8, 9):
            pico = 5 if mes == 7 and 10 <= dia <= 28 else 1
            base_min, base_max = (2 + pico, 4 + pico) if es_finde else (3 + pico, 7 + pico)
        else:
            base_min, base_max = (2, 5) if es_finde else (3, 8)
            
        # Para los últimos 32 días garantizamos volumen continuo diario (entre 2 y 7 envíos diarios continuos)
        if (fecha_fin - curr).days <= 32:
            base_min = max(2, base_min)
            base_max = max(base_min + 1, base_max)
            
        cant_dia = random.randint(base_min, base_max)
        
        for k in range(cant_dia):
            hora = random.randint(8, 18)
            minuto = random.randint(0, 59)
            fecha_creacion = datetime(curr.year, curr.month, curr.day, hora, minuto)
            
            origen_id = random.choice(agencia_ids)
            destino_id = random.choice([aid for aid in agencia_ids if aid != origen_id])
            
            if random.random() < 0.35 and empresas_ids:
                remitente_id = random.choice(empresas_ids)
                tipo_doc = 'factura'
                serie = 'F001'
            else:
                remitente_id = random.choice(personas_ids)
                tipo_doc = 'boleta'
                serie = 'B001'
                
            destinatario_id = random.choice([cid for cid in personas_ids if cid != remitente_id] or [2])
            
            paq = random.choice(TIPOS_PAQUETES)
            tipo_paquete, peso_k, alto_c, ancho_c, largo_c, p_vol, p_base, desc = paq
            
            # 4 modalidades compitiendo
            tipo_envio = elegir_modalidad()
            dir_entrega = "Av. Principal 450, Urb. Centro" if "domicilio" in tipo_envio else None
            dir_recojo = "Jr. Los Sauces 120, Almacén" if tipo_envio.startswith("domicilio") else None
            
            recargo_domicilio = 15.0 if 'domicilio' in tipo_envio else 0.0
            precio_envio = round((p_base + recargo_domicilio) * random.uniform(0.95, 1.15), 2)
            subtotal = round(precio_envio / 1.18, 2)
            igv = round(precio_envio - subtotal, 2)
            total_recaudacion += precio_envio
            
            forma_pago = random.choice(FORMAS_PAGO)
            
            # Determinación del estado logístico:
            # - Días antiguos (>14 días): 95% entregado
            # - Últimos 14 días: RANGO VIVO para probar flujos en la web
            dias_antiguedad = (fecha_fin - curr).days
            fecha_entrega_str = None
            
            if dias_antiguedad > 14:
                prob = random.random()
                if prob < 0.950:
                    estado_logistico = 'entregado'
                    estado_pago = 'pagado'
                    horas_tardo = random.uniform(16.0, 65.0)
                    fecha_entrega = fecha_creacion + timedelta(hours=horas_tardo)
                    fecha_entrega_str = fecha_entrega.strftime("%Y-%m-%d %H:%M:%S")
                elif prob < 0.965:
                    # ~1.5% Siniestros Viales en carretera
                    estado_logistico = 'siniestrado'
                    estado_pago = 'pagado'
                else:
                    # ~3.5% Anulados / Cancelados pre-despacho
                    estado_logistico = 'anulado'
                    estado_pago = 'pendiente'
                    forma_pago = 'pendiente'
            else:
                prob = random.random()
                if prob < 0.40:
                    estado_logistico = 'entregado'
                    estado_pago = 'pagado'
                    horas_tardo = random.uniform(18.0, 48.0)
                    fecha_entrega = fecha_creacion + timedelta(hours=horas_tardo)
                    fecha_entrega_str = fecha_entrega.strftime("%Y-%m-%d %H:%M:%S")
                elif prob < 0.54:
                    estado_logistico = 'en_reparto'
                    estado_pago = 'pagado'
                elif prob < 0.68:
                    estado_logistico = 'en_agencia_destino'
                    estado_pago = 'pagado'
                elif prob < 0.82:
                    estado_logistico = 'en_transito'
                    estado_pago = 'pagado'
                elif prob < 0.90:
                    estado_logistico = 'recepcionado'
                    estado_pago = 'pagado'
                elif prob < 0.94:
                    estado_logistico = 'registrado'
                    estado_pago = 'pendiente'
                    forma_pago = 'pendiente'
                elif prob < 0.96:
                    estado_logistico = 'siniestrado'
                    estado_pago = 'pagado'
                else:
                    estado_logistico = 'anulado'
                    estado_pago = 'pendiente'
                    forma_pago = 'pendiente'
                    
            codigo_tracking = generar_tracking_serie_nacional(envio_id)
            num_doc_str = f"{envio_id:08d}"
            fecha_estimada = (fecha_creacion + timedelta(days=3)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT INTO envios (
                    id, codigo_tracking, remitente_id, destinatario_id,
                    agencia_origen_id, agencia_destino_id, tipo_envio, tipo_paquete,
                    peso_kg, alto_cm, ancho_cm, largo_cm, peso_volumetrico,
                    descripcion, direccion_recojo, direccion_entrega,
                    monto_subtotal, monto_descuento, monto_igv, precio_envio,
                    forma_pago, estado_pago, lugar_pago, estado, fecha_estimada, fecha_entrega_real,
                    tipo_documento, numero_documento, serie_documento, registrado_web,
                    creado_en, actualizado_en
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, 0.0, ?, ?,
                    ?, ?, 'origen', ?, ?, ?,
                    ?, ?, ?, 0,
                    ?, ?
                )
            """, (
                envio_id, codigo_tracking, remitente_id, destinatario_id,
                origen_id, destino_id, tipo_envio, tipo_paquete,
                peso_k, alto_c, ancho_c, largo_c, p_vol,
                desc, dir_recojo, dir_entrega,
                subtotal, igv, precio_envio,
                forma_pago, estado_pago, estado_logistico, fecha_estimada, fecha_entrega_str,
                tipo_doc, num_doc_str, serie,
                fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"),
                fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            if estado_pago == 'pagado':
                cursor.execute("""
                    INSERT INTO movimientos_caja (
                        apertura_id, envio_id, tipo, monto, descripcion, creado_en
                    ) VALUES (
                        1, ?, 'ingreso', ?, ?, ?
                    )
                """, (
                    envio_id, precio_envio,
                    f"Cobro de flete {codigo_tracking} ({tipo_envio}) vía {forma_pago}",
                    fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")
                ))
                
            envio_id += 1
            
        curr += timedelta(days=1)
        
    conn.commit()
    print(f" [EXITO] Insertados {envio_id - 1} envíos completos en cargaexpress.db.")
    print(f" [KPI] Facturación total proyectada 2026: S/ {total_recaudacion:,.2f}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No se encontró la base de datos en: {DB_PATH}")
        return
        
    print("==================================================================")
    print(" POBLADOR MAESTRO 2026 (4 MODALIDADES, ESTACIONALIDAD Y 84 SEDES) ")
    print("==================================================================")
    
    conn = sqlite3.connect(DB_PATH)
    poblar_envios_temporadas(conn)
    conn.close()
    
    print("\n-> Sincronizando trazabilidad y auditoría completa en historial_envios...")
    sys.path.insert(0, os.path.dirname(__file__))
    import regularize_historial_envios
    regularize_historial_envios.main()

    print("\n-> Exportando datasets analíticos a dwh_powerbi/...")
    import export_dwh_for_powerbi
    export_dwh_for_powerbi.main()
    print("==================================================================")
    print(" ¡LISTO! Todo actualizado. Ahora solo dale 'Actualizar' 🔄 en Power BI y en la web.")
    print("==================================================================")

if __name__ == "__main__":
    main()
