# CAPÍTULO 3 – GESTIÓN DEL SERVICIO Y DATA WAREHOUSE

---

## 3.1. Gestión Operativa del Servicio Logístico

La gestión del servicio en **CargaExpress Perú** comprende el conjunto de procesos, reglas de negocio y mecanismos tecnológicos que garantizan la cadena de custodia de las encomiendas, desde su admisión inicial hasta su entrega efectiva y liquidación financiera. El sistema desacopla la operativa transaccional diaria (OLTP) de la capa analítica de toma de decisiones (OLAP).

### 3.1.1. Admisión, Pesaje Oficial y Trazabilidad en Tiempo Real
El ciclo de vida del servicio inicia con la solicitud del cliente (presencial en ventanilla o mediante pre-registro web como usuario invitado). Todo paquete atraviesa un control físico obligatorio en balanza calibrada para determinar el peso gravable (máximo entre peso real en kilogramos y peso volumétrico según fórmula oficial MTC para transporte terrestre: $\frac{\text{Largo (cm)} \times \text{Ancho (cm)} \times \text{Alto (cm)}}{6000}$).

* **Generación de Código de Tracking Único:** Emisión de un identificador alfanumérico irrepetible con formato `CE-2026-XXXXXXX` y código QR para lectura óptica.
* **Transición Automatizada de Estados:** El envío pasa de forma estricta por los estados logísticos:
  1. `REGISTRADO`: Pre-orden web generada o registro en cola de mostrador.
  2. `RECEPCIONADO`: Paquete pesado, cubicado, cobrado y rotulado con ticket de código de barras.
  3. `EN_TRANSITO`: Carga consolidada en camión troncal interprovincial con manifiesto de carga.
  4. `EN_AGENCIA_DESTINO`: Arribo a bodega provincial, descarga y verificación física contra guía de remisión.
  5. `EN_REPARTO`: Asignación a chofer o courier motorizado para despacho a domicilio.
  6. `ENTREGADO`: Recepción conforme del destinatario mediante validación de identidad.

> [!NOTE]
> *Nota: Colocar aquí captura de pantalla del Portal Web de Tracking Público con la línea de tiempo de hitos de auditoría de una encomienda.*

---

### 3.1.2. Servicio Courier de Última Milla con Evidencia Digital (Firma y Foto)
Para las modalidades de entrega a domicilio (`agencia_domicilio` y `domicilio_domicilio`), se implementó el módulo de **Reparto Urbano de Última Milla (Sprint 08)**, diseñado para terminales móviles de los repartidores.

* **Hoja de Ruta Digital:** El repartidor accede a su lista de despachos asignados con geolocalización, teléfono del destinatario y estado de cobranza (pagado vs contraentrega).
* **Protocolo de Entrega con Evidencia Digital:**
  * Captura y validación del documento de identidad oficial (DNI) del receptor.
  * Captura de firma digital manuscrita sobre pantalla táctil mediante Canvas HTML5.
  * Captura fotográfica de evidencia del paquete en la puerta del domicilio codificada en Base64.
  * Cierre instantáneo del ciclo logístico cambiando el estado a `ENTREGADO` y notificando al remitente.

> [!NOTE]
> *Nota: Colocar aquí captura de pantalla de la interfaz móvil del Courier (`CourierRepartos.jsx`) mostrando la captura de firma digital y foto de evidencia.*

---

### 3.1.3. Control de Caja Chica, Arqueo Ciego e Incidencias (Siniestros y Cancelaciones)
El manejo de dinero en mostrador y la gestión de contingencias operativas se rigen bajo estándares de control interno:

* **Turnos de Caja y Arqueo Ciego:**
  * Apertura obligatoria de sesión de ventanilla con saldo base en sencillo (ej: S/ 100.00).
  * Registro de cobros en Efectivo, Billeteras Digitales (Yape / Plin) y Tarjeta POS.
  * **Arqueo Ciego de Cierre:** El cajero ingresa el dinero físico en mano sin conocer el saldo del sistema; el backend calcula automáticamente el cuadre y reporta sobrantes o faltantes.
* **Gestión de Incidencias Operativas:**
  * **Siniestralidad Vial (1.41%):** Protocolo ante asaltos o volcaduras en carreteras interprovinciales. El paquete se marca como `SINIESTRADO`, se congela el tracking con mensaje explicativo al cliente y se activa la provisión para reclamo ante la compañía de seguros.
  * **Cancelaciones y Desistimiento Web (3.29%):** Si el cliente desiste de una pre-orden antes de la admisión física, la orden se anula sin penalidad. Si la anulación ocurre posterior al pago en agencia, se aplica retención de hasta el 10% por gastos administrativos.

---

## 3.2. Arquitectura del Data Warehouse (DWH)

Para habilitar la toma de decisiones sin degradar el rendimiento de la base de datos operacional de PostgreSQL / SQLite, se diseñó e implementó un **Data Warehouse analítico desacoplado**, estructurado bajo las directrices formales de **Ralph Kimball**.

### 3.2.1. Metodología Kimball: Modelo Dimensional en Constelación (Galaxy Schema)
A diferencia de un modelo relacional normalizado (3NF) o de un esquema estrella único monolítico, se implementó una **Constelación de Hechos (Galaxy Schema)**. Esta arquitectura permite convivir a múltiples procesos de negocio con diferente granularidad mediante **Dimensiones Conformadas**:

1. **Estrella 1: Procesos Logísticos de Envíos (`fact_envios`)**
   * *Granularidad:* Una fila por cada encomienda física admitida.
   * *Métricas:* Flete total en Soles, subtotal, IGV 18%, peso real (kg), peso volumétrico y lead time de entrega en horas.
2. **Estrella 2: Tesorería y Movimientos de Mostrador (`fact_caja_movimientos`)**
   * *Granularidad:* Una fila por cada cobro o egreso de dinero en ventanilla.
   * *Métricas:* Importe monetario en Soles y conciliación de aperturas.
3. **Estrella 3: Estado de Resultados, Nómina y Rentabilidad (`fact_pnl_rentabilidad_mes`)**
   * *Granularidad:* Una fila por cada sede provincial y mes del año.
   * *Métricas:* Ingresos de fletes, gasto de planilla de personal, costo de combustible diésel, peajes de ruta, alquiler de locales, Utilidad Neta (EBITDA) y ROI %.
4. **Dimensiones Conformadas Compartidas:**
   * `dim_tiempo`: Dimensión temporal única (año, trimestre, mes, día, fin de semana).
   * `dim_agencia`: Catálogo nacional de 84 agencias en los 25 departamentos.
   * `dim_cliente`: Directorio clasificado entre Personas Naturales (DNI) y Empresas (RUC).
   * `dim_empleado`: Padrón formal de 40 colaboradores con sus roles y escalas salariales.

> [!NOTE]
> *Nota: Colocar aquí el Diagrama del Modelo Dimensional de Power BI (Vista de Relaciones) mostrando la Constelación de Hechos limpia y conectada con relaciones 1 a Varios (1:\*).*

---

### 3.2.2. Pipeline ETL Automatizado con Cobertura en 84 Agencias Nacionales
La extracción, transformación y carga de datos se consolidó en un pipeline modular mediante el script maestro [`export_dwh_for_powerbi.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/export_dwh_for_powerbi.py):

* **Extracción y Validación de Integridad:** El script recorre la base de datos transaccional, valida llaves foráneas y descarta registros huérfanos.
* **Transformación y Codificación:** Genera archivos CSV limpios con codificación **UTF-8 con BOM**, asegurando la lectura correcta de caracteres especiales peruanos (tildes y eñes).
* **Datasets Analíticos Exportados en `dwh_powerbi/`:**
  * `dim_agencia.csv` (84 agencias con ubicación geográfica INEI Ubigeo).
  * `dim_cliente.csv` (Directorio de clientes categorizado B2B vs B2C).
  * `dim_tiempo.csv` (Calendario cronológico completo del año 2026).
  * `dim_empleado.csv` (Nómina de 40 trabajadores con sueldos y cargas de ley).
  * `fact_envios.csv` (1,275 órdenes nacionales con cobertura en las 4 modalidades).
  * `fact_caja_movimientos.csv` (1,228 registros de recaudación de ventanilla).
  * `fact_pnl_rentabilidad_mes.csv` (248 registros mensuales de ingresos, costos y ROI).

---

## 3.3. Cuadro de Mando Integral en Power BI (Dashboards por Rol)

La visualización de datos en **Microsoft Power BI Desktop** se estructuró en una suite de tableros ejecutivos segregados por rol de negocio, garantizando que cada líder acceda a información relevante sin ruido visual:

---

### 3.3.1. Dashboard 1: Visión Gerencial y Expansión Comercial
* **Usuario Objetivo:** Directorio Ejecutivo, Gerente General y Gerente Comercial.
* **Propósito:** Proporcionar una **Torre de Control Estratégica (Single Pane of Glass)** sobre la facturación global, cumplimiento de entregas, penetración geográfica y mix de mercado corporativo.

> [!NOTE]
> *Nota: Colocar aquí el pantallazo de la Página 1: "Visión Gerencial" de Power BI.*

#### Análisis de Métricas y Visuales:
* **Tarjetas KPIs Ejecutivas:**
  * **Facturación Cobrada:** **S/ 137.70 mil Soles** recaudados efectivamente.
  * **Volumen Total:** **1,275 encomiendas** operadas en el año 2026.
  * **Ticket Promedio:** **S/ 108.00 Soles** por encomienda.
  * **Cumplimiento Logístico:** **91.9%** de efectividad de entrega.
  * **Lead Time Promedio:** **39.94 horas** (~1.6 días de ciclo nacional).
* **Auditoría de Contingencias:**
  * **Tasa de Siniestralidad Vial:** **1.41% (18 casos)** en rutas interprovinciales.
  * **Tasa de Cancelación Web:** **3.29% (42 casos)** de pre-registros no concretados.
* **Mapa de Cobertura Nacional:** Visualiza la densidad de facturación a lo largo de las **84 agencias operativas en los 25 departamentos del Perú**, demostrando presencia en las macro-regiones Norte, Centro, Sur y Oriente.
* **Curva de Ventas Mensual 2026:** Refleja el crecimiento sostenido de la demanda con picos estacionales en el mes de Julio (**S/ 26.5 mil** por Fiestas Patrias).
* **Segmentación B2B vs B2C y Modalidades:** Muestra el equilibrio entre Personas Naturales (DNI) y Clientes Corporativos con RUC, así como la preferencia por despacho tradicional (*Agencia a Agencia: 36.9%*) frente a entrega courier (*Agencia a Domicilio: 31.8%*).

---

### 3.3.2. Dashboard 2: Operaciones, Flota y Seguridad Vial
* **Usuario Objetivo:** Jefe de Logística, Supervisor de Almacén Central y Coordinador de Transporte.
* **Propósito:** Supervisar el flujo físico de mercancías, volumen en toneladas, saturación de bodegas y puntos críticos de riesgo en carretera.

> [!NOTE]
> *Nota: Colocar aquí el pantallazo de la Página 2: "Operaciones y Flota" de Power BI.*

#### Análisis de Métricas y Visuales:
* **Tonelaje Total Movilizado:** **17.55 Toneladas (17,552 kg)** de carga transportada.
* **Ranking Operativo Regional (25 Departamentos):** Gráfico de barras extendido a todo lo ancho que clasifica el volumen por departamento: Lima lidera la carga con 142 despachos, seguida de Arequipa (107) y Piura (87), hasta sedes provinciales de menor flujo como Huánuco (28).
* **Pipeline de Estados Logísticos (Donut Chart):** Control del ciclo de custodia: 1,172 paquetes entregados con éxito y 43 encomiendas activas en ruta rodando en carreteras nacionales.
* **Cubicaje de Flota (Treemap):** Clasificación del espacio de carga en bodega: Cajas industriales (733 unidades), Paquetes medianos (186), Sacos agrícolas/textiles (180) y Sobres documentarios (176).
* **Mapa de Riesgo Vial por Departamento:** Identifica las carreteras con incidencias de siniestros: Loreto (3), Huánuco (2), La Libertad (2), Junín (1), Lima (1), Piura (1), permitiendo focalizar la custodia satelital GPS y pólizas de seguro.

---

### 3.3.3. Dashboard 3: Finanzas, Caja y Liquidación SUNAT
* **Usuario Objetivo:** Jefe de Finanzas, Contador General y Auditor Tributario.
* **Propósito:** Auditar el flujo monetario, conciliar pagos digitales vs efectivo, controlar las cuentas por cobrar y liquidar los compromisos fiscales ante la SUNAT.

> [!NOTE]
> *Nota: Colocar aquí el pantallazo de la Página 3: "Finanzas, Caja & SUNAT" de Power BI.*

#### Análisis de Métricas y Visuales:
* **Ecuación de Cierre Contable:**
  $$\text{Base Imponible (S/ 121.53K)} + \text{IGV 18\% (S/ 21.87K)} = \text{Facturación Emitida (S/ 143.40K)}$$
  $$\text{Total Cobrado (S/ 137.70K)} + \text{Cuentas por Cobrar (S/ 5.70K)} = \text{Total Fletes (S/ 143.40K)}$$
* **Mix de Canales de Pago:** Demuestra la modernización de cobros: el **78.2% de los ingresos se encuentra bancarizado y digitalizado** (Yape: 18.2%, Tarjeta POS: 20.2%, Transferencia: 18.7%, Plin: 18.0%), mitigando riesgos de asalto en agencias al reducir el efectivo físico a solo 20.9%.
* **Proyección Tributaria Mensual:** Columnas que muestran mes a mes la base imponible y el 18% de IGV generado para la declaración mensual del formulario PDT 621 ante la SUNAT.
* **Tabla de Auditoría por Región:** Cierre auditado departamento por departamento: Total recaudado en caja de **S/ 137,703.10** y control de las 45 órdenes pendientes por contraentrega (**S/ 5,698.14**).

---

### 3.3.4. Dashboard 4: P&L, Sueldos y Rentabilidad ROI
* **Usuario Objetivo:** Directorio Ejecutivo, Accionistas y Gerencia de Recursos Humanos.
* **Propósito:** Demostrar con rigor contable la rentabilidad operativa neta, controlando la nómina de personal y los costos de flota.

> [!NOTE]
> *Nota: Colocar aquí el pantallazo de la Página 4: "P&L, Sueldos y Rentabilidad (ROI)" de Power BI.*

#### Análisis de Métricas y Visuales:
* **Estado de Ganancias y Pérdidas Consolidado (P&L):**
  * **Facturación Bruta:** **S/ 143.40 mil Soles**.
  * **Costo Operativo Total:** **S/ 108.44 mil Soles**.
  * **Planilla de Sueldos Pagados:** **S/ 49.07 mil Soles**.
  * **UTILIDAD NETA OPERATIVA (EBITDA):** **+S/ 34.96 mil Soles** *(en superávit)*.
  * **RETORNO DE INVERSIÓN (ROI):** **32.23%**.
* **Distribución Salarial por Cargo (Dona):** Desglose del costo de mano de obra: Choferes troncales con licencia A-IIIc (21.7%), Supervisores de sede (19.4%), Personal de almacén y balanza (19.3%), Cajeros de ventanilla (18.1%) y Couriers motorizados (12.3%).
* **Ranking de Utilidad Neta por Región:** Clasificación de sedes superavitarias: Lima genera más de S/ 6.5K de utilidad neta, Arequipa S/ 4.7K, Piura S/ 4.5K e Ica S/ 4.1K.
* **Padrón Oficial de Nómina Laboral:** Tabla con los 40 colaboradores de la empresa detallando nombres, cargo, sede provincial, sueldo base formal (**S/ 76,300.00** total), aporte de EsSalud 9% (**S/ 7,235.80**) y costo empresa total (**S/ 102,107.80** anualizado).
* **Evolución Mensual de Utilidad:** Gráfico de líneas que ilustra la estabilidad financiera del negocio a lo largo de los 11 meses de 2026, con un pico de rentabilidad en Julio (+S/ 5.8K de ganancia).

---

### 3.3.5. Dashboard 5: Tesorería y Arqueos de Ventanilla
* **Usuario Objetivo:** Cajero Principal, Supervisor de Ventanilla y Auditor Interno.
* **Propósito:** Auditar el dinero físico ingresado a los cajones de mostrador y garantizar el cuadre de arqueo ciego diario (Sprint 05 y 08).

> [!NOTE]
> *Nota: Colocar aquí el pantallazo de la Página 5: "Tesorería y Arqueos de Caja" de Power BI.*

#### Análisis de Métricas y Visuales:
* **Recaudación en Ventanilla:** **S/ 137.58 mil Soles** ingresados físicamente por caja registradora.
* **Total de Transacciones:** **1,228 operaciones** de mostrador registradas y auditadas.
* **Ticket Promedio de Caja:** **S/ 112.03 Soles** por operación de cobro.
* **Efectividad de Arqueo (Cuadre):** **99.9% de coincidencia** entre los envíos emitidos y el dinero ingresado a ventanilla, con un descalce temporal mínimo de apenas S/ 124.00 derivado de órdenes en liquidación bancaria.
* **Libro Diario de Tesorería:** Tabla detallada de transacciones con fecha, identificador de movimiento, tipo de cobro (Efectivo / Yape / Plin) y código de tracking asociado.

---

## 3.4. Evaluación de Rentabilidad, Nómina de Personal y Retorno de Inversión (ROI)

### 3.4.1. Análisis del Costo Laboral de 40 Colaboradores y Cargas de Ley (EsSalud 9%)
CargaExpress Perú cumple estrictamente con el marco normativo laboral formal del régimen general de la actividad privada en el Perú:

| Rol Operativo | Cargo Institucional | Sueldo Base (PEN) | Asignación Familiar | EsSalud 9% (Empleador) | Costo Mensual Empresa | N° Colaboradores |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`transportista`** | Chofer Troncal (Licencia MTC A-IIIc) | S/ 2,800.00 | S/ 102.50 | S/ 261.23 | **S/ 3,163.73** | 6 |
| **`supervisor`** | Supervisor de Operaciones de Sede | S/ 2,500.00 | S/ 102.50 | S/ 234.22 | **S/ 2,836.72** | 7 |
| **`courier`** | Repartidor Motorizado Última Milla | S/ 1,550.00 | S/ 102.50 | S/ 148.73 | **S/ 2,096.00** | 6 |
| **`almacen`** | Operador de Almacén y Balanza | S/ 1,450.00 | S/ 102.50 | S/ 139.72 | **S/ 1,971.67** | 10 |
| **`cajero`** | Cajero de Ventanilla y Recepción | S/ 1,350.00 | S/ 102.50 | S/ 130.72 | **S/ 1,844.67** | 10 |
| **`admin`** | Administrador de Sede Central | S/ 3,600.00 | - | S/ 324.00 | **S/ 4,700.00** | 1 |
| **TOTALES** | **Planilla Oficial CargaExpress** | **S/ 76,300.00** | - | **S/ 7,235.80** | **S/ 102,107.80** | **40** |

---

### 3.4.2. Estado de Resultados (P&L): Demostración de Utilidad Neta y Viabilidad del Negocio (32.23% ROI)

El Estado de Ganancias y Pérdidas del ejercicio operativo 2026 demuestra que el modelo de negocio es **sostenible, autofinanciable y altamente rentable**:

```text
========================================================================================
           CARGAEXPRESS PERÚ - ESTADO DE RESULTADOS OPERACIONAL (P&L 2026)
========================================================================================
(+) FACTURACIÓN BRUTA TOTAL (Fletes admitidos):                     S/ 143,401.24  [100.0%]
----------------------------------------------------------------------------------------
(-) COSTOS DIRECTOS DE TRANSPORTE (Combustible Diésel D-50):        S/  25,812.33  [ 18.0%]
(-) COSTOS DIRECTOS DE RUTA (Peajes concesionados MTC):             S/   7,170.09  [  5.0%]
----------------------------------------------------------------------------------------
(=) UTILIDAD BRUTA MARGINAL:                                        S/ 110,418.82  [ 77.0%]
----------------------------------------------------------------------------------------
(-) GASTOS DE PLANILLA OPERATIVA (Sueldos netos pagados):           S/  49,066.10  [ 34.2%]
(-) CARGAS SOCIALES DE LEY (EsSalud 9% + Beneficios sociales):      S/   4,415.95  [  3.1%]
(-) GASTOS FIJOS DE SEDES (Alquiler de agencias y servicios luz/web):S/ 21,980.39  [ 15.3%]
----------------------------------------------------------------------------------------
(=) COSTO TOTAL OPERATIVO (Egresos acumulados):                     S/ 108,444.86  [ 75.6%]
========================================================================================
(=) UTILIDAD NETA OPERATIVA (EBITDA / Ganancia Neta Real):         +S/  34,956.38  [ 24.4%]
========================================================================================
(=) RETORNO SOBRE LA INVERSIÓN (ROI CORPORATIVO):                          32.23%
========================================================================================
```

$$\text{Margen Operativo Neto} = \left( \frac{\text{S/ 34,956.38}}{\text{S/ 143,401.24}} \right) \times 100 = \mathbf{24.38\%}$$
$$\text{ROI Corporativo} = \left( \frac{\text{S/ 34,956.38}}{\text{S/ 108,444.86}} \right) \times 100 = \mathbf{32.23\%}$$

#### Veredicto y Conclusión Financiera:
1. **Superación del Estándar Sectorial:** El margen operativo del **24.38%** y el ROI del **32.23%** superan con creces el promedio del sector logístico en el Perú (que oscila entre el 8% y el 14%), gracias a la optimización de rutas troncales y a la alta participación de cobros digitales sin comisiones excesivas.
2. **Capacidad de Reinversión:** Por cada S/ 100.00 invertidos en operar el servicio, CargaExpress genera **S/ 32.23 Soles de ganancia líquida libre**, lo que permite amortizar la adquisición de nuevos vehículos de flota y financiar la apertura de nuevas sedes en provincias.
3. **Comportamiento del Período en Curso:** La inflexión de la curva en el mes de Noviembre no representa un declive comercial, sino que refleja fielmente el corte parcial del mes en curso, corroborando la autenticidad e integridad de la base de datos empresarial.

