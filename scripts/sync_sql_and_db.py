# -*- coding: utf-8 -*-
"""
Script para sincronizar y volcar el dataset ampliado de 2026 a cargaexpress.sql y cargaexpress.db
"""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from scripts.generate_dw_seed_2026 import (
    USUARIOS_NUEVOS, NUEVOS_VEHICULOS, NUEVAS_ASIGNACIONES,
    NUEVOS_CLIENTES, NUEVAS_APERTURAS_CAJA,
    DEFAULT_PWD_HASH, construir_datawarehouse_seed, SQL_FILE, poblar_sqlite
)

def generar_inserts_sql():
    data = construir_datawarehouse_seed()

    # 1. SQL Usuarios
    sql_usuarios = []
    for u in USUARIOS_NUEVOS:
        caja_val = f"{u[8]}" if u[8] is not None else "NULL"
        lic_val = f"'{u[9]}'" if u[9] is not None else "NULL"
        totp = f"TOTPSEC2026CARGAEXPRESS{u[0]:02d}"
        sql_usuarios.append(
            f"({u[0]}, {u[1]}, '{u[2]}', '{u[3]}', '{u[4]}', '{u[5]}', '{DEFAULT_PWD_HASH}', "
            f"'{u[6]}', {u[7]}, {caja_val}, {lic_val}, '{totp}', false, 0, false, 1, true, "
            f"'2026-01-05 08:00:00', '2026-01-05 08:00:00', '{u[10]}')"
        )

    # 2. SQL Vehículos
    sql_vehiculos = []
    for v in NUEVOS_VEHICULOS:
        sql_vehiculos.append(
            f"({v[0]}, '{v[1]}', '{v[2]}', '{v[3]}', '{v[4]}', true, '2026-01-05 08:00:00')"
        )

    # 3. SQL Asignaciones
    sql_asignaciones = []
    for a in NUEVAS_ASIGNACIONES:
        sql_asignaciones.append(
            f"({a[0]}, {a[1]}, {a[2]}, '{a[3]}', NULL, true, '{a[3]} 08:00:00')"
        )

    # 4. SQL Clientes
    sql_clientes = []
    for c in NUEVOS_CLIENTES:
        sql_clientes.append(
            f"({c[0]}, '{c[1]}', '{c[2]}', '{c[3]}', '{c[4]}', '{c[5]}', '{c[6]}', true, '2026-01-05 08:00:00', '2026-01-05 08:00:00', 1)"
        )

    # 5. SQL Aperturas de caja
    sql_aperturas = []
    for ap in NUEVAS_APERTURAS_CAJA:
        f_cierre_val = f"'{ap[5]}'" if ap[5] else "NULL"
        s_fin_val = f"{ap[6]:.2f}" if ap[6] is not None else "NULL"
        tot_v_val = f"{ap[7]:.2f}" if ap[7] is not None else "NULL"
        sql_aperturas.append(
            f"({ap[0]}, {ap[1]}, {ap[2]}, {ap[3]:.2f}, '{ap[4]}', {f_cierre_val}, {s_fin_val}, {tot_v_val}, '{ap[8]}', '{ap[4]}')"
        )

    # 6. SQL Envíos
    sql_envios = []
    for e in data['envios']:
        f_entrega = f"'{e[25]}'" if e[25] else "NULL"
        dir_ent = f"'{e[15]}'" if e[15] else "NULL"
        courier = f"{e[34]}" if e[34] else "NULL"
        sql_envios.append(
            f"({e[0]}, '{e[1]}', {e[2]}, {e[3]}, {e[4]}, {e[5]}, '{e[6]}', '{e[7]}', {e[8]:.2f}, "
            f"{e[9]:.2f}, {e[10]:.2f}, {e[11]:.2f}, {e[12]:.2f}, '{e[13]}', NULL, {dir_ent}, "
            f"{e[16]:.2f}, {e[17]:.2f}, {e[18]:.2f}, {e[19]:.2f}, '{e[20]}', '{e[21]}', '{e[22]}', "
            f"'{e[23]}', '{e[24]}', {f_entrega}, NULL, NULL, '{e[28]}', '{e[29]}', '{e[30]}', "
            f"{e[31]}, false, {e[33]}, {courier}, '{e[35]}', '{e[36]}')"
        )

    # 7. SQL Guías
    sql_guias = []
    for g in data['guias']:
        sql_guias.append(
            f"({g[0]}, {g[1]}, {g[2]}, {g[3]}, '{g[4]}', '{g[5]}', {g[6]}, {g[7]}, {g[8]}, '{g[9]}', '{g[10]}')"
        )

    sql_guias_detalle = []
    for gd in data['guias_detalle']:
        sql_guias_detalle.append(
            f"({gd[0]}, {gd[1]}, {gd[2]}, '{gd[3]}')"
        )

    # 8. SQL Historial
    sql_historial = []
    for h in data['historial']:
        sql_historial.append(
            f"({h[0]}, {h[1]}, '{h[2]}', '{h[3]}', '{h[4]}', {h[5]}, '{h[6]}')"
        )

    # 9. SQL Movimientos Caja
    sql_movimientos = []
    for m in data['movimientos']:
        sql_movimientos.append(
            f"({m[0]}, {m[1]}, {m[2]}, '{m[3]}', {m[4]:.2f}, '{m[5]}', '{m[6]}')"
        )

    return {
        'usuarios': sql_usuarios,
        'vehiculos': sql_vehiculos,
        'asignaciones': sql_asignaciones,
        'clientes': sql_clientes,
        'aperturas': sql_aperturas,
        'envios': sql_envios,
        'guias': sql_guias,
        'guias_detalle': sql_guias_detalle,
        'historial': sql_historial,
        'movimientos': sql_movimientos
    }

if __name__ == "__main__":
    print("[*] Sincronizador listo.")

