import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash as werkzeug_generate_hash

from main import app
from app.db.base import Base
from app.api.deps import get_db
from app.core.security import get_password_hash
from app.models.agencia import Agencia
from app.models.usuario import Usuario

# Base de datos SQLite en memoria para tests aislados
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine
)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_seed_data(db_session):
    """Inserta una agencia y tres usuarios de prueba para validar flujos 2FA y login directo."""
    agencia = Agencia(
        id=1,
        codigo_agencia=101,
        nombre="Sede Central Lima",
        departamento="LIMA",
        provincia="LIMA",
        distrito="MIRAFLORES",
        direccion="Av. Ricardo Palma 245",
        estado="ACTIVO"
    )
    db_session.add(agencia)

    # Usuario con 2FA configurado (Secret conocido en Base32)
    totp_secret_conocido = "JBSWY3DPEHPK3PXP"
    usuario_2fa = Usuario(
        id=1,
        codigo_trabajador=1001,
        dni="70809010",
        nombres="Carlos",
        apellidos="Administrador",
        email="admin@cargaexpress.pe",
        password_hash=get_password_hash("AdminPass123!"),
        tipo="administrador",
        agencia_id=1,
        totp_secret=totp_secret_conocido,
        totp_configurado=True,
        activo=True,
        sesion_version=1
    )
    db_session.add(usuario_2fa)

    # Usuario sin 2FA (login directo)
    usuario_directo = Usuario(
        id=2,
        codigo_trabajador=1002,
        dni="70809020",
        nombres="Maria",
        apellidos="Cajera",
        email="cajera@cargaexpress.pe",
        password_hash=get_password_hash("CajeroPass123!"),
        tipo="cajero",
        agencia_id=1,
        totp_secret=None,
        totp_configurado=False,
        activo=True,
        sesion_version=1
    )
    db_session.add(usuario_directo)

    # Usuario con hash heredado Werkzeug (compatibilidad cargaexpress.sql)
    usuario_legacy = Usuario(
        id=3,
        codigo_trabajador=1003,
        dni="70809030",
        nombres="Juan",
        apellidos="Legacy",
        email="legacy@cargaexpress.pe",
        password_hash=werkzeug_generate_hash("LegacyPass123!"),
        tipo="almacen",
        agencia_id=1,
        totp_secret=None,
        totp_configurado=False,
        activo=True,
        sesion_version=1
    )
    db_session.add(usuario_legacy)

    db_session.commit()

    return {
        "agencia": agencia,
        "usuario_2fa": usuario_2fa,
        "totp_secret": totp_secret_conocido,
        "usuario_directo": usuario_directo,
        "usuario_legacy": usuario_legacy
    }
