import pytest
from decimal import Decimal
from app.models.agencia import Agencia
from app.models.cliente import Cliente
from app.models.envio import Envio, HistorialEnvio


@pytest.fixture
def publico_seed_data(db_session, test_seed_data):
    """Crea una segunda agencia y un envío de prueba para validar cotización y tracking."""
    agencia_arequipa = Agencia(
        id=2,
        codigo_agencia=102,
        nombre="Sede Arequipa Parque Industrial",
        departamento="AREQUIPA",
        provincia="AREQUIPA",
        distrito="CERRO COLORADO",
        direccion="Av. Industrial 500",
        estado="HABILITADO"
    )
    db_session.add(agencia_arequipa)

    cliente_rem = Cliente(
        id=1,
        tipo_documento="dni",
        numero_documento="45678912",
        nombre_completo="Juan Carlos Pérez Ramos",
        email="juan.perez@ejemplo.pe",
        telefono="987654321",
        tipo_cliente="persona_natural",
        activo=True
    )
    cliente_dest = Cliente(
        id=2,
        tipo_documento="dni",
        numero_documento="78945612",
        nombre_completo="María Elena Gómez Flores",
        email="maria.gomez@ejemplo.pe",
        telefono="912345678",
        tipo_cliente="persona_natural",
        activo=True
    )
    db_session.add_all([cliente_rem, cliente_dest])
    db_session.flush()

    envio_demo = Envio(
        id=1,
        codigo_tracking="CE-2026-00001",
        remitente_id=cliente_rem.id,
        destinatario_id=cliente_dest.id,
        agencia_origen_id=1,
        agencia_destino_id=agencia_arequipa.id,
        tipo_envio="agencia_agencia",
        tipo_paquete="caja",
        peso_kg=Decimal("5.00"),
        alto_cm=Decimal("20.00"),
        ancho_cm=Decimal("20.00"),
        largo_cm=Decimal("30.00"),
        peso_volumetrico=Decimal("2.00"),
        descripcion="Documentos y accesorios",
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
    db_session.add(envio_demo)
    db_session.flush()

    hito_1 = HistorialEnvio(
        envio_id=envio_demo.id,
        estado="registrado",
        descripcion="Paquete recibido en agencia origen.",
        ubicacion="Sede Central Lima"
    )
    hito_2 = HistorialEnvio(
        envio_id=envio_demo.id,
        estado="en_transito",
        descripcion="En viaje terrestre hacia Arequipa.",
        ubicacion="Ruta Panamericana Sur"
    )
    db_session.add_all([hito_1, hito_2])
    db_session.commit()

    return {
        "agencia_arequipa": agencia_arequipa,
        "envio_demo": envio_demo,
        "cliente_rem": cliente_rem
    }


def test_listar_agencias_publicas(client, publico_seed_data):
    """Verifica el listado de agencias habilitadas para clientes web."""
    res = client.get("/api/v1/publico/agencias")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert len(body["data"]) >= 2
    nombres = [a["nombre"] for a in body["data"]]
    assert "Sede Central Lima" in nombres
    assert "Sede Arequipa Parque Industrial" in nombres


def test_cotizador_peso_fisico(client):
    """Cotiza envío de 10 kg con dimensiones pequeñas (prevalece peso físico)."""
    res = client.post(
        "/api/v1/publico/cotizar",
        json={
            "agencia_origen_id": 1,
            "agencia_destino_id": 2,
            "tipo_envio": "agencia_agencia",
            "peso_kg": 10.0,
            "largo_cm": 20.0,
            "ancho_cm": 20.0,
            "alto_cm": 20.0
        }
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["peso_fisico"] == 10.0
    assert data["tarifa_base"] == 8.00
    # 10 * 2.50 = 25.00
    assert data["tarifa_peso_adicional"] == 25.00
    assert data["recargo_domicilio"] == 0.00
    assert data["precio_total"] == 33.00


def test_cotizador_peso_volumetrico(client):
    """Cotiza bulto liviano pero voluminoso (prevalece peso volumétrico)."""
    # 60 * 50 * 40 / 6000 = 20.0 kg volumétrico vs 2 kg físico
    res = client.post(
        "/api/v1/publico/cotizar",
        json={
            "agencia_origen_id": 1,
            "agencia_destino_id": 2,
            "tipo_envio": "agencia_domicilio",
            "peso_kg": 2.0,
            "largo_cm": 60.0,
            "ancho_cm": 50.0,
            "alto_cm": 40.0
        }
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["peso_volumetrico"] == 20.0
    assert data["peso_liquidable"] == 20.0
    assert data["recargo_domicilio"] == 12.00
    # 8.00 + (20 * 2.50 = 50.00) + 12.00 = 70.00
    assert data["precio_total"] == 70.00


def test_tracking_existente_con_pii_enmascarado(client, publico_seed_data):
    """Tracking devuelve datos públicos y enmascara PII de remitente y destinatario."""
    res = client.get("/api/v1/publico/tracking/CE-2026-00001")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["codigo_tracking"] == "CE-2026-00001"
    assert data["estado"] == "EN_TRANSITO"
    # PII enmascarada
    assert "Juan Carlos" not in data["remitente"]
    assert "*" in data["remitente"]
    assert "*" in data["destinatario"]
    # Historial de 2 hitos
    assert len(data["historial"]) == 2
    assert data["historial"][0]["estado"] == "REGISTRADO"
    assert data["historial"][1]["estado"] == "EN_TRANSITO"


def test_tracking_no_existente(client):
    """Tracking con código erróneo retorna HTTP 404 estandarizado."""
    res = client.get("/api/v1/publico/tracking/CE-INEXISTENTE-999")
    assert res.status_code == 404
    assert res.json()["success"] is False


def test_buscar_cliente_existente(client, publico_seed_data):
    """Búsqueda de cliente por DNI enmascara email y teléfono."""
    res = client.get("/api/v1/publico/buscar-cliente/45678912")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["encontrado"] is True
    assert data["nombre_completo"] == "Juan Carlos Pérez Ramos"
    assert data["telefono_enmascarado"].endswith("321")
    assert "@" in data["email_enmascarado"]


def test_registrar_pedido_web_exitoso(client, publico_seed_data):
    """Pre-registro exitoso de encomienda genera tracking y desglose contable."""
    res = client.post(
        "/api/v1/publico/pedidos/registrar",
        json={
            "rem_tipo_doc": "dni",
            "rem_num_doc": "11223344",
            "rem_nombre": "Roberto Alva",
            "rem_email": "roberto@ejemplo.pe",
            "rem_telefono": "999888777",
            "dest_tipo_doc": "dni",
            "dest_num_doc": "55667788",
            "dest_nombre": "Lucia Mendez",
            "agencia_origen_id": 1,
            "agencia_destino_id": 2,
            "tipo_envio": "agencia_agencia",
            "tipo_paquete": "caja",
            "peso_kg": 4.0,
            "largo_cm": 25.0,
            "ancho_cm": 20.0,
            "alto_cm": 15.0,
            "descripcion": "Caja de herramientas"
        }
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["codigo_tracking"].startswith("CE-2026-")
    assert data["precio_estimado"] > 0
    assert data["monto_subtotal"] > 0
    assert data["monto_igv"] > 0
    assert data["estado"] == "REGISTRADO"

    # Verificar que ahora se puede rastrear de inmediato
    track_res = client.get(f"/api/v1/publico/tracking/{data['codigo_tracking']}")
    assert track_res.status_code == 200
    assert track_res.json()["data"]["codigo_tracking"] == data["codigo_tracking"]
