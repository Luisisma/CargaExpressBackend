# -*- coding: utf-8 -*-
import os
import sys
import sqlite3

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")

def diagnosticar():
    if not os.path.exists(DB_PATH):
        print(f"[!] No existe {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Ver agencias
    cur.execute("SELECT count(*), min(id), max(id) FROM agencias")
    total_ag, min_id, max_id = cur.fetchone()
    print(f"Total Agencias: {total_ag} (IDs desde {min_id} hasta {max_id})")

    # Muestra de agencias
    cur.execute("SELECT id, codigo_agencia, nombre, departamento, estado FROM agencias LIMIT 5")
    print("Primeras 5 agencias:", cur.fetchall())

    # 2. Ver usuarios 32 a 40
    print("\n--- Usuarios 32 a 40 ---")
    cur.execute("""
        SELECT u.id, u.nombres || ' ' || u.apellidos, u.tipo, u.agencia_id, a.nombre, u.licencia_conducir
        FROM usuarios u
        LEFT JOIN agencias a ON u.agencia_id = a.id
        WHERE u.id BETWEEN 32 AND 40
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"ID {r[0]}: {r[1]} | Tipo: {r[2]} | Agencia ID: {r[3]} | Agencia Nombre: {r[4]} | Licencia: {r[5]}")

    conn.close()

if __name__ == "__main__":
    diagnosticar()

