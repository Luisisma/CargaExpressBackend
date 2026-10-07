import sys
import psycopg

# Lista de combinaciones comunes a probar para PostgreSQL local
CANDIDATOS = [
    ("postgres", "change-me", "postgres con change-me"),
    ("cargaexpress_app", "change-me", "cargaexpress_app con change-me"),
    ("postgres", "", "Sin contraseña"),
    ("postgres", "postgres", "postgres"),
    ("postgres", "123456", "123456"),
    ("postgres", "1234", "1234"),
    ("postgres", "admin", "admin"),
    ("postgres", "root", "root"),
    ("postgres", "password", "password"),
]

print("=" * 60)
print("COMPROBACIÓN DE CONEXIÓN A POSTGRESQL (127.0.0.1:5432)")
print("=" * 60)

conexion_exitosa = None
password_funcional = None

# 1. Probar conectarse a la base de datos de mantenimiento 'postgres' o 'cargaexpress_dev'
for user, pwd, desc in CANDIDATOS:
    # Probar con base de datos 'postgres' o por defecto
    for db_test in ["postgres", "cargaexpress_dev", "cargaexpress"]:
        conninfo = f"host=127.0.0.1 port=5432 user={user} password='{pwd}' dbname={db_test} connect_timeout=3"
        try:
            with psycopg.connect(conninfo) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    v = cur.fetchone()[0]
                    print(f"[OK] ¡Autenticación EXITOSA con '{desc}' en base '{db_test}'!")
                    conexion_exitosa = True
                    password_funcional = pwd
                    usuario_funcional = user
                    bdd_funcional = db_test
                    break
        except psycopg.OperationalError as e:
            err = str(e).strip()
            if "database" in err and "does not exist" in err:
                continue
            elif "password authentication failed" in err:
                print(f"[-] '{desc}' en '{db_test}': Contraseña rechazada.")
                break
            else:
                continue
        if conexion_exitosa:
            break
    if conexion_exitosa:
        break

if not conexion_exitosa:
    print("\n[!] No se pudo autenticar con ninguna de las contraseñas comunes.")
    print("Por favor, revisa en DBeaver qué contraseña utilizas para tu conexión.")
    sys.exit(1)

# 2. Verificar si la base de datos 'cargaexpress' existe
print("\n" + "=" * 60)
print("VERIFICANDO SI EXISTE LA BASE DE DATOS 'cargaexpress'...")
print("=" * 60)

conninfo_admin = f"host=127.0.0.1 port=5432 user={usuario_funcional} password='{password_funcional}' dbname=postgres"
existe_bdd = False
try:
    with psycopg.connect(conninfo_admin) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT datname FROM pg_database WHERE datname = 'cargaexpress';")
            res = cur.fetchone()
            if res:
                existe_bdd = True
                print("[OK] La base de datos 'cargaexpress' existe en PostgreSQL.")
            else:
                print("[ALERTA] La base de datos 'cargaexpress' NO existe todavía.")
                print("   -> Creando base de datos 'cargaexpress' automáticamente...")
                conn.autocommit = True
                cur.execute("CREATE DATABASE cargaexpress;")
                print("   [OK] Base de datos 'cargaexpress' creada con éxito.")
                existe_bdd = True
except Exception as e:
    print(f"Nota: {e}")

# 3. Verificar tablas dentro de 'cargaexpress'
conninfo_app = f"host=127.0.0.1 port=5432 user={usuario_funcional} password='{password_funcional}' dbname=cargaexpress"
try:
    with psycopg.connect(conninfo_app) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tablas = [row[0] for row in cur.fetchall()]
            print(f"\nTablas encontradas en 'cargaexpress': {len(tablas)}")
            if "usuarios" in tablas:
                cur.execute("SELECT count(*) FROM usuarios;")
                cant_usuarios = cur.fetchone()[0]
                print(f"[OK] Tabla 'usuarios' encontrada con {cant_usuarios} registros.")
            else:
                print("[!] Aún no se han ejecutado los scripts de tablas.")
                print("   Debes ejecutar 'cargaexpress_clean.sql' sobre la base de datos 'cargaexpress'.")
except Exception as e:
    print(f"Error al inspeccionar 'cargaexpress': {e}")

print("\n" + "=" * 60)
print(f"VALOR RECOMENDADO PARA TU .env (DATABASE_URL):")
if password_funcional:
    print(f"DATABASE_URL=postgresql+psycopg://{usuario_funcional}:{password_funcional}@127.0.0.1:5432/cargaexpress")
else:
    print(f"DATABASE_URL=postgresql+psycopg://{usuario_funcional}@127.0.0.1:5432/cargaexpress")
print("=" * 60)
sys.exit(0)
