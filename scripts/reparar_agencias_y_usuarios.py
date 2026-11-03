# -*- coding: utf-8 -*-
"""
Script de reparación y sincronización completa para SQLite (cargaexpress.db):
1. Carga las 84 agencias nacionales del INEI Ubigeo garantizando su existencia con estado 'habilitado'.
2. Sincroniza y asigna las agencias correctas a cada uno de los 32 colaboradores operativos.
3. Normaliza las licencias de conducir MTC (A-IIIc para transportistas, B-IIb para couriers)
   para que el modal de edición del Frontend y la validación Pydantic del Backend funcionen al 100%.
"""

import os
import sys
import sqlite3
import re

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")
SQL_FILE = os.path.abspath(os.path.join(BACKEND_DIR, "..", "cargaexpress.sql"))

def reparar_todo():
    if not os.path.exists(DB_PATH):
        print(f"[!] No se encontró el archivo de base de datos en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("[*] 1. Extrayendo las 84 agencias de cargaexpress.sql...")
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Extraer el bloque INSERT INTO public.agencias
    match_agencias = re.search(r"INSERT INTO public\.agencias [^;]+;", sql_content, re.DOTALL)
    if not match_agencias:
        print("[!] No se encontró el bloque de agencias en cargaexpress.sql")
        conn.close()
        return

    bloque_agencias = match_agencias.group(0)
    # Extraer cada tupla (id, codigo_agencia, nombre, depto_id, depto, prov, dist, dir, estado, ...)
    patron_tupla = re.compile(
        r"\((\d+),\s*(\d+),\s*'([^']*)',\s*(\d+),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'",
        re.MULTILINE
    )

    agencias_insertadas = 0
    for match in patron_tupla.finditer(bloque_agencias):
        ag_id = int(match.group(1))
        cod_ag = int(match.group(2))
        nombre = match.group(3)
        depto_id = int(match.group(4))
        depto = match.group(5)
        prov = match.group(6)
        dist = match.group(7)
        direcc = match.group(8)
        estado = match.group(9)

        cur.execute("SELECT id FROM agencias WHERE id = ?", (ag_id,))
        existe = cur.fetchone()

        if not existe:
            cur.execute("""
                INSERT INTO agencias (
                    id, codigo_agencia, nombre, departamento_id, departamento,
                    provincia, distrito, direccion, estado, creado_en, actualizado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (ag_id, cod_ag, nombre, depto_id, depto, prov, dist, direcc, estado))
            agencias_insertadas += 1
        else:
            # Asegurar que esté habilitada y con nombre correcto
            cur.execute("""
                UPDATE agencias
                SET nombre = ?, departamento = ?, provincia = ?, distrito = ?, direccion = ?, estado = 'habilitado'
                WHERE id = ?
            """, (nombre, depto, prov, dist, direcc, ag_id))

    print(f"[+] Agencias sincronizadas. {agencias_insertadas} agencias nuevas insertadas en cargaexpress.db.")

    # 2. Sincronizar asignaciones de agencias y licencias para los 32 usuarios
    print("[*] 2. Sincronizando sedes operativas y licencias MTC de los colaboradores...")

    ASIGNACIONES_USUARIOS = [
        # (id, agencia_id, num_caja, licencia_mtc)
        (9, 1, 1, None),        # Lima - Javier Prado
        (10, 2, 1, None),       # Arequipa - P. Armas
        (11, 2, None, None),    # Arequipa - P. Armas (Supervisor)
        (12, 3, 1, None),       # Lima - Miraflores
        (13, 1, None, None),    # Lima - Javier Prado (Almacén)
        (14, 3, None, None),    # Lima - Miraflores (Supervisor)
        (15, 1, None, 'A-IIIc'),# Lima - Javier Prado (Transportista)
        (16, 4, 1, None),       # Cañete
        (17, 1, None, 'B-IIb'), # Lima - Javier Prado (Courier)
        (18, 2, None, None),    # Arequipa - P. Armas (Almacén)
        (19, 2, None, 'A-IIIc'),# Arequipa - P. Armas (Transportista)
        (20, 5, 1, None),       # Callao - Bellavista
        (21, 11, None, None),   # Cusco - Wanchaq (Almacén)
        (22, 11, None, None),   # Cusco - Wanchaq (Supervisor)
        (23, 2, None, 'B-IIb'), # Arequipa - P. Armas (Courier)
        (24, 19, 1, None),      # La Libertad - Trujillo
        (25, 19, None, None),   # La Libertad - Trujillo (Almacén)
        (26, 19, None, None),   # La Libertad - Trujillo (Supervisor)
        (27, 19, None, 'A-IIIc'),# La Libertad - Trujillo (Transportista)
        (28, 21, 1, None),      # Lambayeque - Chiclayo
        (29, 21, None, None),   # Lambayeque - Chiclayo (Almacén)
        (30, 19, None, 'B-IIb'),# La Libertad - Trujillo (Courier)
        (31, 21, None, 'A-IIIc'),# Lambayeque - Chiclayo (Transportista)
        (32, 23, 1, None),      # Piura - Piura
        (33, 23, None, None),   # Piura - Piura (Almacén)
        (34, 23, None, None),   # Piura - Piura (Supervisor)
        (35, 23, None, 'B-IIb'),# Piura - Piura (Courier)
        (36, 7, 1, None),       # Ica - Ica
        (37, 7, None, None),    # Ica - Ica (Almacén)
        (38, 7, None, None),    # Ica - Ica (Supervisor)
        (39, 7, None, 'A-IIIc'),# Ica - Ica (Transportista)
        (40, 7, None, 'B-IIb'), # Ica - Ica (Courier)
    ]

    usuarios_actualizados = 0
    for u_id, ag_id, num_caja, lic in ASIGNACIONES_USUARIOS:
        cur.execute("""
            UPDATE usuarios
            SET agencia_id = ?, numero_caja = ?, licencia_conducir = ?, activo = 1
            WHERE id = ?
        """, (ag_id, num_caja, lic, u_id))
        usuarios_actualizados += 1

    conn.commit()

    # 3. Verificación de integridad
    cur.execute("""
        SELECT u.id, u.nombres || ' ' || u.apellidos, u.tipo, a.nombre, u.licencia_conducir
        FROM usuarios u
        JOIN agencias a ON u.agencia_id = a.id
        WHERE u.id BETWEEN 32 AND 40
    """)
    print("\n--- Verificación de Personal (IDs 32 al 40) ---")
    for r in cur.fetchall():
        print(f"✓ #{r[0]}: {r[1]} [{r[2].upper()}] -> Sede: {r[3]} (Licencia: {r[4] or 'N/A'})")

    conn.close()
    print("\n[ÉXITO] Base de datos reparada y 100% sincronizada.")

if __name__ == "__main__":
    reparar_todo()

