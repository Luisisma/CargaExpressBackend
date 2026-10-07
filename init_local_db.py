import os
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.agencia import Agencia
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.envio import Envio, HistorialEnvio
from app.models.auditoria import AuditoriaSeguridad, AuditoriaOperaciones

DB_FILE = os.path.join(os.path.dirname(__file__), "cargaexpress.db")
SQLITE_URL = f"sqlite:///{DB_FILE}"

print(f"Inicializando Base de Datos SQLite: {DB_FILE}")

engine = create_engine(SQLITE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 1. Crear todas las tablas del modelo normalizado 3NF
Base.metadata.create_all(bind=engine)
print("[OK] Tablas creadas con éxito.")

db = SessionLocal()

try:
    # 2. Insertar agencias principales si no existen
    if db.query(Agencia).count() == 0:
        agencias = [
            Agencia(
                id=1,
                codigo_agencia=1001,
                nombre="AGENCIA LIMA - LIMA CENTRAL",
                departamento="Lima",
                provincia="Lima",
                distrito="Lima",
                direccion="Av. Nicolás de Piérola 1220, Lima",
                estado="habilitado"
            ),
            Agencia(
                id=2,
                codigo_agencia=1002,
                nombre="AGENCIA AREQUIPA - AREQUIPA",
                departamento="Arequipa",
                provincia="Arequipa",
                distrito="Arequipa",
                direccion="Calle Mercaderes 314, Arequipa",
                estado="habilitado"
            ),
            Agencia(
                id=10,
                codigo_agencia=1010,
                nombre="AGENCIA CUSCO - CUSCO",
                departamento="Cusco",
                provincia="Cusco",
                distrito="Cusco",
                direccion="Calle Matará 241, Cusco",
                estado="habilitado"
            )
        ]
        db.add_all(agencias)
        db.commit()
        print(f"[OK] {len(agencias)} Agencias semilla insertadas.")

    # 3. Insertar o actualizar usuarios semilla con hash Bcrypt garantizado de 'password123'
    from app.core.security import get_password_hash
    hash_password123 = get_password_hash("password123")

    u_admin = db.query(Usuario).filter(Usuario.dni == "79665184").first()
    if not u_admin:
        u_admin = Usuario(
            id=1,
            codigo_trabajador=1,
            dni="79665184",
            nombres="Administrador",
            apellidos="CargaExpress",
            email="admin@cargaexpress.local",
            password_hash=hash_password123,
            tipo="administrador",
            agencia_id=1,
            totp_secret="P7345HJPC3KW2LQTJWLT2FTBAF2STND2",
            totp_configurado=True,
            activo=True,
            sesion_version=1
        )
        db.add(u_admin)
    else:
        u_admin.password_hash = hash_password123
        u_admin.intentos_fallidos = 0
        u_admin.bloqueado = False

    u_cajero = db.query(Usuario).filter(Usuario.dni == "82922603").first()
    if not u_cajero:
        u_cajero = Usuario(
            id=2,
            codigo_trabajador=2,
            dni="82922603",
            nombres="Postman",
            apellidos="Demo Cajero",
            email="cajero@cargaexpress.pe",
            password_hash=hash_password123,
            tipo="cajero",
            agencia_id=1,
            numero_caja=1,
            totp_secret=None,
            totp_configurado=False,
            activo=True,
            sesion_version=1
        )
        db.add(u_cajero)
    else:
        u_cajero.password_hash = hash_password123
        u_cajero.intentos_fallidos = 0
        u_cajero.bloqueado = False

    db.commit()
    print("[OK] Contraseñas actualizadas con éxito a 'password123' con Bcrypt.")

    # 4. Insertar cliente y envío de prueba
    if db.query(Cliente).count() == 0:
        c1 = Cliente(
            id=1,
            tipo_documento="dni",
            numero_documento="45678912",
            nombre_completo="Juan Carlos Pérez Ramos",
            email="juan.perez@ejemplo.pe",
            telefono="987654321",
            tipo_cliente="persona_natural",
            activo=True
        )
        c2 = Cliente(
            id=2,
            tipo_documento="dni",
            numero_documento="78945612",
            nombre_completo="María Elena Gómez Flores",
            email="maria.gomez@ejemplo.pe",
            telefono="912345678",
            tipo_cliente="persona_natural",
            activo=True
        )
        db.add_all([c1, c2])
        db.commit()

        envio1 = Envio(
            id=1,
            codigo_tracking="CE-2026-00001",
            remitente_id=1,
            destinatario_id=2,
            agencia_origen_id=1,
            agencia_destino_id=2,
            tipo_envio="agencia_agencia",
            tipo_paquete="caja",
            peso_kg=Decimal("5.00"),
            peso_volumetrico=Decimal("2.00"),
            descripcion="Paquete de prueba para tracking",
            monto_subtotal=Decimal("17.37"),
            monto_descuento=Decimal("0.00"),
            monto_igv=Decimal("3.13"),
            precio_envio=Decimal("20.50"),
            forma_pago="efectivo",
            estado_pago="pagado",
            lugar_pago="origen",
            estado="en_transito",
            tipo_documento="boleta",
            registrado_web=False
        )
        db.add(envio1)
        db.commit()

        h1 = HistorialEnvio(
            envio_id=1,
            estado="REGISTRADO",
            descripcion="Envío recepcionado en agencia Lima.",
            ubicacion="AGENCIA LIMA - LIMA CENTRAL"
        )
        h2 = HistorialEnvio(
            envio_id=1,
            estado="EN_TRANSITO",
            descripcion="En viaje terrestre hacia Arequipa.",
            ubicacion="Ruta Panamericana Sur"
        )
        db.add_all([h1, h2])
        db.commit()
        print("[OK] Clientes y Envíos de prueba insertados con éxito.")

    print("\n" + "=" * 60)
    print("BASE DE DATOS LOCAL LISTA PARA FUNCIONAR")
    print(f"Ruta: {DB_FILE}")
    print("=" * 60)

finally:
    db.close()
