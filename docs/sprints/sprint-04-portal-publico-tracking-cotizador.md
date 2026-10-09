# Sprint 04: Ciclo Completo de Envíos - Cotizador Real, Persistencia BDD y Dashboard en Vivo

> **Módulos:** 
> 1. Motor de Cotización y Tarifas (`/api/v1/publico/cotizar`)
> 2. Registro Transaccional de Envíos (`/api/v1/publico/pedidos/registrar`)
> 3. Trazabilidad Pública con Protección PII (`/api/v1/publico/tracking/{codigo}`)
> 4. Sincronización del Dashboard Administrativo (`/api/v1/dashboard/resumen` & `/api/v1/envios`)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (`src/pages/public/` y `src/pages/admin/Dashboard.jsx`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + SQLAlchemy 2.0)  
> **Persistencia:** SQLite Local (`cargaexpress.db`) / PostgreSQL 17 (`cargaexpress.sql`)  
> **Estado del Sprint:** 🚀 **FASE 1 COMPLETADA Y CERTIFICADA E2E** (Portal Público, Registro Invitado y Tracking en BDD) | 📋 **FASE 2 PENDIENTE** (Dashboard Admin en Vivo)

---

## 1. Justificación y Objetivos de Negocio

El objetivo primordial de este sprint es cerrar el **ciclo operativo completo** de CargaExpress Perú:
1. **Calcular con precisión matemática** el costo del servicio en base a peso real y volumétrico.
2. **Generar y persistir el envío** con integridad referencial estricta (clientes, encomienda, tracking correlativo y primer hito histórico).
3. **Reflejar de inmediato el resultado en el Dashboard Administrativo**, sustituyendo los datos simulados (*mocks*) por métricas vivas calculadas desde la base de datos relacional.

```text
┌────────────────────────┐      POST /publico/cotizar      ┌────────────────────────┐
│  Cotizador Web / App   │ ──────────────────────────────> │   FastAPI Backend      │
│  (kg, cm, agencias)    │ <────────────────────────────── │ (Tarifas e IGV SUNAT)  │
└────────────────────────┘         Cálculo Server-Side     └────────────────────────┘
            │                                                           │
            │ POST /publico/pedidos/registrar                           │
            ▼                                                           ▼
┌────────────────────────┐         Transacción ACID        ┌────────────────────────┐
│   Pedido Creado        │ ──────────────────────────────> │  Base de Datos (3NF)   │
│   (CE-2026-NNNNN)      │                                 │  - clientes            │
└────────────────────────┘                                 │  - envios              │
                                                           │  - historial_envios    │
                                                           └────────────────────────┘
                                                                        │
┌────────────────────────┐      GET /dashboard/resumen                  │
│  Dashboard Admin       │ <────────────────────────────────────────────┘
│  (KPIs en vivo e       │      Métricas reales: Ingresos hoy,
│   historial reciente)  │      envíos hoy, pendientes de pago.
└────────────────────────┘
```

---

## 2. Requerimientos Funcionales y Validaciones Estrictas

### 2.1. Motor de Cálculo Tarifario Server-Side (OWASP A04)
* **Prohibición de cálculo en cliente:** El Frontend envía dimensiones y peso; el backend calcula el precio final.
* **Fórmulas Oficiales:**
  * **Peso Volumétrico:**
    $$\text{peso\_volumetrico} = \text{round}\left(\frac{\text{largo\_cm} \times \text{ancho\_cm} \times \text{alto\_cm}}{6000.0}, 2\right)$$
  * **Peso Liquidable (Tarifable):**
    $$\text{peso\_liquidable} = \max(\text{peso\_kg}, \text{peso\_volumetrico})$$
  * **Cálculo de Tarifas:**
    * Tarifa base provincial: `S/ 8.00`
    * Tarifa por peso liquidable: `round(peso_liquidable * 2.50, 2)`
    * Recargo por entrega a domicilio: `S/ 12.00` (solo si `tipo_envio == "agencia_domicilio"`, `0.00` si es agencia a agencia).
    * **Precio Total Bruto:** `tarifa_base + tarifa_peso + recargo_domicilio`.
  * **Desglose Contable SUNAT:**
    * $\text{monto\_subtotal} = \text{round}(\text{precio\_total} / 1.18, 2)$
    * $\text{monto\_igv} = \text{round}(\text{precio\_total} - \text{monto\_subtotal}, 2)$
    * $\text{monto\_descuento} = 0.00$

### 2.2. Validaciones de Entrada (Pydantic v2 Schemas)
* `peso_kg`: Flotante obligatorio, `gt=0.0`, `le=1000.0`.
* `largo_cm`, `ancho_cm`, `alto_cm`: Flotantes obligatorios, `gt=0.0`, `le=300.0`.
* `tipo_envio`: Literal estricto `["agencia_agencia", "agencia_domicilio"]`.
* `agencia_origen_id`, `agencia_destino_id`: Enteros positivos que deben existir y tener `estado == 'habilitado'`.
* **Identificación de Clientes:**
  * DNI: Exactamente 8 dígitos numéricos `^\d{8}$`.
  * RUC: Exactamente 11 dígitos numéricos `^\d{11}$`.
  * Nombres/Razón Social: Entre 2 y 150 caracteres.

### 2.3. Transacción Atómica de Registro (ACID)
1. Iniciar sesión de base de datos con bloqueo transaccional.
2. Buscar cliente remitente por documento en `clientes`; si no existe, crearlo.
3. Buscar cliente destinatario por documento en `clientes`; si no existe, crearlo.
4. Generar código correlativo de tracking único con formato `CE-YYYY-NNNNN` (ejemplo: `CE-2026-00002`).
5. Insertar en la tabla `envios` con `estado = 'registrado'`, `estado_pago = 'pendiente'`, `registrado_web = true`.
6. Insertar en `historial_envios`:
   * `estado = 'registrado'`
   * `descripcion = 'Envío pre-registrado vía portal web'`
   * `agencia_id = agencia_origen_id`
7. Commit atómico. Si ocurre cualquier excepción, ejecutar `rollback` para impedir registros huérfanos.

### 2.4. Protección de Datos Personales en Tracking Público (OWASP API1 / API3)
* Nunca exponer precios contables, documentos de identidad completos ni direcciones exactas a usuarios no autenticados en la API de rastreo.
* Enmascaramiento de nombres: `Juan Carlos Pérez` -> `J*** C***** P****`.
* La dirección de entrega solo expone distrito y provincia.

---

## 3. Matriz de Endpoints del Sprint

| Endpoint | Método | Acceso | Propósito | DTO / Esquema | Estado de Implementación |
| :--- | :---: | :---: | :--- | :--- | :---: |
| `/api/v1/publico/agencias` | `GET` | Público | Lista agencias activas para selectores | `List[AgenciaPublicaDTO]` | ✅ En producción |
| `/api/v1/publico/cotizar` | `POST` | Público | Cálculo matemático server-side | `CotizacionRequest` &rarr; `CotizacionResponse` | ✅ En producción |
| `/api/v1/publico/buscar-cliente/{doc}` | `GET` | Público | Autocompletar clientes frecuentes | `ClientePublicoDTO` | ✅ En producción |
| `/api/v1/publico/pedidos/registrar` | `POST` | Público | Genera y almacena nuevo envío en BDD | `RegistroPedidoRequest` &rarr; `PedidoCreadoResponse` | ✅ En producción |
| `/api/v1/publico/tracking/{codigo}` | `GET` | Público | Consulta de línea de tiempo con PII oculto | `TrackingPublicoResponse` | ✅ En producción |
| `/api/v1/dashboard/resumen` | `GET` | Autenticado | KPIs en vivo (envíos hoy, ingresos, tabla) | `DashboardResumenDTO` | 📋 Próximo paso |
| `/api/v1/envios` | `GET` | Autenticado | Listado administrativo paginado de envíos | `List[EnvioAdminDTO]` | 📋 Próximo paso |

---

## 4. Avances Logrados y Certificación E2E (Fase 1)

En la sesión de desarrollo actual se alcanzó la sincronización total del **Portal de Autoservicio Público**:

1. **Frontend Integrado y Operativo:**
   * [`RegistrarPedido.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/RegistrarPedido.jsx): Stepper de 4 pasos con consulta asíncrona de clientes (RENIEC / base de datos), selectores de agencias operativas activas y cotización en tiempo real.
   * [`PedidoExitoso.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/PedidoExitoso.jsx): Despliegue de código correlativo `CE-2026-NNNNN`, desglose contable (Subtotal, IGV 18%, Total a pagar), copia rápida al portapapeles y botón de impresión de hoja de despacho.
   * [`Tracking.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/Tracking.jsx): Consulta en vivo con línea de tiempo interactiva de hitos históricos y protección estricta PII.
   * [`Cotizador.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/Cotizador.jsx): Enlace directo con traspaso de parámetros a la pantalla de registro de pedidos.

2. **Evidencia de Pruebas Reales (Test de Navegador Automatizado):**
   * Registro completado de la encomienda **`CE-2026-00003`** (4.0 kg, Lima ➔ Arequipa).
   * Cálculo verificado en backend: Tarifa base $S/\ 8.00$ + Tarifa peso $S/\ 10.00$ = **$S/\ 18.00$** (Subtotal: $S/\ 15.25$, IGV: $S/\ 2.75$).
   * Persistencia confirmada en base de datos relacional (`envios` e `historial_envios`) y trazabilidad consultada exitosamente en la vista pública de tracking.

3. **Políticas de Negocio Asociadas:**
   * Se incorporó el documento formal de reglas de negocio para cancelaciones y reembolsos:  
     📄 [01-politicas-cancelaciones-reembolsos.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/01-politicas-cancelaciones-reembolsos.md).

---

## 5. Próximo Paso: Fase 2 (Dashboard Administrativo en Vivo)

1. Implementar el endpoint autenticado `GET /api/v1/dashboard/resumen` con agregaciones SQL (`COUNT(*)`, `SUM(precio_envio)`).
2. Conectar [`Dashboard.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/Dashboard.jsx) con `dashboardService.js` para reemplazar los *mocks* por datos vivos de la base de datos relacional.

