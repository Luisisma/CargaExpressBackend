# Flujo de Exposición 09: Dataset Semilla 2026 y Preparación Data Warehouse

## 1. Resumen Ejecutivo
Para habilitar las analíticas operativas y estratégicas del **Data Warehouse 2026** de CargaExpress Perú, se ha diseñado e implementado una arquitectura de datos semilla normalizada y cronológica que cubre el periodo **Enero a Noviembre 2026**.

El dataset refleja:
- Crecimiento sostenido del negocio con curvas de demanda ascendente.
- Tasa de cumplimiento y efectividad de entrega superior al 85%.
- Cadena de custodia logística completa: desde la emisión del comprobante (Boleta/Factura con IGV 18%) hasta el arribo, asignación a courier y liquidación en caja.
- Catálogo nacional completo de **84 agencias operativas** distribuidas en los 25 departamentos según la codificación oficial de **INEI Ubigeo**.

---

## 2. Catálogo de Colaboradores Operativos (32 Nuevos Usuarios)
Todos los usuarios se crearon con roles operativos variados, contraseña por defecto `CargaExp#2026`, credenciales de correo bajo la convención corporativa `nombre.apellido@cargaexpress.pe` y DNIs peruanos validados:

| ID | Código | Rol | Nombres y Apellidos | DNI | Licencia MTC | Agencia Sede | Email |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 9 | 9 | `cajero` | Juan Carlos Pérez Quispe | 10458923 | - | Lima - Javier Prado (#1) | `juan.perez@cargaexpress.pe` |
| 10 | 10 | `cajero` | Rosa María Benavides Alva | 72345678 | - | Arequipa - P. Armas (#2) | `rosa.benavides@cargaexpress.pe` |
| 11 | 11 | `supervisor` | Carlos Alberto Mendoza Ramos | 45678912 | - | Arequipa - P. Armas (#2) | `carlos.mendoza@cargaexpress.pe` |
| 12 | 12 | `cajero` | Lucía Valeria Paredes Cano | 78123456 | - | Lima - Miraflores (#3) | `lucia.paredes@cargaexpress.pe` |
| 13 | 13 | `almacen` | Jorge Luis Huamán Ticona | 41239876 | - | Lima - Javier Prado (#1) | `jorge.huaman@cargaexpress.pe` |
| 14 | 14 | `supervisor` | Patricia Sofía Morales Vega | 70987654 | - | Lima - Miraflores (#3) | `patricia.morales@cargaexpress.pe` |
| 15 | 15 | `transportista` | Miguel Ángel Flores Carazas | 43567890 | Q43567890 (A-IIIc) | Lima - Javier Prado (#1) | `miguel.flores@cargaexpress.pe` |
| 16 | 16 | `cajero` | Andrea Celeste Rivas Chávez | 76543210 | - | Cañete (#4) | `andrea.rivas@cargaexpress.pe` |
| 17 | 17 | `courier` | Diego Alonso Castillo Ruiz | 44567891 | B44567891 (B-IIb) | Lima - Javier Prado (#1) | `diego.castillo@cargaexpress.pe` |
| 18 | 18 | `almacen` | Gabriela Elena Navarro Soto | 75432109 | - | Arequipa - P. Armas (#2) | `gabriela.navarro@cargaexpress.pe` |
| 19 | 19 | `transportista` | Fernando José Rojas Valdivia | 42345678 | Q42345678 (A-IIIc) | Arequipa - P. Armas (#2) | `fernando.rojas@cargaexpress.pe` |
| 20 | 20 | `cajero` | Claudia Marcela Medina Espinoza | 71234567 | - | Callao - Bellavista (#5) | `claudia.medina@cargaexpress.pe` |
| 21 | 21 | `almacen` | Víctor Manuel Romero Salas | 46789012 | - | Cusco - Wanchaq (#11) | `victor.romero@cargaexpress.pe` |
| 22 | 22 | `supervisor` | Fiorella Beatriz Díaz Cárdenas | 74321098 | - | Cusco - Wanchaq (#11) | `fiorella.diaz@cargaexpress.pe` |
| 23 | 23 | `courier` | Renzo Javier Vargas Aguilar | 47890123 | B47890123 (B-IIb) | Arequipa - P. Armas (#2) | `renzo.vargas@cargaexpress.pe` |
| 24 | 24 | `cajero` | Stephanie Paola Cruz Delgado | 73210987 | - | La Libertad - Trujillo (#19) | `stephanie.cruz@cargaexpress.pe` |
| 25 | 25 | `almacen` | Walter Enrique Salazar Bravo | 48901234 | - | La Libertad - Trujillo (#19) | `walter.salazar@cargaexpress.pe` |
| 26 | 26 | `supervisor` | Vanessa Carolina Ortiz Peña | 72109876 | - | La Libertad - Trujillo (#19) | `vanessa.ortiz@cargaexpress.pe` |
| 27 | 27 | `transportista` | Christian Alexander Ramos Silva | 49012345 | Q49012345 (A-IIIc) | La Libertad - Trujillo (#19) | `christian.ramos@cargaexpress.pe` |
| 28 | 28 | `cajero` | Karina Lizbeth Morales Guerrero | 71098765 | - | Lambayeque - Chiclayo (#21) | `karina.morales@cargaexpress.pe` |
| 29 | 29 | `almacen` | Raúl Ernesto Gómez Palacios | 40123456 | - | Lambayeque - Chiclayo (#21) | `raul.gomez@cargaexpress.pe` |
| 30 | 30 | `courier` | Melissa Isabel Tapia Lozano | 70987651 | B70987651 (B-IIb) | La Libertad - Trujillo (#19) | `melissa.tapia@cargaexpress.pe` |
| 31 | 31 | `transportista` | Oscar Eduardo Cabrera Montes | 41234567 | Q41234567 (A-IIIc) | Lambayeque - Chiclayo (#21) | `oscar.cabrera@cargaexpress.pe` |
| 32 | 32 | `cajero` | Diana Carolina Herrera Ponce | 79876543 | - | Piura (#23) | `diana.herrera@cargaexpress.pe` |
| 33 | 33 | `almacen` | Gonzalo Andrés Cueva Villalobos | 42345679 | - | Piura (#23) | `gonzalo.cueva@cargaexpress.pe` |
| 34 | 34 | `supervisor` | Lorena Patricia Alva Bustamante | 78765432 | - | Piura (#23) | `lorena.alva@cargaexpress.pe` |
| 35 | 35 | `courier` | Julio César Villegas Cornejo | 43456780 | B43456780 (B-IIb) | Piura (#23) | `julio.villegas@cargaexpress.pe` |
| 36 | 36 | `cajero` | Shirley Tatiana Miranda Barreto | 77654321 | - | Ica (#7) | `shirley.miranda@cargaexpress.pe` |
| 37 | 37 | `almacen` | Edwin Arturo Pacheco Zúñiga | 44567892 | - | Ica (#7) | `edwin.pacheco@cargaexpress.pe` |
| 38 | 38 | `supervisor` | Maricielo Nicole Campos Ríos | 76543219 | - | Ica (#7) | `maricielo.campos@cargaexpress.pe` |
| 39 | 39 | `transportista` | Héctor Daniel Prado Benítez | 45678913 | Q45678913 (A-IIIc) | Ica (#7) | `hector.prado@cargaexpress.pe` |
| 40 | 40 | `courier` | Milagros Alejandra Castro Quiroz | 75432198 | B75432198 (B-IIb) | Ica (#7) | `milagros.castro@cargaexpress.pe` |

---

## 3. Comportamiento Temporal de Envíos 2026 (Progresión Positiva)
El volumen mensual ilustra una curva ascendente de captación de mercado:

```
Envíos
  ▲
8 ┼                                      ╭───╮   ╭───╮   ╭───╮
7 ┼                              ╭───╮   │   │   │   │   │   │   ╭───╮
6 ┼                      ╭───╮   │   │   │   │   │   │   │   │   │   │
5 ┼              ╭───╮   │   │   │   │   │   │   │   │   │   │   │   │
4 ┼      ╭───╮   │   │   │   │   │   │   │   │   │   │   │   │   │   │
3 ┼  ╭───┤   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
  └──┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───► Mes (2026)
    Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov
```

- **Enero:** 3 órdenes (lanzamiento y validación de rutas troncales).
- **Febrero a Abril:** 4 a 5 órdenes mensuales (expansión a zona sur y norte).
- **Mayo a Julio:** 5 a 6 órdenes mensuales (incorporación de entregas a domicilio).
- **Agosto a Octubre:** 7 órdenes mensuales (pico de consolidación corporativa B2B).
- **Noviembre:** 6 órdenes (operación en curso reflejando estados vivos: entregados, en tránsito, recepcionados y pendientes).

---

## 4. Scripts y Archivos Generados
1. [cargaexpress.sql](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress.sql): Dump maestro PostgreSQL actualizado con los 84 agencias, 40 usuarios, 45 clientes, 6 vehículos, 16 aperturas de caja, 74 envíos, 32 guías y 69 movimientos.
2. [seed_dw_2026.sql](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/seed_dw_2026.sql): Script SQL modular e idempotente (`ON CONFLICT DO NOTHING`) para inyecciones puntuales en entornos staging o Data Warehouse.
3. [generate_dw_seed_2026.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/generate_dw_seed_2026.py): Generador algorítmico y poblador directo a SQLite (`cargaexpress.db`).

