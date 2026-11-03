import os
import sys
import sqlite3
import random
import string
from datetime import datetime

# Añadir el backend al sys.path para reutilizar app.core.security
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from app.core.security import get_password_hash
    DEFAULT_PWD_HASH = get_password_hash("CargaExp#2026")
except Exception:
    import bcrypt
    DEFAULT_PWD_HASH = bcrypt.hashpw(b"CargaExp#2026", bcrypt.gensalt(12)).decode("utf-8")

DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")
SQL_FILE = os.path.abspath(os.path.join(BACKEND_DIR, "..", "cargaexpress.sql"))

# 1. Nuevas Agencias Complementarias (IDs 69 al 84)
NUEVAS_AGENCIAS_69_84 = [
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

# 2. 32 Nuevos Colaboradores Operativos con DNI comprobado y Roles Variados (Sin Admin)
# (id, cod_trab, dni, nombres, apellidos, email, tipo, agencia_id, num_caja, licencia, fecha_nac)
NUEVOS_USUARIOS = [
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

def random_totp():
    return "".join(random.choices(string.ascii_uppercase + "234567", k=32))

def poblar_sqlite():
    if not os.path.exists(DB_PATH):
        print(f"[!] No existe SQLite en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Insertar agencias extras
    ag_count = 0
    for ag in NUEVAS_AGENCIAS_69_84:
        cur.execute("SELECT id FROM agencias WHERE id = ? OR codigo_agencia = ?", (ag[0], ag[1]))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO agencias (id, codigo_agencia, nombre, departamento_id, departamento, provincia, distrito, direccion, estado, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, ag)
            ag_count += 1

    # Insertar usuarios
    usr_count = 0
    for u in NUEVOS_USUARIOS:
        cur.execute("SELECT id FROM usuarios WHERE id = ? OR dni = ? OR email = ?", (u[0], u[2], u[5]))
        if not cur.fetchone():
            totp = random_totp()
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
            usr_count += 1

    conn.commit()
    conn.close()
    print(f"[OK SQLite] {ag_count} nuevas agencias y {usr_count} nuevos colaboradores insertados en cargaexpress.db.")


def actualizar_sql_dump():
    if not os.path.exists(SQL_FILE):
        print(f"[!] No existe {SQL_FILE}")
        return

    with open(SQL_FILE, "r", encoding="utf-8") as f:
        contenido = f.read()

    # 1. Agregar agencias 69-84 si no existen
    if "AGENCIA UCAYALI - YARINACOCHA" not in contenido:
        lineas_ag = []
        for ag in NUEVAS_AGENCIAS_69_84:
            lineas_ag.append(f"({ag[0]}, {ag[1]}, '{ag[2]}', {ag[3]}, '{ag[4]}', '{ag[5]}', '{ag[6]}', '{ag[7]}', '{ag[8]}', '2026-07-14 15:55:56', '2026-07-14 15:55:56')")
        
        bloque_ag = ",\n" + ",\n".join(lineas_ag) + ";\n\nSELECT pg_catalog.setval('public.agencias_id_seq', 84, true);"
        contenido = contenido.replace(
            ";\n\nSELECT pg_catalog.setval('public.agencias_id_seq', 68, true);",
            bloque_ag
        )
        print("[OK SQL] 16 agencias complementarias añadidas a cargaexpress.sql (total: 84).")

    # 2. Agregar los 32 usuarios si no existen
    if "juan.perez@cargaexpress.pe" not in contenido:
        lineas_usr = []
        for u in NUEVOS_USUARIOS:
            totp = random_totp()
            caja_val = str(u[8]) if u[8] is not None else "NULL"
            lic_val = f"'{u[9]}'" if u[9] is not None else "NULL"
            fnac_val = f"'{u[10]}'" if u[10] is not None else "NULL"
            
            lineas_usr.append(
                f"({u[0]}, {u[1]}, '{u[2]}', '{u[3]}', '{u[4]}', '{u[5]}', '{DEFAULT_PWD_HASH}', "
                f"'{u[6]}', {u[7]}, {caja_val}, {lic_val}, '{totp}', false, 0, false, 1, true, "
                f"'2026-07-15 08:00:00', '2026-07-15 08:00:00', {fnac_val})"
            )
        
        bloque_usr = ",\n" + ",\n".join(lineas_usr) + ";\n\nSELECT pg_catalog.setval('public.usuarios_id_seq', 40, true);"
        contenido = contenido.replace(
            ";\n\nSELECT pg_catalog.setval('public.usuarios_id_seq', 8, true);",
            bloque_usr
        )
        print("[OK SQL] 32 colaboradores operativos añadidos a cargaexpress.sql (total: 40).")

    with open(SQL_FILE, "w", encoding="utf-8") as f:
        f.write(contenido)


if __name__ == "__main__":
    print(f"--> Hash Bcrypt generado para contraseña 'CargaExp#2026': {DEFAULT_PWD_HASH[:25]}...")
    poblar_sqlite()
    actualizar_sql_dump()
    print("\n[RESUMEN OPERATIVO]")
    print(f"- Total Agencias registradas: 84")
    print(f"- Total Usuarios registrados: 40 (32 nuevos: Cajeros, Supervisores, Almaceneros, Couriers, Transportistas)")
    print(f"- Credenciales por defecto: Correo institucional @cargaexpress.pe / Clave: CargaExp#2026")

