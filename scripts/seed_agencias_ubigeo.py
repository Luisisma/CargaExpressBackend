import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cargaexpress.db")

NUEVAS_AGENCIAS = [
    (53, 1053, 'AGENCIA LIMA - LOS OLIVOS', 15, 'Lima', 'Lima', 'Los Olivos', 'Av. Carlos Izaguirre 1250, Los Olivos', 'habilitado'),
    (54, 1054, 'AGENCIA LIMA - SAN JUAN DE MIRAFLORES', 15, 'Lima', 'Lima', 'San Juan de Miraflores', 'Av. Los Héroes 480, San Juan de Miraflores', 'habilitado'),
    (55, 1055, 'AGENCIA LIMA - ATE VITARTE', 15, 'Lima', 'Lima', 'Ate', 'Carretera Central Km 7.5, Ate', 'habilitado'),
    (56, 1056, 'AGENCIA LIMA - HUACHO', 15, 'Lima', 'Huaura', 'Huacho', 'Av. 28 de Julio 320, Huacho', 'habilitado'),
    (57, 1057, 'AGENCIA AREQUIPA - PAUCARPATA', 4, 'Arequipa', 'Arequipa', 'Paucarpata', 'Av. Mariscal Castilla 815, Paucarpata', 'habilitado'),
    (58, 1058, 'AGENCIA AREQUIPA - CERRO COLORADO', 4, 'Arequipa', 'Arequipa', 'Cerro Colorado', 'Av. Aviación 602, Cerro Colorado', 'habilitado'),
    (59, 1059, 'AGENCIA LA LIBERTAD - EL PORVENIR', 13, 'La Libertad', 'Trujillo', 'El Porvenir', 'Av. Sánchez Carrión 540, El Porvenir', 'habilitado'),
    (60, 1060, 'AGENCIA LA LIBERTAD - HUAMACHUCO', 13, 'La Libertad', 'Sánchez Carrión', 'Huamachuco', 'Jr. Ramón Castilla 210, Huamachuco', 'habilitado'),
    (61, 1061, 'AGENCIA LAMBAYEQUE - FERREÑAFE', 14, 'Lambayeque', 'Ferreñafe', 'Ferreñafe', 'Calle Real 145, Ferreñafe', 'habilitado'),
    (62, 1062, 'AGENCIA PIURA - TALARA', 20, 'Piura', 'Talara', 'Pariñas', 'Av. Bolognesi 310, Talara', 'habilitado'),
    (63, 1063, 'AGENCIA PIURA - PAITA', 20, 'Piura', 'Paita', 'Paita', 'Jr. Zepita 180, Paita', 'habilitado'),
    (64, 1064, 'AGENCIA ICA - PISCO', 11, 'Ica', 'Pisco', 'Pisco', 'Calle Comercio 412, Pisco', 'habilitado'),
    (65, 1065, 'AGENCIA ICA - NAZCA', 11, 'Ica', 'Nazca', 'Nazca', 'Av. Los Incas 230, Nazca', 'habilitado'),
    (66, 1066, 'AGENCIA CUSCO - URUBAMBA', 8, 'Cusco', 'Urubamba', 'Urubamba', 'Av. Ferrocarril 115, Urubamba', 'habilitado'),
    (67, 1067, 'AGENCIA JUNÍN - TARMA', 12, 'Junín', 'Tarma', 'Tarma', 'Jr. Lima 450, Tarma', 'habilitado'),
    (68, 1068, 'AGENCIA SAN MARTÍN - JUANJUÍ', 22, 'San Martín', 'Mariscal Cáceres', 'Juanjuí', 'Jr. Huallaga 315, Juanjuí', 'habilitado')
]

def poblar_agencias():
    if not os.path.exists(DB_PATH):
        print(f"[!] No existe el archivo de base de datos en: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    insertados = 0
    for a in NUEVAS_AGENCIAS:
        cursor.execute("SELECT id FROM agencias WHERE id = ? OR codigo_agencia = ?", (a[0], a[1]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO agencias (id, codigo_agencia, nombre, departamento_id, departamento, provincia, distrito, direccion, estado, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, a)
            insertados += 1
            
    conn.commit()
    conn.close()
    print(f"[OK] {insertados} nuevas agencias provinciales y distritales insertadas exitosamente en {DB_PATH}.")

if __name__ == "__main__":
    poblar_agencias()

