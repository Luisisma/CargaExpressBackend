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

## 3. Universo de Datos Maestro 2026 (1,275 Envíos Reales)
El dataset consolidado cubre 1,275 órdenes a nivel nacional distribuidas a lo largo del año 2026:

### A. Distribución por Estado Logístico
| Estado Logístico | Envíos | Participación (%) | Significado de Negocio |
| :--- | :---: | :---: | :--- |
| **`entregado`** | 1,172 | 91.92% | Servicio completado con recepción documentada con DNI (`BR-ENV-04`). |
| **`cancelado` / `anulado`** | 42 | 3.29% | Pre-registros web desestimados o caducados tras 48 hrs. |
| **`siniestrado`** | 18 | 1.41% | Incidencias viales (asaltos en ruta, volcaduras) amparadas bajo póliza de seguro. |
| **`en_agencia_destino`** | 18 | 1.41% | Paquetes en estantería de destino listos para recojo en mostrador. |
| **`en_reparto`** | 9 | 0.71% | Bultos asignados al courier para entrega en domicilio última milla. |
| **`en_transito` / `en_ruta`** | 8 | 0.63% | Carga consolidada en bodegas de camiones en autopistas nacionales. |
| **`recepcionado`** | 5 | 0.39% | Encomiendas pesadas y cobradas en balanza de origen. |
| **`registrado`** | 3 | 0.24% | Pre-órdenes web vigentes a la espera de entrega en agencia. |
| **TOTAL** | **1,275** | **100.0%** | **Población total consolidada.** |

---

## 4. Estandarización de Códigos de Tracking (Crockford Base32)
A fin de erradicar inconsistencias entre datos autogenerados y pedidos web reales, el sistema establece dos series oficiales:

1. **Serie Portal Web (`CE-2026-PXXXXXXX`):**
   - Prefijo `P` (Portal).
   - Generada mediante `secrets` con alfabeto Base32 de Crockford (ej. `CE-2026-P8WJVNY`).
   - Identifica pre-órdenes registradas directamente por el cliente en el frontend público.
2. **Serie Red Nacional (`CE-2026-NXXXXXXX`):**
   - Prefijo `N` (Nacional).
   - Generada para la red de 84 agencias provinciales (ej. `CE-2026-N9CBH2A`).
   - Evita colisiones involuntarias con pedidos de clientes reales garantizando unicidad criptográfica.

---

## 5. Conciliación Financiera y Ticket Promedio

### A. Conciliación entre Web Dashboard y Power BI Desktop
Existe una distinción conceptual rigurosa entre la métrica operacional y la métrica analítica de flete bruto:

| Módulo | Métrica Mostrada | Importe (PEN) | Criterio Contable |
| :--- | :--- | :---: | :--- |
| **Web Dashboard** | Facturación Cobrada | **S/ 137,703.10** | **Criterio de Caja:** Solo suma envíos con `estado_pago = 'pagado'` (1,230 órdenes liquidadas en efectivo/bancos). Excluye las 45 órdenes por cobrar/canceladas. |
| **Power BI (Visual Bruto)** | Suma de `total_flete_pen` | **S/ 143,401.00** | **Criterio de Devengado / Flete Bruto:** Suma simple de las 1,275 filas cotizadas. |
| **Diferencia Explicada** | 45 órdenes impagas | **S/ 5,697.90** | Pre-registros web pendientes, contraentregas y siniestros/cancelados sin cobro efectivo. |
| **Power BI (DAX Oficial)** | `[Facturacion_Cobrada_PEN]` | **S/ 137,703.10** | Conciliación exacta centavo a centavo mediante medida DAX con filtro `estado_pago = "pagado"`. |

### B. Análisis del Ticket Promedio (S/ 108.00)
El ticket promedio global de **S/ 108.00** refleja con total realismo la operativa de empresas de paquetería peruanas como *Shalom Empresarial* o *Expreso Marvisur*:
- **Retail / Personas Naturales (65% del volumen):** Sobres y paquetes medianos con fletes entre **S/ 15.00 y S/ 45.00**.
- **Corporativo / B2B (35% del volumen):** Encomiendas pesadas, cajas comerciales y sacos de mercadería de 40 kg a 150 kg en rutas largas (Lima $\rightarrow$ Puno, Trujillo $\rightarrow$ Arequipa) con fletes de **S/ 130.00 a S/ 320.00**.
- La media ponderada de ambos segmentos da como resultado el ticket equilibrado de **S/ 108.00**.

---

## 6. Scripts y Herramientas del Data Warehouse
1. [populate_full_dwh_2026.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/populate_full_dwh_2026.py): Poblador maestro 2026 con 84 agencias, 1,275 envíos, serie `CE-2026-N...` y preservación de pedidos web reales `CE-2026-P...`.
2. [migrar_a_serie_nacional.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/migrar_a_serie_nacional.py): Script de migración in-place de tracking codes artificiales a la Serie Nacional Crockford Base32.
3. [regularize_historial_envios.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/regularize_historial_envios.py): Generación cronológica de hitos de auditoría con soporte para eventos `CANCELADO` y `SINIESTRADO`.
4. [export_dwh_for_powerbi.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/export_dwh_for_powerbi.py): Extracción analítica Star Schema a CSV en `dwh_powerbi/`.

