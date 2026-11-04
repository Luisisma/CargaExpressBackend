# 📊 Guía Técnica de Exposición 10: Dashboard Gerencial, KPIs y Métricas Operacionales

Esta guía documenta la arquitectura técnica, las consultas de agregación SQL, los indicadores de siniestralidad/cancelaciones y la visualización de datos en tiempo real del **Dashboard Operativo y Métricas** (`/admin/dashboard`) en **CargaExpress Perú**.

---

## 1. Visión General del Negocio

El **Dashboard Administrativo** es el centro de comando diario de los directivos, supervisores y personal de CargaExpress.

### Objetivos del Módulo:
1. **Monitoreo Ejecutivo en Tiempo Real:** Visualizar el volumen de paquetes admitidos hoy y la facturación real cobrada en caja en Soles (`PEN`).
2. **Control de Siniestralidad Vial e Incidencias:** Detección inmediata de encomiendas siniestradas en carretera nacional con identificación de los códigos de tracking afectados y monto asegurado en congelamiento.
3. **Control de Desistimiento / Cancelaciones:** Supervisión de la tasa de cancelación de pre-registros web para medir la fricción comercial y abandono.
4. **Alertas Operativas de Cobro:** Detección inmediata de encomiendas con **pago pendiente** para evitar que salgan a ruta sin cobrar.
5. **Flujo Reciente de Paquetes y Trazabilidad:** Tabla en vivo con los últimos envíos admitidos, sus orígenes, destinos y estados logísticos.

---

## 2. Diagrama de Conexión de Componentes (Frontend ⇄ Backend ⇄ Base de Datos)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                                   │
│                                                                                        │
│   [Vista Principal: Dashboard.jsx] ──────────► [Servicio: dashboardService.js]         │
│   - Rejilla de 6 KPIs Ejecutivos (Facturación, Envíos, Ticket, Cobros, Siniestros, Canc)│
│   - Alerta Operativa de Siniestros con Badges de Tracking Clickeables                  │
│   - Pipeline & Ciclo Logístico con Sección de Excepciones e Incidencias               │
│   - Tabla de Últimos 8 Envíos Recientes        - Inyección de Token Bearer JWT         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP GET (Headers: Authorization Bearer)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                              BACKEND (FastAPI Core)                                    │
│                                                                                        │
│   [Router: endpoints/dashboard.py] ◄─────────► [Control de Acceso: deps.py]            │
│   - Agrupación temporal: inicio_hoy a mañana   - require_role([ADMIN, SUPERVISOR,      │
│   - Agregaciones: COUNT(), SUM(precio_envio)     CAJERO, ALMACEN, COURIER, TRANSPORT]) │
│   - Cálculo atómico de Siniestros y Cancelados (agrupación funcional lower(estado))   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
                             ┌────────────────────────────────┐
                             │         TABLA: envios          │
                             ├────────────────────────────────┤
                             │ id, codigo_tracking            │
                             │ creado_en (DATETIME indexado)  │
                             │ precio_envio (NUMERIC)         │
                             │ estado_pago ('pagado'/'pend')  │
                             │ estado (registrado, entregado, │
                             │         siniestrado, anulado)  │
                             └────────────────────────────────┘
```

---

## 3. Rejilla de 6 KPIs Ejecutivos para Administradores

El Dashboard cuenta con una grilla armónica de **6 tarjetas métricas** (`col-6 col-md-4 col-xl-2`):

| Tarjeta KPI | Valor Real Típico | Definición Contable / Operacional | Color |
| :--- | :--- | :--- | :--- |
| **Facturación Total** | `S/ 137,703.10` | Suma de fletes de encomiendas efectivamente cobradas (`estado_pago = 'pagado'`). | Verde |
| **Total Envíos** | `1,275` | Cantidad total de encomiendas procesadas a nivel nacional. | Azul |
| **Ticket Promedio** | `S/ 108.00` | Recaudación cobrada por encomienda ($\frac{137,703.10}{1,275}$). Refleja mezcla equilibrada de sobres (S/ 15) y carga pesada B2B (S/ 230). | Celeste |
| **Órdenes por Cobrar** | `45` | Encomiendas con pago pendiente o pre-registros no abonados. | Rojo / Naranja |
| **Tasa de Siniestros** | `1.41% (18 casos)` | Ratio de siniestralidad vial en carretera nacional respecto al total de encomiendas. Cumple estándar de industria ($< 1.5\%$). | Rojo Crítico |
| **Tasa de Cancelados** | `3.29% (42 casos)` | Ratio de desistimiento o anulación de pre-registros web antes del pago. | Gris / Secundario |

---

## 4. Alerta Operativa de Siniestros en Vivo

Cuando existen encomiendas en estado `siniestrado`:
1. El sistema despliega una barra de alerta roja en la cabecera:
   > **Alerta Operativa:** 18 encomienda(s) declarada(s) en siniestro vial. Carga congelada para liquidación de póliza por un valor estimado de S/ 1,690.26.
2. Muestra los **códigos de tracking específicos afectados** (`CE-2026-N9CBH2A`, `CE-2026-NJ7ADVN`, etc.) como badges clickeables que filtran directamente esa orden.
3. Incluye el botón **"Filtrar Siniestros"** que redirige a `/admin/envios?estado=siniestrado` activando la píldora roja en el módulo de envíos.

---

## 5. Reconciliación Contable: Web Dashboard vs Power BI

Una pregunta fundamental en auditorías y evaluaciones de jurado es la aparente diferencia entre los números de la web y Power BI:

| Métrica | Web Dashboard (Admin) | Power BI Desktop | Causa Técnica |
| :--- | :--- | :--- | :--- |
| **Total Envíos** | **1,275** | **1.275 mil** | **Idéntico (100% de coincidencia)** |
| **Facturación** | **S/ 137,703.10** | **143.401 mil (S/ 143,401.00)** | **S/ 5,697.90 de diferencia exacta** |
| **Ticket Promedio** | **S/ 108.00** | **S/ 112.47** | S/ 4.47 de diferencia |

### Explicación Contable:
* **El Web Dashboard** mide **Recaudación Real Cobrada en Caja**:
  $$\text{SELECT SUM(precio\_envio) FROM envios WHERE estado\_pago = 'pagado'}$$
  Excluye las 45 órdenes pendientes/canceladas que no aportaron dinero a caja.
* **Power BI (por defecto)** suma el flete nominal de **todas** las órdenes registradas (`SUM(fact_envios[total_flete_pen])`), incluyendo los pre-registros pendientes/anulados.
* **Reconciliación:**
  $$\text{S/ } 137,703.10 \text{ (Cobrado en Caja)} + \text{S/ } 5,697.90 \text{ (Flete de las 45 órdenes por cobrar)} = \mathbf{\text{S/ } 143,401.00 \text{ (Total Cotizado)}}$$
* **Medida DAX Oficial para Cuadre al Centavo en Power BI:**
  ```dax
  Facturacion_Cobrada_PEN = 
  CALCULATE(
      SUM(fact_envios[total_flete_pen]),
      fact_envios[estado_pago] = "pagado"
  )
  ```
  Al aplicar esta medida en la tarjeta de Power BI, muestra exactamente **`137.703 mil`**, cuadrando al centavo con el Web Dashboard.

---

## 6. Módulos de Código Exactos

### Backend:
1. [`app/api/v1/endpoints/dashboard.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/dashboard.py):
   * Endpoint `obtener_resumen_dashboard()`: Cálculos en tiempo real de `recaudacion_total`, `tasa_siniestros`, `total_siniestrados`, `monto_siniestrado`, `codigos_siniestrados`, `tasa_cancelados`, `total_cancelados`.
   * Unificación de `cancelado` y `anulado` en `estados_embudo`.
2. [`app/schemas/dashboard.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/schemas/dashboard.py):
   * Contrato Pydantic v2 `AdminStats` con las nuevas métricas operativas.

### Frontend:
1. [`src/pages/admin/Dashboard.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/Dashboard.jsx):
   * Rejilla de 6 KPIs ejecutivos.
   * Banner de alerta con tags de tracking clickeables.
   * Pipeline logístico con subpanel de **Excepciones e Incidencias Registradas**.
   * Retiro del botón de datos demo para depender exclusivamente de scripts auditados.

---

## 7. Preguntas Frecuentes del Jurado / Evaluador

| Pregunta Típica | Respuesta Técnica y de Negocio |
|:---|:---|
| **¿Por qué difiere la facturación del Dashboard Web respecto a Power BI?** | *"El Dashboard Web mide ingresos realizados y cobrados en caja (S/ 137,703.10), protegiendo la liquidez real. Power BI reporta la demanda total cotizada (S/ 143,401.00). La diferencia de S/ 5,697.90 corresponde exactamente al flete de las 45 órdenes pendientes y canceladas que nunca ingresaron a caja."* |
| **¿Qué significa el Ticket Promedio de S/ 108 y es realista?** | *"Es el flete medio cobrado por encomienda. Es 100% realista para transporte interprovincial pesado en Perú (similar a Shalom o Marvisur), ya que el 35% de nuestros clientes son empresas B2B que mueven cajas de 20-50 kg (S/ 135 a S/ 230), equilibrando los sobres pequeños de S/ 15."* |
| **¿Por qué el personal de almacén no ve montos de dinero?** | *"Por el Principio de Mínimo Privilegio (NIST / OWASP API5). Los operarios de bodega gestionan bultos físicos, cubicaje y manifiestos; exponer la facturación representaría un riesgo innecesario de seguridad y confidencialidad."* |
