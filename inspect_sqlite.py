import sqlite3
import os

db_path = r"c:\Users\User\Documents\VSC-Integrador\cargaexpress-\instance\dev.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print("Tablas en dev.db:", tables)
    if "usuarios" in tables:
        cur.execute("SELECT id, dni, email, tipo FROM usuarios LIMIT 10;")
        users = cur.fetchall()
        print("\nUsuarios en dev.db:")
        for u in users:
            print(u)
    conn.close()
else:
    print("No se encontró dev.db en:", db_path)
