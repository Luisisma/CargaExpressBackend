"""
==============================================================================
CARGAEXPRESS PERÚ - UTILIDAD DE BACKUP Y RESTAURACIÓN DE BASE DE DATOS SQLITE
==============================================================================
Permite realizar respaldos completos (SQL dump y copia binaria .db) y restauraciones
en cualquier momento sin depender de herramientas externas.

USO RÁPIDO:
    py backup_db.py                 # Genera backup en SQL y binario con timestamp
    py backup_db.py --status        # Muestra el estado actual y conteo de registros
    py backup_db.py --restore [archivo.sql]  # Restaura la base de datos desde un archivo SQL
    py backup_db.py --restore-db [archivo.db] # Restaura desde un archivo binario .db
==============================================================================
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime

# Configurar salida segura en consolas de Windows (evita errores con cp1252)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "cargaexpress.db")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
DEFAULT_DUMP_FILE = os.path.join(BASE_DIR, "cargaexpress_backup.sql")


def obtener_conteo_tablas(db_path=DB_FILE):
    """Devuelve un diccionario con el conteo de filas por cada tabla."""
    if not os.path.exists(db_path):
        return {}
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]
    conteo = {}
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        conteo[table] = cur.fetchone()[0]
    conn.close()
    return conteo


def imprimir_resumen_tablas(conteo):
    """Imprime una tabla formateada en consola con el conteo de registros."""
    print("\n" + "=" * 55)
    print(" 📊 ESTADO ACTUAL DE REGISTROS EN CARGAEXPRESS DB")
    print("=" * 55)
    print(f"{'Tabla':<30} | {'N° Registros':>18}")
    print("-" * 55)
    total_registros = 0
    for tabla, total in sorted(conteo.items()):
        print(f"{tabla:<30} | {total:>18,}")
        total_registros += total
    print("-" * 55)
    print(f"{'TOTAL GENERAL':<30} | {total_registros:>18,}")
    print("=" * 55 + "\n")


def exportar_backup():
    """Genera dump SQL completo y copia física .db con fecha y hora."""
    if not os.path.exists(DB_FILE):
        print(f"❌ Error: No se encontró la base de datos en '{DB_FILE}'.")
        return False

    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Archivo SQL de respaldo rápido principal
    sql_dump_latest = DEFAULT_DUMP_FILE
    # 2. Archivo SQL timestamped en carpeta backups
    sql_dump_timestamped = os.path.join(BACKUPS_DIR, f"cargaexpress_backup_{timestamp}.sql")
    # 3. Copia binaria .db timestamped en carpeta backups
    db_backup_timestamped = os.path.join(BACKUPS_DIR, f"cargaexpress_backup_{timestamp}.db")

    print(f"🔄 Iniciando respaldo de '{os.path.basename(DB_FILE)}'...")

    # Generar SQL Dump mediante iterdump()
    conn = sqlite3.connect(DB_FILE)
    with open(sql_dump_timestamped, "w", encoding="utf-8") as f_ts:
        for linea in conn.iterdump():
            f_ts.write(f"{linea}\n")
    conn.close()

    # Copiar también al archivo estándar cargaexpress_backup.sql en la raíz
    shutil.copy2(sql_dump_timestamped, sql_dump_latest)

    # Copiar binario .db completo
    shutil.copy2(DB_FILE, db_backup_timestamped)

    conteo = obtener_conteo_tablas(DB_FILE)
    imprimir_resumen_tablas(conteo)

    size_sql_kb = os.path.getsize(sql_dump_latest) / 1024
    size_db_kb = os.path.getsize(db_backup_timestamped) / 1024

    print("✅ ¡RESPALDO COMPLETADO CON ÉXITO!")
    print(f"  📄 Dump SQL (raíz):       {sql_dump_latest} ({size_sql_kb:.1f} KB)")
    print(f"  📁 Dump SQL (historial):  {sql_dump_timestamped}")
    print(f"  💾 Binario .db (copia):   {db_backup_timestamped} ({size_db_kb:.1f} KB)")
    return True


def restaurar_desde_sql(ruta_sql):
    """Restaura la base de datos ejecutando el script SQL."""
    if not os.path.exists(ruta_sql):
        print(f"❌ Error: El archivo SQL '{ruta_sql}' no existe.")
        return False

    # Crear backup de seguridad del .db actual antes de sobrescribir
    if os.path.exists(DB_FILE):
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        respaldo_seguridad = os.path.join(
            BACKUPS_DIR, f"cargaexpress_antes_de_restaurar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        shutil.copy2(DB_FILE, respaldo_seguridad)
        print(f"🛡️  Copia de seguridad previa guardada en: {respaldo_seguridad}")
        try:
            os.remove(DB_FILE)
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo eliminar el archivo DB previo: {e}")

    print(f"🔄 Restaurando base de datos desde '{ruta_sql}'...")
    conn = sqlite3.connect(DB_FILE)
    with open(ruta_sql, "r", encoding="utf-8") as f:
        script_sql = f.read()

    conn.executescript(script_sql)
    conn.commit()
    conn.close()

    conteo = obtener_conteo_tablas(DB_FILE)
    imprimir_resumen_tablas(conteo)
    print("✅ ¡BASE DE DATOS RESTAURADA EXITOSAMENTE DESDE SQL!")
    return True


def restaurar_desde_db(ruta_db):
    """Restaura la base de datos copiando un archivo .db respaldado."""
    if not os.path.exists(ruta_db):
        print(f"❌ Error: El archivo DB '{ruta_db}' no existe.")
        return False

    if os.path.exists(DB_FILE):
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        respaldo_seguridad = os.path.join(
            BACKUPS_DIR, f"cargaexpress_antes_de_restaurar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        shutil.copy2(DB_FILE, respaldo_seguridad)
        print(f"🛡️  Copia de seguridad previa guardada en: {respaldo_seguridad}")

    shutil.copy2(ruta_db, DB_FILE)
    conteo = obtener_conteo_tablas(DB_FILE)
    imprimir_resumen_tablas(conteo)
    print("✅ ¡BASE DE DATOS RESTAURADA EXITOSAMENTE DESDE ARCHIVO BINARIO!")
    return True


def main():
    args = sys.argv[1:]

    if len(args) == 0:
        exportar_backup()
    elif args[0] in ("--status", "-s"):
        conteo = obtener_conteo_tablas(DB_FILE)
        imprimir_resumen_tablas(conteo)
    elif args[0] in ("--restore", "-r"):
        if len(args) < 2:
            # Restaurar por defecto desde cargaexpress_backup.sql
            restaurar_desde_sql(DEFAULT_DUMP_FILE)
        else:
            restaurar_desde_sql(args[1])
    elif args[0] in ("--restore-db", "-rdb"):
        if len(args) < 2:
            print("❌ Debe especificar la ruta del archivo .db a restaurar.")
            print("   Ejemplo: py backup_db.py --restore-db backups/cargaexpress_backup_20261013_203000.db")
        else:
            restaurar_desde_db(args[1])
    else:
        print("Uso:")
        print("  py backup_db.py                       # Exporta backup SQL y DB")
        print("  py backup_db.py --status              # Muestra estadísticas")
        print("  py backup_db.py --restore [ruta.sql]  # Restaura desde SQL")
        print("  py backup_db.py --restore-db [ruta.db]# Restaura desde .db")


if __name__ == "__main__":
    main()
