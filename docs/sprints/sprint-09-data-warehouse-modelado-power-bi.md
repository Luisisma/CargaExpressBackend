# Sprint 09: Data Warehouse (DWH) y Modelado Analítico Multirrol para Power BI

> **Módulos:**
> 1. Arquitectura de Datos Desacoplada (OLTP vs OLAP)
> 2. Modelo Dimensional de Kimball (Esquema Estrella en Power BI)
> 3. Pipeline ETL Automatizado con Cobertura Nacional (`scripts/populate_full_dwh_2026.py` y `scripts/export_dwh_for_powerbi.py`)
> 4. Catálogo de Vistas SQL Analíticas (`vw_powerbi_*`) y Datasets Estructurados (`dwh_powerbi/`)
> 5. **Dashboards Especializados Segregados por Rol de Negocio (Gerencia, Operaciones, Finanzas y Courier)**
> 6. **Gestión de Incidencias Operativas: Tasa de Siniestralidad y Cancelaciones por Rol**
> 7. Catálogo Integral de Medidas DAX Oficiales  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (PostgreSQL 17 / SQLite 3 / SQLAlchemy)  
> **BI Engine:** Microsoft Power BI Desktop 2026  
> **Estado del Sprint:** ✅ **ESPECIFICADO, MODELADO Y POBLADO CON 84 AGENCIAS NACIONALES**

---

## 1. Justificación y Objetivos de Negocio

El crecimiento sostenido de **CargaExpress Perú** exige una capacidad analítica avanzada para directivos y gerencia comercial que permita:
1. **Analítica sin Impacto en Operaciones:** Evitar que las consultas analíticas pesadas ralenticen las operaciones transaccionales diarias de ventanilla, balanza y caja (aislamiento OLTP vs OLAP).
2. **Esquema Dimensional Optimizado (Metodología Kimball):** Transformar la base de datos relacional normalizada (3NF) en un **Esquema Estrella (Star Schema)** con tablas de hechos (`fact_envios`, `fact_caja_movimientos`) y dimensiones de contexto (`dim_tiempo`, `dim_agencia`, `dim_cliente`).
3. **Dashboards Segregados por Rol de Negocio:** Proveer tableros especializados donde cada líder acceda a las métricas pertinentes a su responsabilidad sin ruido visual.
4. **Cobertura Nacional Completa:** Datos reales distribuidos en las **84 agencias operativas** a lo largo de los **25 departamentos del Perú**, sin concentraciones artificiales ni sesgos.
5. **4 Modalidades de Servicio Compitiendo:** Modelado equilibrado entre despacho tradicional y última milla:
   * `agencia_agencia` (~38%): Envío tradicional de ventanilla a ventanilla.
   * `agencia_domicilio` (~30%): Admisión en sede y entrega con courier en casa/oficina.
   * `domicilio_agencia` (~18%): Recojo a domicilio corporativo y retiro en sede provincial.
   * `domicilio_domicilio` (~14%): Puerta a puerta (*Door-to-Door* integral).
6. **Estados Vivos para Pruebas Operativas E2E:** Paquetes en etapas activas (`registrado`, `recepcionado`, `en_transito`, `en_agencia_destino`, `en_reparto`, `entregado`).
7. **Control de Incidencias Críticas (Siniestros y Cancelaciones):** Medir formalmente el ratio de siniestralidad vial (asaltos, volcaduras, siniestros de fuerza mayor) y el ratio de desistimiento/cancelación de pre-registros web, asignando la responsabilidad analítica al rol correspondiente.

---

## 2. Arquitectura Dimensional Implementada (Esquema Estrella)

```text
                             ┌────────────────────────┐
                             │       dim_tiempo       │
                             ├────────────────────────┤
                             │ tiempo_id (PK: YYYYMMDD)│
                             │ fecha (ISO Date)       │
                             │ anio, mes_num, dia     │
                             │ nombre_mes, dia_semana │
                             │ trimestre, es_fin_semana│
                             └───────────┬────────────┘
                                         │ 1
                                         │ 
                                         │ * tiempo_id
┌────────────────────────┐       ┌───────▼──────────────┐       ┌────────────────────────┐
│      dim_agencia       │       │     fact_envios      │       │      dim_cliente       │
├────────────────────────┤       ├──────────────────────┤       ├────────────────────────┤
│ agencia_id (PK)        │1     *│ envio_id (PK)        │*     1│ cliente_id (PK)        │
│ codigo_agencia         ├───────┤ origen_id (FK)       ├───────┤ tipo_documento (DNI/RUC│
│ nombre_agencia         │origen │ destino_id (FK)      │remit. │ numero_documento       │
│ departamento           │       │ cliente_remitente(FK)│       │ nombre_cliente         │
│ provincia, distrito    │       │ total_flete_pen (S/) │       │ categoria_cliente      │
│ direccion              │       │ subtotal_pen, igv_pen│       │ (Empresa vs Natural)   │
│ estado_operativo       │       │ peso_fisico_kg       │       └────────────────────────┘
└────────────────────────┘       │ peso_volumetrico_kg  │
                                 │ horas_entrega (Lead) │
                                 │ forma_pago           │       ┌────────────────────────┐
                                 │ estado_logistico     │       │ fact_caja_movimientos  │
                                 └──────────────────────┘       ├────────────────────────┤
                                                                │ movimiento_id (PK)     │
                                                                │ apertura_id (FK)       │
                                                                │ tiempo_id (FK ➔ dim_t) │
                                                                │ tipo_movimiento        │
                                                                │ monto_pen (S/)         │
                                                                │ descripcion            │
                                                                └────────────────────────┘
```

---

## 3. Catálogo de Dashboards Especializados por Rol

Para una presentación profesional ante directivos o jurados evaluadores, la analítica se estructura en **3 páginas/vistas independientes en Power BI**, respondiendo a las preguntas estratégicas de cada actor e integrando los KPIs de incidencias según su competencia:

### Vista 1: Dashboard para Gerencia General & Comercial (Estratégico)
> **Usuario Objetivo:** Director Ejecutivo, Gerente General, Jefe Comercial.  
> **Objetivo:** Monitorear la salud financiera, el volumen de ventas, el crecimiento intermensual, la cuota de mercado corporativo vs personas y la **tasa de desistimiento de clientes (Cancelaciones)**.

| Métrica / Visual | Tipo de Gráfico | Justificación para este Rol |
| :--- | :--- | :--- |
| **Facturación Acumulada (S/)** | Tarjeta KPI | Muestra el ingreso bruto total en Soles (`total_flete_pen`). |
| **Ticket Promedio (S/)** | Tarjeta KPI | Evalúa si captamos encomiendas de alto valor o paquetería menor. |
| **Tasa de Cancelación (%)** | Tarjeta KPI (Alerta) | **[NUEVO]** Mide qué porcentaje de pre-registros fueron anulados por el cliente antes del pago o despacho (meta: < 4%). Permite detectar fricción tarifaria o abandono en la web. |
| **Pérdida por Desistimiento (S/)** | Tarjeta KPI | **[NUEVO]** Monto potencial de fletes cancelados no convertidos en ingresos reales. |
| **Curva de Ventas Ene - Nov 2026** | Gráfico de Líneas | Demuestra la tendencia de expansión y picos estacionales (Día de la Madre, Fiestas Patrias). |
| **Mapa Nacional de Ventas** | Mapa de Perú | Visualiza la densidad de facturación en las 84 sedes de los 25 departamentos. |
| **Participación B2B vs B2C** | Columnas Apiladas | Segmenta cuánto dinero aportan las empresas con RUC frente a personas con DNI. |
| **Slicer de Meses y Trimestres** | Mosaico Interactivo | Permite auditar el rendimiento de cualquier período en 1 clic. |

---

### Vista 2: Dashboard para Jefatura de Logística y Operaciones (Supply Chain & Seguridad Vial)
> **Usuario Objetivo:** Jefe de Operaciones, Supervisor de Almacén Central, Coordinador de Flota y Seguridad Vial.  
> **Objetivo:** Garantizar la promesa de entrega, medir cuellos de botella en tránsito, optimizar la capacidad de carga en camiones, controlar el reparto de última milla y **monitorear la siniestralidad vial en carreteras nacionales**.

| Métrica / Visual | Tipo de Gráfico | Justificación para este Rol |
| :--- | :--- | :--- |
| **Tasa de Cumplimiento Logístico (%)** | Tarjeta KPI | Porcentaje de encomiendas entregadas satisfactoriamente (>85%). |
| **Tasa de Siniestralidad Vial (%)** | Tarjeta KPI (Alerta Crítica) | **[NUEVO]** Porcentaje de encomiendas declaradas en siniestro (accidente, asalto, daño grave). Estándar logístico: < 1.5%. Indicador clave de seguridad de flota. |
| **Lead Time Promedio (Horas)** | Tarjeta KPI | Tiempo medio transcurrido desde admisión en balanza hasta entrega final. |
| **Pipeline de Estados en Vivo** | Gráfico de Anillos | Supervisa cuántos paquetes están en ruta, en almacén de destino, en reparto o con incidencia activa. |
| **Mapa de Calor de Riesgo Vial** | Mapa / Barras por Región | **[NUEVO]** Identifica qué rutas interprovinciales (ej: Lima ➔ Junín / Carretera Central) concentran la mayor cantidad de siniestros o demoras. |
| **Rendimiento por Departamento** | Columnas y Líneas | Cruza el volumen de paquetes recibidos frente a la facturación por región. |
| **Cubicaje y Tipo de Paquete** | Treemap | Distribución del espacio de carga (Cajas industriales, Sacos, Sobres, Paquetes). |
| **Canal de Entrega** | Dona / Barras | Proporción de retiro en sede (*agencia_agencia*) vs reparto courier a domicilio. |

---

### Vista 3: Dashboard para Supervisión Financiera y Cajas (Auditoría & Seguros)
> **Usuario Objetivo:** Jefe de Finanzas, Auditor Interno, Cajero Principal.  
> **Objetivo:** Controlar el flujo monetario, cuadre de turnos, fiscalización de comprobantes SUNAT (Boletas vs Facturas), penetración de billeteras digitales y **provisiones para contingencias / liquidación de seguros**.

| Métrica / Visual | Tipo de Gráfico | Justificación para este Rol |
| :--- | :--- | :--- |
| **Ingresos vs Egresos en Caja** | Barras Agrupadas | Comparativa de entradas operativas frente a salidas registradas en `fact_caja_movimientos`. |
| **Monto Comprometido en Siniestros (S/)** | Tarjeta KPI | **[NUEVO]** Valor comercial total de las encomiendas siniestradas pendientes de indemnización o recupero con la aseguradora. |
| **Mix de Medios de Pago** | Gráfico de Anillos | Participación de canales digitales (Yape, Plin, Tarjeta) frente al Efectivo físico. |
| **Desglose Fiscal (IGV vs Subtotal)** | Gráfico de Columnas | Control contable del 18% de IGV generado para liquidación tributaria. |
| **Alerta de Pagos Pendientes** | Tarjeta KPI | Detección inmediata de encomiendas por cobrar para evitar despachos impagos. |
| **Ingresos por Retención de Cancelaciones (S/)** | Tarjeta KPI | **[NUEVO]** Registro de ingresos por gastos operativos (hasta 10%) en cancelaciones presenciales posteriores al pago. |

---

## 4. Catálogo de Medidas DAX Oficiales

```dax
// ==========================================
// 1. FACTURACIÓN Y VOLUMEN BASE
// ==========================================

// Facturación Bruta Acumulada (Suma simple de los 1,275 envíos cotizados: S/ 143,401.00)
Facturacion_Bruta_Total = SUM(fact_envios[total_flete_pen])

// Facturación Efectivamente Cobrada en Caja / Banco (Conciliación exacta con Web Dashboard: S/ 137,703.10)
Facturacion_Cobrada_PEN = 
CALCULATE(
    SUM(fact_envios[total_flete_pen]),
    fact_envios[estado_pago] = "pagado"
)

// Órdenes por Cobrar (Pendientes en mostrador, contraentrega o no liquidadas: 45 órdenes = S/ 5,697.90)
Ordenes_Por_Cobrar = 
CALCULATE(
    COUNTROWS(fact_envios),
    fact_envios[estado_pago] <> "pagado"
)

// Total de Encomiendas Registradas (1,275 órdenes)
Total_Envios = COUNTROWS(fact_envios)

// Ticket Promedio (Soles por Envío: S/ 108.00 oficial)
Ticket_Promedio_PEN = AVERAGE(fact_envios[total_flete_pen])

// Tiempo Promedio de Tránsito (Lead Time en Horas)
Lead_Time_Promedio_Hrs = AVERAGE(fact_envios[horas_entrega])

// Recaudación Neta en Billeteras Digitales (Yape / Plin)
Recaudacion_Digital_PEN = 
CALCULATE(
    [Facturacion_Total],
    fact_envios[forma_pago] IN {"yape", "plin", "yape_plin"}
)

// ==========================================
// 2. EFECTIVIDAD LOGÍSTICA Y CUMPLIMIENTO
// ==========================================

// Tasa Bruta de Entregas Satisfactorias (%)
Tasa_Entrega_% = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_envios), fact_envios[estado_logistico] = "entregado"),
    COUNTROWS(fact_envios),
    0
) * 100

// Efectividad Logística Neta (excluyendo cancelaciones no imputables a transporte)
Efectividad_Logistica_Neta_% = 
VAR TotalOperables = CALCULATE(COUNTROWS(fact_envios), fact_envios[estado_logistico] <> "cancelado")
VAR TotalEntregados = CALCULATE(COUNTROWS(fact_envios), fact_envios[estado_logistico] = "entregado")
RETURN
DIVIDE(TotalEntregados, TotalOperables, 0) * 100

// ==========================================
// 3. SINIESTRALIDAD OPERATIVA Y VIAL (Operaciones & Seguros)
// ==========================================

// Total de Encomiendas Siniestradas
Total_Siniestrados = 
CALCULATE(
    COUNTROWS(fact_envios),
    fact_envios[estado_logistico] = "siniestrado"
)

// Tasa de Siniestralidad Vial (%)
Tasa_Siniestralidad_% = 
DIVIDE([Total_Siniestrados], [Total_Envios], 0) * 100

// Monto Económico Comprometido en Siniestros (S/)
Monto_Siniestrado_PEN = 
CALCULATE(
    SUM(fact_envios[total_flete_pen]),
    fact_envios[estado_logistico] = "siniestrado"
)

// ==========================================
// 4. DESISTIMIENTO Y CANCELACIONES (Comercial & Finanzas)
// ==========================================

// Total de Encomiendas Canceladas / Anuladas
Total_Cancelados = 
CALCULATE(
    COUNTROWS(fact_envios),
    fact_envios[estado_logistico] = "cancelado"
)

// Tasa de Cancelación / Churn Web (%)
Tasa_Cancelacion_% = 
DIVIDE([Total_Cancelados], [Total_Envios], 0) * 100

// Monto Potencial Cancelado (S/)
Monto_Cancelado_PEN = 
CALCULATE(
    SUM(fact_envios[total_flete_pen]),
    fact_envios[estado_logistico] = "cancelado"
)
```

---

## 5. Sinergia: Dashboard Operativo Web (Admin) vs Data Warehouse (Power BI)

Una duda de diseño clave en la arquitectura empresarial es: **¿Debe el Administrador ver la tasa de cancelados y siniestros en el Dashboard Web del sistema, o solo en Power BI?**

### Decisión de Arquitectura: Modelo Híbrido Complementario

| Dimensión | Dashboard Operativo Web (FastAPI + React) | Data Warehouse Analítico (Kimball + Power BI) |
| :--- | :--- | :--- |
| **Naturaleza** | **Táctico / Operacional en Tiempo Real (OLTP)** | **Estratégico / Histórico Multidimensional (OLAP)** |
| **Propósito para Siniestros** | **Alerta inmediata para acción rápida:** Notifica siniestros reportados **hoy** para contactar de inmediato a la compañía de seguros, bloquear la carga y emitir respuesta al cliente. | **Auditoría de riesgos de ruta:** Analiza correlaciones históricas: ¿qué tramos carreteros o qué meses tienen mayor tasa de asaltos o volcaduras? |
| **Propósito para Cancelaciones** | **Control de flujo diario:** Detecta si hoy hubo cancelaciones masivas que liberen espacio en bodega o anulen comprobantes pendientes. | **Análisis de conversión y funnel:** Mide la tasa de abandono mensual para revisar la política de tarifas de flete. |
| **Frecuencia de Actualización** | Segundos (Event-driven / Live query a PostgreSQL/SQLite). | Diario / Periódico vía Pipeline ETL (`dwh_powerbi/*.csv`). |

### Implementación en el Dashboard Web de Admin:
En el sistema web administrativo (`CargaExpressFront/src/pages/admin/Dashboard.jsx` y `CargaExpressBackend/app/api/v1/endpoints/dashboard.py`):
1. **Tarjeta de Incidencias Operativas:**
   - Un indicador visible para Administradores y Supervisores con el conteo de **Siniestros Activos** y **Cancelaciones del Mes**.
2. **Ampliación del Pipeline Logístico:**
   - En el embudo operativo, además de los 5 estados del camino estándar (`registrado`, `recepcionado`, `en_ruta`, `en_agencia_destino`, `entregado`), se añade una pestaña/alerta de **"Excepciones del Servicio"** que desglosa los envíos cancelados y siniestrados sin mezclarlos con la carga activa.

---

## 6. Pipeline de Datos y Scripts Disponibles

| Script | Propósito | Comando de Ejecución |
| :--- | :--- | :--- |
| [`scripts/populate_full_dwh_2026.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/populate_full_dwh_2026.py) | **Poblador Maestro 2026:** Inyecta más de 500 encomiendas distribuidas en las 84 agencias, modelando entregas exitosas (~92%), cancelaciones pre-despacho (~4.5%) y siniestros viales realistas (~1.5%) con su trazabilidad de hitos. | `python scripts\populate_full_dwh_2026.py` |
| [`scripts/export_dwh_for_powerbi.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/export_dwh_for_powerbi.py) | **Extractor ETL:** Sincroniza y extrae las dimensiones y hechos a `dwh_powerbi/` garantizando integridad referencial para el modelo estrella en Power BI. | `python scripts\export_dwh_for_powerbi.py` |
