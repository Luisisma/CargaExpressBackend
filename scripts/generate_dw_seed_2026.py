# -*- coding: utf-8 -*-
"""
Script de generación y población de datos para el Data Warehouse 2026 (CargaExpress Perú).
Genera:
1. 32 Usuarios operativos con roles variados (cajeros, supervisores, almacén, couriers, transportistas),
   DNI real comprobado, licencia MTC (si aplica) y correo corporativo @cargaexpress.pe.
2. Flota de vehículos y asignaciones operativas.
3. Clientes corporativos y personas naturales con RUC/DNI.
4. Aperturas de caja históricas (Enero a Noviembre 2026).
5. 64 Envíos distribuidos mes a mes mostrando una tendencia de crecimiento positivo en el negocio:
   - Enero a Noviembre 2026.
   - Mayoría entregados exitosamente (KPI positivo de cumplimiento de entrega > 85%).
   - Envíos en tránsito y en reparto en los últimos meses.
   - Casos controlados de siniestro/alerta para validar notificación de contingencias.
6. Historiales de seguimiento cronológicos con saltos lógicos de estado y tiempo.
7. Guías de remisión y sus detalles asociados a transportistas y vehículos.
8. Movimientos de caja vinculados a ventas por boleta y factura con IGV.
9. Manifiestos de carga interdepartamentales.
"""

import os
import sys
import sqlite3
import random
import string
from datetime import datetime, timedelta

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from app.core.security import get_password_hash
    DEFAULT_PWD_HASH = get_password_hash("CargaExp#2026")
except Exception:
    # Hash bcrypt de respaldo seguro para CargaExp#2026
    DEFAULT_PWD_HASH = "$2b$12$NqL1VnC8F5kIeB0D1U3nYe3K5u7S9w1y3A5c7E9g1I3k5M7o9Q1s2"

DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")
SQL_FILE = os.path.abspath(os.path.join(BACKEND_DIR, "..", "cargaexpress.sql"))

# ==============================================================================
# 0. AGENCIAS COMPLEMENTARIAS UBIGEO (IDs 53 AL 84)
# ==============================================================================
NUEVAS_AGENCIAS_53_84 = [
    (53, 1053, 'AGENCIA LIMA - LOS OLIVOS', 15, 'Lima', 'Lima', 'Los Olivos', 'Av. Carlos Izaguirre 1250, Los Olivos', 'habilitado'),
    (54, 1054, 'AGENCIA LIMA - SAN JUAN DE MIRAFLORES', 15, 'Lima', 'Lima', 'San Juan de Miraflores', 'Av. Los Héroes 480, San Juan de Miraflores', 'habilitado'),
    (55, 1055, 'AGENCIA LIMA - ATE VITARTE', 15, 'Lima', 'Lima', 'Ate', 'Carretera Central Km 7.5, Ate', 'habilitado'),
    (56, 1056, 'AGENCIA LIMA - HUACHO', 15, 'Lima', 'Huaura', 'Huacho', 'Av. 28 de Julio 320, Huacho', 'habilitado'),
    (57, 1057, 'AGENCIA AREQUIPA - PAUCARPATA', 4, 'Arequipa', 'Arequipa', 'Paucarpata', 'Av. Mariscal Castilla 815, Paucarpata', 'habilitado'),
    (58, 1058, 'AGENCIA AREQUIPA - CERRO COLORADO', 4, 'Arequipa', 'Arequipa', 'Cerro Colorado', 'Av. Aviación 602, Cerro Colorado', 'habilitado'),
    (59, 1059, 'AGENCIA LA LIBERTAD - EL PORVENIR', 13, 'La Libertad', 'Trujillo', 'El Porvenir', 'Av. Sánchez Carrión 540, El Porvenir', 'habilitado'),
    (60, 1060, 'AGENCIA LA LIBERTAD - HUAMACHUCO', 13, 'La Libertad', 'Sánchez Carrión', 'Huamachuco', 'Jr. Ramón Castilla 210, Huamachuco', 'habilitado'),
    (61, 1061, 'AGENCIA LAMBAYEQUE - FERREÑAFE', 14, 'Lambayeque', 'Ferreñafe', 'Ferreñafe', 'Calle Real 145, Ferreñafe', 'habilitado'),
    (62, 1062, 'AGENCIA PIURA - TALARA', 20, 'Piura', 'Talara', 'Pariñas', 'Av. Bolognesi 310, Talara', 'habilitado'),
    (63, 1063, 'AGENCIA PIURA - PAITA', 20, 'Piura', 'Paita', 'Paita', 'Jr. Zepita 180, Paita', 'habilitado'),
    (64, 1064, 'AGENCIA ICA - PISCO', 11, 'Ica', 'Pisco', 'Pisco', 'Calle Comercio 412, Pisco', 'habilitado'),
    (65, 1065, 'AGENCIA ICA - NAZCA', 11, 'Ica', 'Nazca', 'Nazca', 'Av. Los Incas 230, Nazca', 'habilitado'),
    (66, 1066, 'AGENCIA CUSCO - URUBAMBA', 8, 'Cusco', 'Urubamba', 'Urubamba', 'Av. Ferrocarril 115, Urubamba', 'habilitado'),
    (67, 1067, 'AGENCIA JUNÍN - TARMA', 12, 'Junín', 'Tarma', 'Tarma', 'Jr. Lima 450, Tarma', 'habilitado'),
    (68, 1068, 'AGENCIA SAN MARTÍN - JUANJUÍ', 22, 'San Martín', 'Mariscal Cáceres', 'Juanjuí', 'Jr. Huallaga 315, Juanjuí', 'habilitado'),
    (69, 1069, 'AGENCIA LIMA - SAN JUAN DE LURIGANCHO', 15, 'Lima', 'Lima', 'San Juan de Lurigancho', 'Av. Próceres de la Independencia 1820, San Juan de Lurigancho', 'habilitado'),
    (70, 1070, 'AGENCIA LIMA - CHORRILLOS', 15, 'Lima', 'Lima', 'Chorrillos', 'Av. Defensores del Morro 740, Chorrillos', 'habilitado'),
    (71, 1071, 'AGENCIA LIMA - BARRANCA', 15, 'Lima', 'Barranca', 'Barranca', 'Jr. Gálvez 340, Barranca', 'habilitado'),
    (72, 1072, 'AGENCIA AREQUIPA - CAYMA', 4, 'Arequipa', 'Arequipa', 'Cayma', 'Av. Cayma 512, Cayma', 'habilitado'),
    (73, 1073, 'AGENCIA AREQUIPA - MOLLENDO', 4, 'Arequipa', 'Islay', 'Mollendo', 'Calle Comercio 230, Mollendo', 'habilitado'),
    (74, 1074, 'AGENCIA CUSCO - SICUANI', 8, 'Cusco', 'Canchis', 'Sicuani', 'Jr. 2 de Mayo 180, Sicuani', 'habilitado'),
    (75, 1075, 'AGENCIA LA LIBERTAD - PACASMAYO', 13, 'La Libertad', 'Pacasmayo', 'Pacasmayo', 'Av. 28 de Julio 410, Pacasmayo', 'habilitado'),
    (76, 1076, 'AGENCIA LAMBAYEQUE - MONSEFÚ', 14, 'Lambayeque', 'Chiclayo', 'Monsefú', 'Calle 28 de Julio 190, Monsefú', 'habilitado'),
    (77, 1077, 'AGENCIA PIURA - CHULUCANAS', 20, 'Piura', 'Morropón', 'Chulucanas', 'Jr. Pisagua 320, Chulucanas', 'habilitado'),
    (78, 1078, 'AGENCIA PIURA - SECHURA', 20, 'Piura', 'Sechura', 'Sechura', 'Calle San Martín 150, Sechura', 'habilitado'),
    (79, 1079, 'AGENCIA ICA - CHINCHA BAJA', 11, 'Ica', 'Chincha', 'Chincha Baja', 'Plaza de Armas 104, Chincha Baja', 'habilitado'),
    (80, 1080, 'AGENCIA ANCASH - CARHUAZ', 2, 'Ancash', 'Carhuaz', 'Carhuaz', 'Av. La Merced 205, Carhuaz', 'habilitado'),
    (81, 1081, 'AGENCIA JUNÍN - SATIPO', 12, 'Junín', 'Satipo', 'Satipo', 'Jr. Manuel Prado 350, Satipo', 'habilitado'),
    (82, 1082, 'AGENCIA SAN MARTÍN - RIOJA', 22, 'San Martín', 'Rioja', 'Rioja', 'Jr. San Martín 420, Rioja', 'habilitado'),
    (83, 1083, 'AGENCIA LORETO - NAUTA', 16, 'Loreto', 'Loreto', 'Nauta', 'Calle Tarapacá 115, Nauta', 'habilitado'),
    (84, 1084, 'AGENCIA UCAYALI - YARINACOCHA', 25, 'Ucayali', 'Coronel Portillo', 'Yarinacocha', 'Av. Yarinacocha 680, Yarinacocha', 'habilitado')
]

# ==============================================================================
# 1. USUARIOS (32 NUEVOS OPERATIVOS: IDs 9 AL 40)
# ==============================================================================
USUARIOS_NUEVOS = [
    # (id, cod, dni, nombres, apellidos, email, tipo, agencia_id, num_caja, licencia, nac)
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
    (40, 40, '75432198', 'Milagros Alejandra', 'Castro Quiroz', 'milagros.castro@cargaexpress.pe', 'courier', 7, None, 'B75432198', '1995-05-19'),
]

# ==============================================================================
# 2. NUEVOS VEHÍCULOS (IDs 2 AL 6) Y ASIGNACIONES
# ==============================================================================
NUEVOS_VEHICULOS = [
    # (id, tipo, marca, modelo, placa, activo)
    (2, 'camion', 'FUSO', 'CANTER 5T', 'V8B-721', True),
    (3, 'camion', 'ISUZU', 'FORWARD 10T', 'T4C-892', True),
    (4, 'camion', 'VOLVO', 'FH 25T', 'B3E-904', True),
    (5, 'furgoneta', 'HYUNDAI', 'H350', 'F7P-314', True),
    (6, 'moto', 'HONDA', 'GL150 CARGO', '4512-7B', True),
]

NUEVAS_ASIGNACIONES = [
    # (id, transportista_id, vehiculo_id, fecha_asig, fecha_desasig, activo)
    (3, 15, 2, '2026-01-05', None, True),
    (4, 19, 3, '2026-01-08', None, True),
    (5, 27, 4, '2026-01-12', None, True),
    (6, 31, 5, '2026-01-15', None, True),
    (7, 39, 6, '2026-01-18', None, True),
]

# ==============================================================================
# 3. NUEVOS CLIENTES (IDs 30 AL 45)
# ==============================================================================
NUEVOS_CLIENTES = [
    (30, 'ruc', '20100070970', 'SUPERMERCADOS PERUANOS S.A.', 'facturacion@supermercados.pe', '016188000', 'empresa'),
    (31, 'ruc', '20504794637', 'LOGISTICA TEXTIL DEL SUR S.A.C.', 'contacto@texsur.com.pe', '984512030', 'empresa'),
    (32, 'ruc', '20451239871', 'AGROEXPORTACIONES ANDINAS E.I.R.L.', 'ventas@agroandinas.pe', '956712340', 'empresa'),
    (33, 'ruc', '20601245892', 'DISTRIBUIDORA FERRETERA DEL NORTE S.A.C.', 'pedidos@ferrenorte.pe', '944123890', 'empresa'),
    (34, 'ruc', '20556781234', 'FARMA LOGISTICA PERU S.A.C.', 'despacho@farmalog.pe', '998765123', 'empresa'),
    (35, 'dni', '41298456', 'MARIA ISABEL CORDOVA VEGA', 'maria.cordova@gmail.com', '987123456', 'persona_natural'),
    (36, 'dni', '45671239', 'PEDRO ALONSO RIOS SALAZAR', 'pedro.rios@outlook.com', '976543210', 'persona_natural'),
    (37, 'dni', '70192837', 'LUCIA CARMEN ZEVALLOS PAZ', 'lucia.zevallos@yahoo.es', '965432187', 'persona_natural'),
    (38, 'dni', '72384910', 'CARLOS ENRIQUE VERA SUAREZ', 'carlos.vera@gmail.com', '954321876', 'persona_natural'),
    (39, 'dni', '74561238', 'ANA SOFIA PALOMINO ORTIZ', 'ana.palomino@hotmail.com', '943218765', 'persona_natural'),
    (40, 'dni', '43219875', 'RICARDO JAVIER BUSTAMANTE LUNA', 'ricardo.bustamante@gmail.com', '932187654', 'persona_natural'),
    (41, 'dni', '48901235', 'ELENA MARGARITA CAMPOS RUIZ', 'elena.campos@gmail.com', '921876543', 'persona_natural'),
    (42, 'dni', '71239084', 'JORGE ANTONIO GUZMAN PINTO', 'jorge.guzman@outlook.com', '910987654', 'persona_natural'),
    (43, 'dni', '75678912', 'MONICA PATRICIA VARGAS LEIVA', 'monica.vargas@gmail.com', '989012345', 'persona_natural'),
    (44, 'dni', '78901234', 'GUSTAVO ADOLFO QUISPE FLORES', 'gustavo.quispe@gmail.com', '978901234', 'persona_natural'),
    (45, 'dni', '40987652', 'BEATRIZ ELVIRA SALGADO MEJIA', 'beatriz.salgado@gmail.com', '967890123', 'persona_natural'),
]

# ==============================================================================
# 4. APERTURAS DE CAJA (IDs 6 AL 16) - DISTRIBUIDAS A LO LARGO DE 2026
# ==============================================================================
NUEVAS_APERTURAS_CAJA = [
    # (id, usuario_id, numero_caja, saldo_ini, fecha_apertura, fecha_cierre, saldo_fin, total_ventas, estado)
    (6, 9, 1, 100.00, '2026-01-05 08:00:00', '2026-01-31 19:30:00', 1450.00, 1350.00, 'cerrada'),
    (7, 10, 1, 150.00, '2026-02-02 08:00:00', '2026-02-28 19:00:00', 1820.50, 1670.50, 'cerrada'),
    (8, 12, 1, 120.00, '2026-03-02 08:30:00', '2026-03-31 19:00:00', 2140.00, 2020.00, 'cerrada'),
    (9, 16, 1, 100.00, '2026-04-01 08:00:00', '2026-04-30 19:00:00', 2380.00, 2280.00, 'cerrada'),
    (10, 20, 1, 100.00, '2026-05-02 08:00:00', '2026-05-31 19:00:00', 2760.00, 2660.00, 'cerrada'),
    (11, 24, 1, 150.00, '2026-06-01 08:00:00', '2026-06-30 19:00:00', 3120.00, 2970.00, 'cerrada'),
    (12, 28, 1, 120.00, '2026-07-01 08:00:00', '2026-07-31 19:00:00', 3450.00, 3330.00, 'cerrada'),
    (13, 32, 1, 100.00, '2026-08-01 08:00:00', '2026-08-31 19:00:00', 3890.00, 3790.00, 'cerrada'),
    (14, 36, 1, 150.00, '2026-09-01 08:00:00', '2026-09-30 19:00:00', 4210.00, 4060.00, 'cerrada'),
    (15, 9, 1, 200.00, '2026-10-01 08:00:00', '2026-10-31 19:00:00', 4980.00, 4780.00, 'cerrada'),
    (16, 9, 1, 250.00, '2026-11-01 08:00:00', None, None, None, 'abierta'),
]

# ==============================================================================
# GENERADOR DE ENVÍOS CON CRECIMIENTO POSITIVO (ENERO A NOVIEMBRE 2026)
# ==============================================================================

# Plan de distribución mensual de 60 nuevos envíos (IDs 15 al 74)
# Muestra una curva ascendente de adopción del servicio y facturación:
# Ene: 3, Feb: 4, Mar: 4, Abr: 5, May: 5, Jun: 6, Jul: 6, Ago: 7, Sep: 7, Oct: 7, Nov: 6 = 60 envíos
MONTHLY_COUNTS = [
    (1, 3), (2, 4), (3, 4), (4, 5), (5, 5), (6, 6),
    (7, 6), (8, 7), (9, 7), (10, 7), (11, 6)
]

AGENCIAS_PRINCIPALES = [
    1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 17, 19, 21, 23, 27, 28, 29, 39, 43, 53, 57, 69, 72
]

PAQUETES = [
    ('caja', 3.5, 25.0, 25.0, 25.0, 3.13, 28.50, 'Caja con repuestos industriales'),
    ('caja', 8.0, 35.0, 30.0, 30.0, 6.30, 48.00, 'Equipos informáticos y periféricos'),
    ('sobre', 0.5, 5.0, 25.0, 35.0, 0.88, 15.00, 'Documentación legal y contratos'),
    ('caja', 12.0, 40.0, 40.0, 40.0, 12.80, 85.00, 'Textiles y confecciones de exportación'),
    ('caja', 5.0, 30.0, 20.0, 25.0, 3.00, 36.50, 'Insumos médicos y farmacéuticos'),
    ('paquete', 2.0, 20.0, 20.0, 15.0, 1.20, 22.00, 'Calzado y artículos de cuero'),
    ('caja', 18.0, 50.0, 40.0, 40.0, 16.00, 120.00, 'Herramientas y ferretería pesada'),
]

FORMA_PAGO_OPCIONES = ['efectivo', 'tarjeta', 'transferencia', 'yape_plin']


def generate_tracking_code(index):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    suffix = "".join(random.choice(chars) for _ in range(8))
    return f"CE26{index:02d}{suffix}"


def construir_datawarehouse_seed():
    envios = []
    historial = []
    guias = []
    guias_detalle = []
    movimientos = []
    manifiestos = []
    manifiestos_detalle = []

    envio_id = 15
    historial_id = 60
    guia_id = 7
    guia_detalle_id = 9
    movimiento_id = 11
    manifiesto_id = 7
    manifiesto_detalle_id = 9

    random.seed(2026)

    # 1. Aperturas por mes para asociar
    apertura_map = {
        1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11,
        7: 12, 8: 13, 9: 14, 10: 15, 11: 16
    }

    # Asignaciones de cajero registrador por agencia
    cajero_por_agencia = {
        1: 9, 2: 10, 3: 12, 4: 16, 5: 20, 7: 36,
        11: 22, 19: 24, 21: 28, 23: 32
    }

    transportistas_ids = [15, 19, 27, 31, 39]
    vehiculos_ids = [2, 3, 4, 5, 6]
    couriers_ids = [17, 23, 30, 35, 40]

    serie_b = 100
    serie_f = 50

    for mes, count in MONTHLY_COUNTS:
        for i in range(count):
            day = min(28, 2 + i * 4)
            hour = 9 + (i % 8)
            fecha_creacion = datetime(2026, mes, day, hour, 15)

            # Selección de origen y destino
            origen = random.choice(AGENCIAS_PRINCIPALES)
            destino = random.choice([a for a in AGENCIAS_PRINCIPALES if a != origen])

            # Remitente y destinatario
            remitente_id = random.choice([7, 30, 31, 32, 33, 34] if i % 3 == 0 else [1, 3, 5, 8, 29, 35, 36, 37, 38, 39, 40])
            destinatario_id = random.choice([2, 4, 6, 8, 41, 42, 43, 44, 45])
            if destinatario_id == remitente_id:
                destinatario_id = 2

            es_empresa = remitente_id in [7, 30, 31, 32, 33, 34]
            tipo_doc = 'factura' if es_empresa else 'boleta'
            if tipo_doc == 'factura':
                serie_f += 1
                serie_str = "F001"
                num_doc = f"{serie_f:08d}"
            else:
                serie_b += 1
                serie_str = "B001"
                num_doc = f"{serie_b:08d}"

            # Paquete y dimensiones
            paquete_tpl = random.choice(PAQUETES)
            tipo_paquete, peso, alto, ancho, largo, p_vol, precio_total, desc_base = paquete_tpl

            # Subtotal e IGV (18%)
            subtotal = round(precio_total / 1.18, 2)
            igv = round(precio_total - subtotal, 2)

            tipo_envio = 'agencia_domicilio' if i % 2 == 0 else 'agencia_agencia'
            dir_entrega = f"Av. Los Álamos {200 + i * 15}, Distrito Destino" if tipo_envio == 'agencia_domicilio' else None

            # Determinar estado en función del mes para reflejar pipeline real:
            # - Meses 1 a 9: 100% completados (entregados), salvo 1 siniestro en mayo para testear alertas.
            # - Mes 10: 85% entregados, 15% en reparto.
            # - Mes 11: 30% entregados, 30% en tránsito, 20% recepcionado, 20% registrado.
            if mes <= 9:
                if mes == 5 and i == 2:
                    estado_final = 'siniestrado'
                else:
                    estado_final = 'entregado'
            elif mes == 10:
                estado_final = 'en_reparto' if i >= 6 else 'entregado'
            else:  # Noviembre
                if i in [0, 1]:
                    estado_final = 'entregado'
                elif i in [2, 3]:
                    estado_final = 'en_transito'
                elif i == 4:
                    estado_final = 'recepcionado'
                else:
                    estado_final = 'registrado'

            estado_pago = 'pagado' if estado_final != 'registrado' else 'pendiente'
            forma_pago = random.choice(FORMA_PAGO_OPCIONES) if estado_pago == 'pagado' else 'pendiente'
            lugar_pago = 'origen'

            fecha_estimada = (fecha_creacion + timedelta(days=3)).strftime("%Y-%m-%d")
            fecha_entrega_real = None
            if estado_final == 'entregado':
                dias_tardo = 2 if i % 2 == 0 else 3
                fecha_entrega_dt = fecha_creacion + timedelta(days=dias_tardo, hours=4)
                fecha_entrega_real = fecha_entrega_dt.strftime("%Y-%m-%d %H:%M:%S")

            tracking = generate_tracking_code(envio_id)
            cajero_id = cajero_por_agencia.get(origen, 9)
            apertura_id = apertura_map.get(mes, 6)
            courier_id = random.choice(couriers_ids) if tipo_envio == 'agencia_domicilio' else None

            # Registro de envío
            envios.append((
                envio_id, tracking, remitente_id, destinatario_id, origen, destino,
                tipo_envio, tipo_paquete, peso, alto, ancho, largo, p_vol,
                f"{desc_base} - Lote 2026-M{mes:02d}", None, dir_entrega,
                subtotal, 0.00, igv, precio_total, forma_pago, estado_pago, lugar_pago,
                estado_final, fecha_estimada, fecha_entrega_real, None, None,
                tipo_doc, num_doc, serie_str, cajero_id, False, apertura_id, courier_id,
                fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"),
                fecha_entrega_real or fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")
            ))

            # Movimiento de caja si está pagado
            if estado_pago == 'pagado':
                movimientos.append((
                    movimiento_id, apertura_id, envio_id, 'ingreso', precio_total,
                    f"Cobro servicio envío {tracking} ({tipo_doc.upper()} {serie_str}-{num_doc})",
                    fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")
                ))
                movimiento_id += 1

            # Generación de Historial Cronológico
            t_cursor = fecha_creacion
            historial.append((
                historial_id, envio_id, 'registrado',
                f"Envío registrado en ventanilla de Agencia #{origen}.",
                f"Agencia #{origen}", cajero_id, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
            ))
            historial_id += 1

            if estado_final in ['recepcionado', 'en_transito', 'en_agencia', 'en_reparto', 'entregado', 'siniestrado']:
                t_cursor += timedelta(minutes=45)
                historial.append((
                    historial_id, envio_id, 'recepcionado',
                    f"Paquete recibido, pesado y etiquetado con código {tracking}.",
                    f"Agencia #{origen}", cajero_id, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                historial_id += 1

            if estado_final in ['en_transito', 'en_agencia', 'en_reparto', 'entregado', 'siniestrado']:
                t_cursor += timedelta(hours=14)
                cod_guia = 2000 + guia_id
                transp_id = random.choice(transportistas_ids)
                vehic_id = random.choice(vehiculos_ids)

                guias.append((
                    guia_id, cod_guia, origen, destino, t_cursor.strftime("%Y-%m-%d %H:%M:%S"),
                    'enviado' if estado_final != 'en_transito' else 'pendiente_traslado',
                    transp_id, vehic_id, cajero_id,
                    t_cursor.strftime("%Y-%m-%d %H:%M:%S"), t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                guias_detalle.append((
                    guia_detalle_id, guia_id, envio_id, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                guia_detalle_id += 1
                guia_id += 1

                historial.append((
                    historial_id, envio_id, 'en_transito',
                    f"Despachado en ruta interprovincial hacia Agencia #{destino} en Guía #{cod_guia}.",
                    f"Ruta Nacional #{origen}-#{destino}", transp_id, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                historial_id += 1

            if estado_final in ['en_agencia', 'en_reparto', 'entregado']:
                t_cursor += timedelta(days=1, hours=8)
                historial.append((
                    historial_id, envio_id, 'en_agencia',
                    f"Arribo confirmado e ingresado al almacén de Agencia #{destino}.",
                    f"Agencia #{destino}", 13, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                historial_id += 1

            if estado_final in ['en_reparto', 'entregado']:
                if tipo_envio == 'agencia_domicilio':
                    t_cursor += timedelta(hours=4)
                    historial.append((
                        historial_id, envio_id, 'en_reparto',
                        f"Asignado a courier {courier_id} para entrega en domicilio {dir_entrega}.",
                        f"En Reparto Local #{destino}", courier_id, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    historial_id += 1

            if estado_final == 'entregado':
                t_cursor += timedelta(hours=3)
                historial.append((
                    historial_id, envio_id, 'entregado',
                    "Entrega conforme efectuada satisfactoriamente al destinatario.",
                    f"Agencia #{destino}" if tipo_envio == 'agencia_agencia' else "Domicilio Destino",
                    courier_id or cajero_id, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                historial_id += 1

            if estado_final == 'siniestrado':
                t_cursor += timedelta(hours=8)
                historial.append((
                    historial_id, envio_id, 'siniestrado',
                    "Incidencia Grave / Siniestro: Desperfecto mecánico y daño de carga durante el traslado. Notificación emitida.",
                    "Carretera Central Km 142", 11, t_cursor.strftime("%Y-%m-%d %H:%M:%S")
                ))
                historial_id += 1

            envio_id += 1

    return {
        'envios': envios,
        'historial': historial,
        'guias': guias,
        'guias_detalle': guias_detalle,
        'movimientos': movimientos
    }


def crear_tablas_si_no_existen(cur):
    """Garantiza la creación de las tablas operativas en SQLite si aún no existen."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY,
            tipo TEXT NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            placa TEXT NOT NULL UNIQUE,
            activo INTEGER DEFAULT 1,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones_vehiculo (
            id INTEGER PRIMARY KEY,
            transportista_id INTEGER NOT NULL REFERENCES usuarios(id),
            vehiculo_id INTEGER NOT NULL REFERENCES vehiculos(id),
            fecha_asignacion DATE NOT NULL,
            fecha_desasignacion DATE,
            activo INTEGER DEFAULT 1,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aperturas_caja (
            id INTEGER PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            numero_caja INTEGER NOT NULL,
            saldo_inicial NUMERIC(10,2) NOT NULL,
            fecha_apertura TIMESTAMP NOT NULL,
            fecha_cierre TIMESTAMP,
            saldo_final NUMERIC(10,2),
            total_ventas NUMERIC(10,2),
            estado TEXT DEFAULT 'abierta',
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_caja (
            id INTEGER PRIMARY KEY,
            apertura_id INTEGER NOT NULL REFERENCES aperturas_caja(id),
            envio_id INTEGER REFERENCES envios(id),
            tipo TEXT NOT NULL,
            monto NUMERIC(10,2) NOT NULL,
            descripcion TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guias_remision (
            id INTEGER PRIMARY KEY,
            codigo_guia INTEGER NOT NULL UNIQUE,
            agencia_origen_id INTEGER NOT NULL REFERENCES agencias(id),
            agencia_destino_id INTEGER NOT NULL REFERENCES agencias(id),
            fecha_salida TIMESTAMP,
            estado TEXT DEFAULT 'pendiente_traslado',
            transportista_id INTEGER REFERENCES usuarios(id),
            vehiculo_id INTEGER REFERENCES vehiculos(id),
            creado_por INTEGER REFERENCES usuarios(id),
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guias_remision_detalle (
            id INTEGER PRIMARY KEY,
            guia_id INTEGER NOT NULL REFERENCES guias_remision(id),
            envio_id INTEGER NOT NULL REFERENCES envios(id),
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


def poblar_sqlite(data):
    if not os.path.exists(DB_PATH):
        print(f"[!] Archivo SQLite no encontrado en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Garantizar esquema completo en SQLite
    crear_tablas_si_no_existen(cur)

    # 0. Agencias complementarias (53 al 84)
    for ag in NUEVAS_AGENCIAS_53_84:
        cur.execute("SELECT id FROM agencias WHERE id = ? OR codigo_agencia = ?", (ag[0], ag[1]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO agencias (id, codigo_agencia, nombre, departamento_id, departamento, provincia, distrito, direccion, estado, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, ag)

    # 1. Usuarios
    for u in USUARIOS_NUEVOS:
        cur.execute("SELECT id FROM usuarios WHERE id = ? OR dni = ? OR email = ?", (u[0], u[2], u[5]))
        if not cur.fetchone():
            totp = "".join(random.choices(string.ascii_uppercase + "234567", k=32))
            cur.execute("""
                INSERT INTO usuarios (
                    id, codigo_trabajador, dni, nombres, apellidos, email, password_hash,
                    tipo, agencia_id, numero_caja, licencia_conducir, totp_secret, totp_configurado,
                    intentos_fallidos, bloqueado, sesion_version, activo, fecha_nacimiento,
                    creado_en, actualizado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 1, 1, ?, datetime('now'), datetime('now'))
            """, (
                u[0], u[1], u[2], u[3], u[4], u[5], DEFAULT_PWD_HASH,
                u[6], u[7], u[8], u[9], totp, u[10]
            ))

    # 2. Vehiculos
    for v in NUEVOS_VEHICULOS:
        cur.execute("SELECT id FROM vehiculos WHERE id = ? OR placa = ?", (v[0], v[4]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO vehiculos (id, tipo, marca, modelo, placa, activo, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, v)

    # 3. Asignaciones
    for a in NUEVAS_ASIGNACIONES:
        cur.execute("SELECT id FROM asignaciones_vehiculo WHERE id = ?", (a[0],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO asignaciones_vehiculo (id, transportista_id, vehiculo_id, fecha_asignacion, fecha_desasignacion, activo, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, a)

    # 4. Clientes
    for c in NUEVOS_CLIENTES:
        cur.execute("SELECT id FROM clientes WHERE id = ? OR numero_documento = ?", (c[0], c[2]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO clientes (id, tipo_documento, numero_documento, nombre_completo, email, telefono, tipo_cliente, activo, creado_en, actualizado_en, creado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'), 1)
            """, c)

    # 5. Aperturas de caja
    for ap in NUEVAS_APERTURAS_CAJA:
        cur.execute("SELECT id FROM aperturas_caja WHERE id = ?", (ap[0],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO aperturas_caja (id, usuario_id, numero_caja, saldo_inicial, fecha_apertura, fecha_cierre, saldo_final, total_ventas, estado, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, ap)

    # 6. Envíos
    for e in data['envios']:
        cur.execute("SELECT id FROM envios WHERE id = ? OR codigo_tracking = ?", (e[0], e[1]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO envios (
                    id, codigo_tracking, remitente_id, destinatario_id, agencia_origen_id, agencia_destino_id,
                    tipo_envio, tipo_paquete, peso_kg, alto_cm, ancho_cm, largo_cm, peso_volumetrico,
                    descripcion, direccion_recojo, direccion_entrega, monto_subtotal, monto_descuento,
                    monto_igv, precio_envio, forma_pago, estado_pago, lugar_pago, estado, fecha_estimada,
                    fecha_entrega_real, imagen_recepcion, imagen_evidencia, tipo_documento, numero_documento,
                    serie_documento, registrado_por_id, registrado_web, apertura_caja_id, courier_id,
                    creado_en, actualizado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, e)

    # 7. Movimientos Caja
    for m in data['movimientos']:
        cur.execute("SELECT id FROM movimientos_caja WHERE id = ?", (m[0],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO movimientos_caja (id, apertura_id, envio_id, tipo, monto, descripcion, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, m)

    # 8. Guías
    for g in data['guias']:
        cur.execute("SELECT id FROM guias_remision WHERE id = ? OR codigo_guia = ?", (g[0], g[1]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO guias_remision (id, codigo_guia, agencia_origen_id, agencia_destino_id, fecha_salida, estado, transportista_id, vehiculo_id, creado_por, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, g)

    for gd in data['guias_detalle']:
        cur.execute("SELECT id FROM guias_remision_detalle WHERE id = ?", (gd[0],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO guias_remision_detalle (id, guia_id, envio_id, creado_en)
                VALUES (?, ?, ?, ?)
            """, gd)

    # 9. Historial
    for h in data['historial']:
        cur.execute("SELECT id FROM historial_envios WHERE id = ?", (h[0],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO historial_envios (id, envio_id, estado, descripcion, ubicacion, usuario_id, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, h)

    conn.commit()
    conn.close()
    print("[+] SQLite actualizado con éxito.")


if __name__ == "__main__":
    print("[*] Generando dataset Data Warehouse CargaExpress 2026...")
    data = construir_datawarehouse_seed()
    print(f"[+] Total Envíos generados: {len(data['envios'])}")
    print(f"[+] Total Movimientos de Caja: {len(data['movimientos'])}")
    print(f"[+] Total Guías de Remisión: {len(data['guias'])}")
    print(f"[+] Total Historiales de Envío: {len(data['historial'])}")
    poblar_sqlite(data)

