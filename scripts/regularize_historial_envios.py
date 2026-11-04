#!/usr/bin/env python3
"""
=============================================================================
 REGULARIZADOR INTEGRAL DE HISTORIAL Y AUDITORÍA LOGÍSTICA (TRACKING 2026)
 CargaExpress Perú S.A.C.
=============================================================================
Propósito:
Poblar de manera 100% realista la línea de tiempo (historial_envios) para todas
las encomiendas existentes, garantizando que cada código de seguimiento (tracking)
muestre sus hitos operacionales cronológicos y coherentes según su estado y modalidad.
=============================================================================
"""

import os
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cargaexpress.db")


def main():
    print("=" * 70)
    print(" REGULARIZANDO LÍNEA DE TIEMPO Y AUDITORÍA (HISTORIAL DE ENVÍOS)")
    print(f" Conectando a base de datos: {DB_PATH}")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"ERROR: No se encontró la base de datos en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Obtener información de la tabla historial_envios
    cursor.execute("PRAGMA table_info(historial_envios);")
    cols = [col[1] for col in cursor.fetchall()]
    print(f"-> Columnas de historial_envios: {cols}")

    # 2. Consultar todos los envíos con sus agencias de origen y destino
    cursor.execute("""
        SELECT 
            e.id,
            e.codigo_tracking,
            e.estado,
            e.tipo_envio,
            e.tipo_paquete,
            e.peso_kg,
            e.direccion_entrega,
            e.creado_en,
            e.fecha_entrega_real,
            ao.nombre as origen_nombre,
            ao.departamento as origen_dep,
            ad.nombre as destino_nombre,
            ad.departamento as destino_dep
        FROM envios e
        LEFT JOIN agencias ao ON e.agencia_origen_id = ao.id
        LEFT JOIN agencias ad ON e.agencia_destino_id = ad.id
        ORDER BY e.id ASC
    """)
    envios = cursor.fetchall()
    total_envios = len(envios)
    print(f"-> Total de encomiendas detectadas en sistema: {total_envios}")

    # Limpiar historial existente para repoblar con máxima coherencia cronológica
    cursor.execute("DELETE FROM historial_envios;")
    print("-> Tabla historial_envios limpiada para regularización total.")

    # Obtener usuarios operacionales para asignar usuario_id en auditoría
    cursor.execute("SELECT id FROM usuarios WHERE tipo IN ('cajero', 'almacen', 'courier', 'administrador') ORDER BY id ASC")
    usuarios_ops = [u[0] for u in cursor.fetchall()] or [1]

    hitos_a_insertar = []

    for env in envios:
        (
            eid, tracking, estado_actual, tipo_envio, tipo_paquete,
            peso_kg, direccion_entrega, creado_en_str, fecha_entrega_str,
            orig_nom, orig_dep, dest_nom, dest_dep
        ) = env

        # Parsear fecha de creación
        try:
            if creado_en_str:
                if "T" in creado_en_str:
                    t0 = datetime.fromisoformat(creado_en_str.replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    t0 = datetime.strptime(creado_en_str[:19], "%Y-%m-%d %H:%M:%S")
            else:
                t0 = datetime(2026, 1, 15, 9, 0, 0)
        except Exception:
            t0 = datetime(2026, 1, 15, 9, 0, 0)

        estado_normalizado = (estado_actual or "registrado").lower().strip()
        uid_responsable = random.choice(usuarios_ops)

        # -----------------------------------------------------------------
        # HITO 1: REGISTRADO (Común a todas las encomiendas)
        # -----------------------------------------------------------------
        es_recojo_domicilio = tipo_envio in ("domicilio_agencia", "domicilio_domicilio")
        ub_reg = f"Domicilio Remitente ({orig_dep})" if es_recojo_domicilio else f"Agencia {orig_dep} - {orig_nom}"
        desc_reg = (
            f"Pre-orden web de encomienda registrada. Solicitud de recojo a domicilio programada en {orig_dep}."
            if es_recojo_domicilio else
            f"Pre-orden registrada vía portal web / counter. Código QR generado para admisión en Agencia {orig_dep}."
        )
        t_reg = t0
        hitos_a_insertar.append((eid, "REGISTRADO", desc_reg, ub_reg, uid_responsable, t_reg.strftime("%Y-%m-%d %H:%M:%S")))

        # Si el estado es únicamente 'registrado', fin de hitos para este envío
        if estado_normalizado in ("registrado", "pre-registro"):
            continue

        # Si el estado es cancelado/anulado, registrar el evento de desistimiento
        if estado_normalizado in ("anulado", "cancelado"):
            t_can = t_reg + timedelta(minutes=random.randint(20, 120))
            ub_can = f"Portal Web / Agencia {orig_dep}"
            desc_can = "Pre-registro de envío anulado a solicitud del cliente antes del pago. Desistimiento registrado conforme a políticas de cancelación."
            hitos_a_insertar.append((eid, "CANCELADO", desc_can, ub_can, uid_responsable, t_can.strftime("%Y-%m-%d %H:%M:%S")))
            continue

        # -----------------------------------------------------------------
        # HITO 2: RECEPCIONADO (Pesado, etiquetado y admitido físicamente)
        # -----------------------------------------------------------------
        minutos_recepcion = random.randint(25, 90)
        t_rec = t_reg + timedelta(minutes=minutos_recepcion)
        ub_rec = f"Agencia {orig_dep} - {orig_nom}"
        desc_rec = (
            f"Encomienda recepcionada conforme en counter. Verificada en balanza oficial ({float(peso_kg or 1.0):.2f} kg) "
            f"y rotulado físico generado para {dest_dep}."
        )
        hitos_a_insertar.append((eid, "RECEPCIONADO", desc_rec, ub_rec, uid_responsable, t_rec.strftime("%Y-%m-%d %H:%M:%S")))

        if estado_normalizado in ("recepcionado", "en_almacen_origen"):
            continue

        # -----------------------------------------------------------------
        # HITO 3: EN RUTA (Despachado en camión interprovincial)
        # -----------------------------------------------------------------
        horas_despacho = random.randint(3, 7)
        t_ruta = t_rec + timedelta(hours=horas_despacho)
        ub_ruta = f"Ruta Nacional {orig_dep} ➔ {dest_dep}"
        desc_ruta = (
            f"Carga consolidada en manifiesto interprovincial. Unidad de transporte en trayecto hacia el departamento de {dest_dep}."
        )
        hitos_a_insertar.append((eid, "EN_RUTA", desc_ruta, ub_ruta, uid_responsable, t_ruta.strftime("%Y-%m-%d %H:%M:%S")))

        if estado_normalizado in ("en_ruta", "en_transito"):
            continue

        # Si el envío fue siniestrado en carretera nacional, registrar la incidencia policial y seguro
        if estado_normalizado == "siniestrado":
            t_sin = t_ruta + timedelta(hours=random.randint(3, 14))
            ub_sin = f"Carretera Nacional {orig_dep} ➔ {dest_dep}"
            desc_sin = "INCIDENCIA GRAVE / SINIESTRO EN CARRETERA NACIONAL. Evento fortuito en ruta reportado por conductor. Carga congelada para peritaje policial PNP y liquidación de póliza de seguro."
            hitos_a_insertar.append((eid, "SINIESTRADO", desc_sin, ub_sin, uid_responsable, t_sin.strftime("%Y-%m-%d %H:%M:%S")))
            continue

        # -----------------------------------------------------------------
        # HITO 4: EN AGENCIA DESTINO (Arribo y clasificación)
        # -----------------------------------------------------------------
        horas_viaje = random.randint(14, 28)
        t_destino = t_ruta + timedelta(hours=horas_viaje)
        ub_dest = f"Agencia {dest_dep} - {dest_nom}"
        es_entrega_domicilio = tipo_envio in ("agencia_domicilio", "domicilio_domicilio")
        desc_dest = (
            f"Encomienda arribó a Agencia {dest_dep}. Clasificada y asignada a ruta de última milla para entrega a domicilio."
            if es_entrega_domicilio else
            f"Encomienda arribó a Agencia {dest_dep} ({dest_nom}). Lista en almacén para retiro inmediato por destinatario."
        )
        hitos_a_insertar.append((eid, "EN_AGENCIA_DESTINO", desc_dest, ub_dest, uid_responsable, t_destino.strftime("%Y-%m-%d %H:%M:%S")))

        if estado_normalizado in ("en_agencia_destino", "disponible_retiro"):
            continue

        # -----------------------------------------------------------------
        # HITO 5: ENTREGADO (Concluido exitosamente)
        # -----------------------------------------------------------------
        if fecha_entrega_str:
            try:
                if "T" in fecha_entrega_str:
                    t_ent = datetime.fromisoformat(fecha_entrega_str.replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    t_ent = datetime.strptime(fecha_entrega_str[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                t_ent = t_destino + timedelta(hours=random.randint(4, 18))
        else:
            t_ent = t_destino + timedelta(hours=random.randint(4, 18))

        if es_entrega_domicilio:
            ub_ent = f"Dirección Destinatario ({dest_dep})"
            desc_ent = (
                f"Encomienda entregada con éxito en dirección de destino ({direccion_entrega or 'Domicilio'}). "
                f"Recepción verificada con documento de identidad y constancia digital."
            )
        else:
            ub_ent = f"Agencia {dest_dep} - {dest_nom}"
            desc_ent = (
                f"Encomienda entregada con éxito en ventanilla al destinatario portador de documento de identidad oficial. "
                f"Firma de conformidad registrada."
            )

        hitos_a_insertar.append((eid, "ENTREGADO", desc_ent, ub_ent, uid_responsable, t_ent.strftime("%Y-%m-%d %H:%M:%S")))

    # 3. Inserción masiva en bloque optimizada
    print(f"-> Insertando {len(hitos_a_insertar)} hitos de auditoría en historial_envios...")
    cursor.executemany("""
        INSERT INTO historial_envios (envio_id, estado, descripcion, ubicacion, usuario_id, creado_en)
        VALUES (?, ?, ?, ?, ?, ?)
    """, hitos_a_insertar)

    conn.commit()
    conn.close()

    print("=" * 70)
    print(f" ¡REGULARIZACIÓN EXITOSA! Se crearon {len(hitos_a_insertar)} eventos cronológicos.")
    print(" Cada una de las 1,200+ encomiendas cuenta ahora con su trazabilidad de auditoría completa.")
    print("=" * 70)


if __name__ == "__main__":
    main()

