# -*- coding: utf-8 -*-
"""
=============================================================================
 MIGRACIÓN MASIVA DE SERIE DE TRACKING: CE-2026-NXXXXXX (CargaExpress Perú)
=============================================================================
Propósito:
1. Convierte todos los códigos artificiales legacy (CE26...) al estándar
   oficial corporativo de 15 caracteres: CE-2026-NXXXXXX (Serie N = Red Nacional).
2. Preserva intactas las órdenes reales generadas por clientes en el portal web
   (Serie P = CE-2026-P...).
3. Sincroniza movimientos de caja para mantener coherencia contable.
4. Distribuye de forma realista un 1.5% de siniestros viales y 3.5% de cancelaciones/anulaciones.
5. Regulariza la línea de tiempo (historial_envios) y regenera dwh_powerbi/*.csv.
=============================================================================
"""

import os
import sys
import sqlite3
import random

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, "cargaexpress.db")
OUTPUT_DIR = os.path.join(BACKEND_DIR, "dwh_powerbi")

TRACKING_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"

def generar_tracking_serie_nacional(seed_id: int) -> str:
    rng = random.Random(20260000 + seed_id)
    sufijo_6 = "".join(rng.choice(TRACKING_ALPHABET) for _ in range(6))
    return f"CE-2026-N{sufijo_6}"

def migrar_base_datos():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No existe la base de datos en: {DB_PATH}")
        return

    print("=" * 70)
    print(" INICIANDO MIGRACIÓN CORPORATIVA: SERIE NACIONAL CE-2026-NXXXXXX")
    print(f" Conectado a: {DB_PATH}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Consultar envíos que tienen formato antiguo (CE26...)
    cursor.execute("SELECT id, codigo_tracking, estado, estado_pago FROM envios ORDER BY id ASC;")
    todos = cursor.fetchall()

    codigos_existentes = set()
    actualizados = 0
    conservados = 0

    # Guardar los códigos que ya tienen formato oficial de clientes (CE-2026-P...)
    for eid, cod, est, pag in todos:
        if cod.startswith("CE-2026-P"):
            codigos_existentes.add(cod)
            conservados += 1

    print(f"-> Detectadas {len(todos)} encomiendas en total.")
    print(f"-> Órdenes reales preservadas (Serie P): {conservados}")

    # 2. Generar y asignar nuevo código CE-2026-N... a cada encomienda artificial
    mapeo_cambios = []
    ids_antiguos = []

    for eid, cod_antiguo, est, pag in todos:
        if cod_antiguo.startswith("CE-2026-P"):
            continue  # Respetar órdenes reales de clientes

        nuevo_cod = generar_tracking_serie_nacional(eid)
        # Garantizar unicidad absoluta
        intento = 1
        while nuevo_cod in codigos_existentes:
            nuevo_cod = generar_tracking_serie_nacional(eid * 100 + intento)
            intento += 1

        codigos_existentes.add(nuevo_cod)
        mapeo_cambios.append((nuevo_cod, eid, cod_antiguo))
        ids_antiguos.append(eid)

    # 3. Actualizar tabla envios en lote
    for nuevo_cod, eid, cod_antiguo in mapeo_cambios:
        cursor.execute("UPDATE envios SET codigo_tracking = ? WHERE id = ?;", (nuevo_cod, eid))
        # Actualizar descripción en movimientos_caja si existía referencia
        cursor.execute("""
            UPDATE movimientos_caja 
            SET descripcion = REPLACE(descripcion, ?, ?)
            WHERE envio_id = ?;
        """, (cod_antiguo, nuevo_cod, eid))
        actualizados += 1

    conn.commit()
    print(f" [OK] Se actualizaron {actualizados} encomiendas a la Serie Nacional (CE-2026-NXXXXXX).")

    # 4. Inyectar cuota realista de siniestros (~1.5%) y cancelaciones (~3.5%) sobre los datos de la red nacional
    print("\n-> Calibrando cuotas realistas de Siniestralidad (1.5%) y Cancelaciones (3.5%)...")
    random.seed(20261104)

    # Buscar envíos antiguos (> 14 días) para aplicar la distribución
    cursor.execute("""
        SELECT id FROM envios 
        WHERE codigo_tracking LIKE 'CE-2026-N%' 
          AND julianday('now') - julianday(creado_en) > 14
        ORDER BY id ASC;
    """)
    ids_antiguos_dwh = [r[0] for r in cursor.fetchall()]

    if ids_antiguos_dwh:
        # 1.5% Siniestrados (~18 a 20 casos en todo el año)
        cant_siniestros = max(15, int(len(ids_antiguos_dwh) * 0.015))
        # 3.5% Cancelados / Anulados (~40 a 45 casos)
        cant_cancelados = max(35, int(len(ids_antiguos_dwh) * 0.035))

        muestra_siniestros = random.sample(ids_antiguos_dwh, cant_siniestros)
        disponibles_canc = [i for i in ids_antiguos_dwh if i not in muestra_siniestros]
        muestra_cancelados = random.sample(disponibles_canc, cant_cancelados)

        # Aplicar siniestros (pagado, pero siniestrado en ruta)
        for sid in muestra_siniestros:
            cursor.execute("""
                UPDATE envios 
                SET estado = 'siniestrado', estado_pago = 'pagado', fecha_entrega_real = NULL
                WHERE id = ?;
            """, (sid,))

        # Aplicar cancelaciones (pre-registro anulado, pago pendiente)
        for cid in muestra_cancelados:
            cursor.execute("""
                UPDATE envios 
                SET estado = 'anulado', estado_pago = 'pendiente', forma_pago = 'pendiente', fecha_entrega_real = NULL
                WHERE id = ?;
            """, (cid,))
            # Eliminar cualquier movimiento de caja ficticio de estas cancelaciones
            cursor.execute("DELETE FROM movimientos_caja WHERE envio_id = ?;", (cid,))

        conn.commit()
        print(f" [OK] {len(muestra_siniestros)} encomiendas configuradas en estado 'siniestrado'.")
        print(f" [OK] {len(muestra_cancelados)} encomiendas configuradas en estado 'anulado' (cancelado).")

    conn.close()

    # 5. Regularizar hitos cronológicos en historial_envios
    print("\n-> Sincronizando historial de auditoría con regularize_historial_envios...")
    sys.path.insert(0, os.path.dirname(__file__))
    import regularize_historial_envios
    regularize_historial_envios.main()

    # 6. Exportar datasets a dwh_powerbi/ para Power BI
    print("\n-> Regenerando datasets analíticos CSV para Power BI...")
    import export_dwh_for_powerbi
    export_dwh_for_powerbi.main()

    print("\n" + "=" * 70)
    print(" ¡MIGRACIÓN COMPLETADA AL 100% CON ÉXITO!")
    print(" Toda tu base de datos y tus archivos Power BI tienen ahora el formato")
    print(" oficial corporativo CE-2026-NXXXXXX, con siniestros y cancelaciones reales.")
    print("=" * 70)

if __name__ == "__main__":
    migrar_base_datos()

