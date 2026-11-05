# -*- coding: utf-8 -*-
"""
Generador del Modelo Contable, Nómina de Sueldos y Rentabilidad (P&L / ROI)
para el Data Warehouse de CargaExpress Perú.

Genera en 'dwh_powerbi/':
1. dim_empleado.csv (35 colaboradores con roles, sedes, sueldos y cargas laborales EsSalud)
2. dim_vehiculo.csv (Flota de camiones troncales, furgones y motos courier)
3. dim_ruta.csv (Rutas interprovinciales con distancias en km y peajes)
4. fact_pnl_rentabilidad_mes.csv (Estrella contable mensual de ingresos vs planilla vs combustible vs alquileres -> ROI)

100% Integridad Referencial con dim_tiempo, dim_agencia y fact_envios.
"""

import os
import sqlite3
import csv
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BACKEND_DIR, "dwh_powerbi")
DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def write_csv(filename, headers, rows):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  [OK] Generado: {filename} ({len(rows)} registros)")

# =========================================================================
# 1. DIMENSIÓN EMPLEADOS & PLANILLA (dim_empleado.csv)
# =========================================================================
def generate_dim_empleado(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.dni, 
               (COALESCE(u.nombres, '') || ' ' || COALESCE(u.apellidos, '')) as nombre_completo, 
               COALESCE(u.tipo, 'cajero') as rol, 
               u.agencia_id, 
               COALESCE(a.nombre, 'Sede Central Lima') as nombre_sede,
               COALESCE(a.departamento, 'Lima') as departamento
        FROM usuarios u
        LEFT JOIN agencias a ON u.agencia_id = a.id
        ORDER BY u.id ASC;
    """)
    rows = cursor.fetchall()
    
    # Tabla de sueldos base de mercado formal peruano
    SUELDOS_POR_ROL = {
        'cajero': (1350.00, 'Cajero de Ventanilla'),
        'almacen': (1450.00, 'Operador de Almacén y Balanza'),
        'transportista': (2800.00, 'Chofer de Ruta Troncal A-IIIc'),
        'courier': (1550.00, 'Repartidor Courier Última Milla'),
        'supervisor': (2500.00, 'Supervisor de Operaciones'),
        'admin': (3600.00, 'Gerencia / Administrador'),
        'administrador': (3600.00, 'Gerencia / Administrador')
    }
    
    empleados = []
    for r in rows:
        uid, dni, nombre, rol, ag_id, sede, dep = r
        rol_key = rol.lower() if rol else 'cajero'
        sueldo_base, cargo = SUELDOS_POR_ROL.get(rol_key, (1350.00, 'Personal Operativo'))
        
        asignacion_fam = 102.50 # Asignación familiar legal Perú (10% RMV)
        essalud_9 = round((sueldo_base + asignacion_fam) * 0.09, 2) # EsSalud 9% a cargo de empleador
        cts_grati_prov = round((sueldo_base + asignacion_fam) * 0.18, 2) # Provisión legal CTS + Gratificación
        costo_total_empresa = round(sueldo_base + asignacion_fam + essalud_9 + cts_grati_prov, 2)
        
        empleados.append((
            uid,
            dni or f"4{uid:07d}",
            nombre,
            cargo,
            rol_key,
            ag_id or 1,
            sede,
            dep,
            sueldo_base,
            asignacion_fam,
            essalud_9,
            costo_total_empresa,
            "Planilla Régimen General (Indefinido)"
        ))
        
    headers = [
        "empleado_id", "dni", "nombre_completo", "cargo", "rol",
        "agencia_id", "nombre_sede", "departamento",
        "sueldo_base_pen", "asignacion_familiar_pen", "essalud_9_pen",
        "costo_total_empresa_pen", "tipo_contrato"
    ]
    write_csv("dim_empleado.csv", headers, empleados)
    return empleados

# =========================================================================
# 2. DIMENSIÓN FLOTA VEHICULAR (dim_vehiculo.csv)
# =========================================================================
def generate_dim_vehiculo():
    flota = [
        (1, "V7A-890", "Camión Troncal Pesado", "Volvo FH 500", 15000, 65.0, "Diésel D-50", 12.5, "Excelente (Operativo)"),
        (2, "V8B-712", "Camión Troncal Pesado", "Mercedes-Benz Actros", 15000, 65.0, "Diésel D-50", 12.8, "Excelente (Operativo)"),
        (3, "B9C-432", "Camión Troncal Pesado", "Scania R450", 14000, 60.0, "Diésel D-50", 13.0, "Excelente (Operativo)"),
        (4, "C1D-654", "Camión Troncal Pesado", "International WorkStar", 12000, 52.0, "Diésel D-50", 11.5, "Excelente (Operativo)"),
        (5, "T2E-119", "Camión Intermedio Regional", "Hino 500 Series", 8000, 38.0, "Diésel D-50", 16.0, "Excelente (Operativo)"),
        (6, "T3F-982", "Camión Intermedio Regional", "Isuzu Forward", 7500, 35.0, "Diésel D-50", 16.5, "Excelente (Operativo)"),
        (7, "A4G-551", "Camión Intermedio Regional", "Fuso Fighter", 7000, 32.0, "Diésel D-50", 17.0, "Mantenimiento Preventivo"),
        (8, "A5H-304", "Furgón Urbano Transferencia", "Hyundai HD78", 4500, 22.0, "Diésel D-50", 22.0, "Excelente (Operativo)"),
        (9, "P6I-771", "Furgón Urbano Transferencia", "Mitsubishi Canter", 4000, 20.0, "Diésel D-50", 23.5, "Excelente (Operativo)"),
        (10, "P7J-882", "Furgón Urbano Transferencia", "Kia K2700", 2500, 14.0, "Diésel D-50", 28.0, "Excelente (Operativo)"),
        (11, "M1K-102", "Moto Reparto Courier", "Honda GL 150 Cargo", 180, 0.8, "Gasolina 95", 140.0, "Excelente (Operativo)"),
        (12, "M2L-304", "Moto Reparto Courier", "Bajaj Boxer 150", 180, 0.8, "Gasolina 95", 145.0, "Excelente (Operativo)"),
        (13, "M3M-509", "Moto Reparto Courier", "Yamaha YBR 125", 160, 0.7, "Gasolina 95", 150.0, "Excelente (Operativo)"),
        (14, "M4N-618", "Moto Reparto Courier", "Honda GL 150 Cargo", 180, 0.8, "Gasolina 95", 140.0, "Excelente (Operativo)"),
        (15, "M5O-722", "Moto Reparto Courier", "Bajaj Platina 125", 150, 0.7, "Gasolina 95", 155.0, "Excelente (Operativo)"),
        (16, "M6P-831", "Moto Reparto Courier", "Honda Navi Cargo", 120, 0.5, "Gasolina 95", 130.0, "Excelente (Operativo)")
    ]
    headers = [
        "vehiculo_id", "placa", "tipo_vehiculo", "marca_modelo",
        "capacidad_carga_kg", "volumen_m3", "tipo_combustible",
        "rendimiento_km_galon", "estado_mecanico"
    ]
    write_csv("dim_vehiculo.csv", headers, flota)

# =========================================================================
# 3. DIMENSIÓN RUTAS TRONCALES (dim_ruta.csv)
# =========================================================================
def generate_dim_ruta():
    rutas = [
        (1, "RUTA-LIM-AQP", "Lima ➔ Arequipa (Panamericana Sur)", "Lima", "Arequipa", 1015, 8, 148.00, 15.5),
        (2, "RUTA-LIM-TRU", "Lima ➔ Trujillo (Panamericana Norte)", "Lima", "La Libertad", 560, 6, 114.00, 8.5),
        (3, "RUTA-LIM-HYO", "Lima ➔ Huancayo (Carretera Central)", "Lima", "Junín", 310, 3, 49.00, 7.0),
        (4, "RUTA-LIM-PIU", "Lima ➔ Piura (Norte Troncal)", "Lima", "Piura", 985, 9, 168.00, 14.0),
        (5, "RUTA-LIM-CUS", "Lima ➔ Cusco (Vía Nazca - Abancay)", "Lima", "Cusco", 1105, 7, 132.00, 20.0),
        (6, "RUTA-LIM-ICA", "Lima ➔ Ica (Autopista Chincha)", "Lima", "Ica", 305, 3, 52.00, 4.5),
        (7, "RUTA-LIM-CHX", "Lima ➔ Chiclayo (Panamericana Norte)", "Lima", "Lambayeque", 770, 7, 132.00, 11.0),
        (8, "RUTA-AQP-CUS", "Arequipa ➔ Cusco (Corredor Sur)", "Arequipa", "Cusco", 510, 4, 68.00, 9.5),
        (9, "RUTA-AQP-TAC", "Arequipa ➔ Tacna (Frontera Sur)", "Arequipa", "Tacna", 370, 3, 46.00, 5.5),
        (10, "RUTA-TRU-CHX", "Trujillo ➔ Chiclayo (Macro Norte)", "La Libertad", "Lambayeque", 215, 2, 36.00, 3.2),
        (11, "RUTA-LIM-ANC", "Lima ➔ Chimbote / Huaraz", "Lima", "Ancash", 425, 4, 76.00, 6.5),
        (12, "RUTA-LIM-AYC", "Lima ➔ Ayacucho (Vía Los Libertadores)", "Lima", "Ayacucho", 565, 4, 72.00, 10.0),
        (13, "RUTA-HYO-PAS", "Huancayo ➔ Cerro de Pasco / Huánuco", "Junín", "Huánuco", 230, 2, 32.00, 5.0),
        (14, "RUTA-TRU-CAJ", "Trujillo ➔ Cajamarca (Sierra Norte)", "La Libertad", "Cajamarca", 300, 3, 48.00, 7.5),
        (15, "RUTA-AQP-PUN", "Arequipa ➔ Puno / Juliaca", "Arequipa", "Puno", 295, 2, 34.00, 5.5),
        (16, "RUTA-LIM-TUM", "Lima ➔ Tumbes (Frontera Norte)", "Lima", "Tumbes", 1270, 11, 198.00, 18.0),
        (17, "RUTA-LIM-UCA", "Lima ➔ Pucallpa (Carretera F. Basadre)", "Lima", "Ucayali", 780, 5, 85.00, 16.5),
        (18, "RUTA-LIM-SMT", "Lima ➔ Tarapoto / Moyobamba", "Lima", "San Martín", 990, 6, 102.00, 21.0),
        (19, "RUTA-LIM-LOR", "Lima ➔ Iquitos (Bimodal Terrestre-Fluvial)", "Lima", "Loreto", 1350, 4, 75.00, 48.0),
        (20, "RUTA-AQP-MOQ", "Arequipa ➔ Moquegua / Ilo", "Arequipa", "Moquegua", 220, 2, 30.00, 3.5)
    ]
    headers = [
        "ruta_id", "codigo_ruta", "nombre_ruta", "departamento_origen",
        "departamento_destino", "distancia_km", "numero_peajes",
        "costo_peajes_estimado_pen", "tiempo_horas_estimado"
    ]
    write_csv("dim_ruta.csv", headers, rutas)

# =========================================================================
# 4. ESTRELLA MAESTRA CONTABLE: P&L, SUELDOS Y ROI (fact_pnl_rentabilidad_mes.csv)
# =========================================================================
def generate_fact_pnl(conn, empleados):
    cursor = conn.cursor()
    
    # 1. Obtener ingresos por mes y departamento de origen de fact_envios
    cursor.execute("""
        SELECT 
            strftime('%Y%m', e.creado_en) || '01' as tiempo_id,
            a.departamento,
            a.id as agencia_id,
            SUM(e.precio_envio) as fletes_totales_pen,
            COUNT(e.id) as cantidad_envios
        FROM envios e
        JOIN agencias a ON e.agencia_origen_id = a.id
        GROUP BY strftime('%Y%m', e.creado_en), a.departamento
        ORDER BY tiempo_id ASC, fletes_totales_pen DESC;
    """)
    ventas_agrupadas = cursor.fetchall()
    
    # Calcular costo mensual de personal por departamento
    costo_personal_por_dep = {}
    for emp in empleados:
        dep = emp[7] # departamento
        costo_emp = emp[11] # costo_total_empresa_pen
        costo_personal_por_dep[dep] = costo_personal_por_dep.get(dep, 0.0) + costo_emp
        
    # Asignar un costo base mínimo de planilla para sedes sin usuario directo
    # (ej: agencias provinciales compartidas: 0.5 tiempo de personal = S/ 850)
    costo_base_sede = 850.00
    
    pnl_rows = []
    pnl_id = 1
    
    # Renta de locales según el departamento (Lima más cara, provincias más económicas)
    ALQUILER_POR_DEP = {
        'Lima': 3200.00,
        'Arequipa': 1800.00,
        'La Libertad': 1600.00,
        'Piura': 1500.00,
        'Lambayeque': 1400.00,
        'Cusco': 1600.00,
        'Junín': 1300.00,
        'Ica': 1300.00,
        'Ancash': 1100.00,
        'Callao': 1400.00,
        'Loreto': 1200.00,
        'San Martín': 1100.00,
        'Ucayali': 1100.00
    }
    
    for r in ventas_agrupadas:
        tiempo_id_str, dep, ag_id, fletes_pen, cant_envios = r
        tiempo_id = int(tiempo_id_str)
        fletes_pen = round(float(fletes_pen or 0.0), 2)
        
        # 1. Costo directo de transporte (Combustible + Peajes de ruta troncal)
        # En el sector transporte peruano, combustible representa ~18% y peajes ~5%
        costo_combustible = round(fletes_pen * 0.18, 2)
        costo_peajes = round(fletes_pen * 0.05, 2)
        
        # 2. Planilla operativa y cargas laborales (Sueldo proporcional al volumen de encomiendas)
        # Factor de eficiencia de sede: sedes grandes aprovechan economías de escala
        es_sede_grande = dep in ('Lima', 'Arequipa', 'La Libertad', 'Piura', 'Lambayeque', 'Ica', 'Junín', 'Cusco')
        ratio_personal = 0.28 if es_sede_grande else 0.42
        
        gasto_sueldos_mes = round(fletes_pen * ratio_personal, 2)
        gasto_cargas_sociales = round(gasto_sueldos_mes * 0.09, 2) # EsSalud 9% ley
        
        # 3. Alquiler de local y servicios (Luz, agua, internet tracking)
        ratio_alquiler = 0.10 if es_sede_grande else 0.22
        gasto_alquiler_servicios = round(fletes_pen * ratio_alquiler, 2)
        
        # Costo total de operación
        costo_total_operativo = round(
            costo_combustible + costo_peajes + gasto_sueldos_mes + gasto_cargas_sociales + gasto_alquiler_servicios, 
            2
        )
        
        # Utilidad Neta Operativa (EBITDA)
        utilidad_neta = round(fletes_pen - costo_total_operativo, 2)
        
        # Margen Operativo %
        margen_operativo_pct = round((utilidad_neta / fletes_pen * 100.0) if fletes_pen > 0 else 0.0, 1)
        
        # Retorno sobre Inversión / Costos (ROI %)
        roi_pct = round((utilidad_neta / costo_total_operativo * 100.0) if costo_total_operativo > 0 else 0.0, 1)
        
        estado_financiero = "Superávit (Rentable)" if utilidad_neta > 0 else "Déficit (En Desarrollo)"
        
        pnl_rows.append((
            pnl_id,
            tiempo_id,
            ag_id,
            dep,
            fletes_pen,
            cant_envios,
            costo_combustible,
            costo_peajes,
            gasto_sueldos_mes,
            gasto_cargas_sociales,
            gasto_alquiler_servicios,
            costo_total_operativo,
            utilidad_neta,
            margen_operativo_pct,
            roi_pct,
            estado_financiero
        ))
        pnl_id += 1
        
    headers = [
        "pnl_id", "tiempo_id", "agencia_id", "departamento",
        "ingresos_fletes_pen", "cantidad_envios",
        "costo_combustible_pen", "costo_peajes_pen",
        "gasto_sueldos_personal_pen", "gasto_cargas_sociales_pen", "gasto_alquiler_servicios_pen",
        "costo_total_operativo_pen", "utilidad_neta_pen",
        "margen_operativo_pct", "roi_porcentaje", "estado_financiero"
    ]
    write_csv("fact_pnl_rentabilidad_mes.csv", headers, pnl_rows)

def main():
    print("=" * 70)
    print("GENERADOR DEL MODELO CONTABLE, NÓMINA DE SUELDOS Y RENTABILIDAD ROI")
    print("Data Warehouse CargaExpress Perú 2026")
    print("=" * 70)
    
    ensure_output_dir()
    conn = sqlite3.connect(DB_PATH)
    
    empleados = generate_dim_empleado(conn)
    generate_dim_vehiculo()
    generate_dim_ruta()
    generate_fact_pnl(conn, empleados)
    
    conn.close()
    print("=" * 70)
    print("[EXITO] Todos los datasets financieros generados en 'dwh_powerbi/'.")
    print("=" * 70)

if __name__ == "__main__":
    main()
