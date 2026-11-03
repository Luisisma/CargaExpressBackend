# Sprint 07: Dashboard Ejecutivo, Reportes Analíticos y KPIs Segregados por Rol

> **Módulos:**
> 1. Motor Analítico de Agregaciones SQL (`/api/v1/dashboard/resumen`)
> 2. Consola Ejecutiva Global para **ADMINISTRADOR** y **SUPERVISOR** (Facturación, Métodos de Pago, Top Rutas, Embudo de Estados)
> 3. Consola Operativa para **CAJERO** (Recaudación de Sede, Paquetes en Mostrador, Cobros Pendientes y Entregas con DNI)
> 4. Consola Logística para **ALMACÉN** y **TRANSPORTISTA** (Carga Pendiente de Camión, En Tránsito, Descarga en Bodega y Tonelaje Movilizado)
> 5. Consola de Última Milla para **COURIER** (Ruta Diaria a Domicilio y Cobros Contraentrega)
> 6. Protocolo de Devolución de Sobrepagos en Billeteras Digitales (Yape / Plin)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (`src/pages/admin/Dashboard.jsx`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + SQLAlchemy 2.0 ORM + Pydantic v2)  
> **Estado del Sprint:** 🚀 **EN EJECUCIÓN (SDD)**

---

## 1. Justificación y Objetivos de Negocio

La dirección de **CargaExpress Perú** requiere monitorear la salud operativa y financiera del negocio en tiempo real. Para garantizar la confidencialidad de la información y no abrumar al personal con datos irrelevantes para su función operativa, el sistema implementa **Segregación de Vistas por Rol (Principio del Menor Privilegio - NIST / OWASP API5)**:

1. **Confidencialidad Financiera:** Un operario de almacén o conductor de camión no debe tener visibilidad de la facturación monetaria en Soles ni de los márgenes de ganancia; su foco son los bultos, el peso en kilogramos y los destinos.
2. **Control Local de Ventanilla:** El cajero debe monitorear exclusivamente la recaudación de su agencia y los paquetes listos para entrega en su sede, previniendo distracciones con cifras globales de otras sucursales.
3. **Visión Estratégica 360° para Gerencia:** El Administrador general debe poder evaluar la efectividad logística global, identificar las rutas más demandadas y optimizar los métodos de cobro digital (Yape/Plin vs POS vs Efectivo).

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE DASHBOARDS POR ROL (RBAC)                     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  ROL: ADMINISTRADOR  │      │     ROL: CAJERO      │      │     ROL: ALMACÉN     │
├──────────────────────┤      ├──────────────────────┤      ├──────────────────────┤
│ • Facturación Total  │      │ • Recaudación Sede   │      │ • Pendientes Carga   │
│ • Envíos Nacionales  │      │ • Cobrados hoy       │      │ • En Tránsito (Ruta) │
│ • Embudo de Estados  │      │ • Pendientes Cobro   │      │ • En Bodega Destino  │
│ • Mix Medios de Pago │      │ • Entregas Mostrador │      │ • Kilos Movilizados  │
│ • Top 5 Rutas Perú   │      │ • Cero cifras ajenas │      │ • CERO datos dinero  │
└──────────────────────┘      └──────────────────────┘      └──────────────────────┘
```

---

## 2. Catálogo de Indicadores (KPIs) Esenciales por Rol

### 2.1. Panel de ADMINISTRADOR y SUPERVISOR (Nivel Gerencial)
* **`KPI-ADM-01` Recaudación Total del Día (S/):** Suma acumulada de fletes en estado `pagado` durante la jornada en todas las agencias del país.
* **`KPI-ADM-02` Total Envíos Nacionales:** Volumen consolidado de paquetes registrados, en tránsito y entregados.
* **`KPI-ADM-03` Distribución por Medio de Pago:** Porcentaje y desglose de operaciones entre **Yape**, **Efectivo**, **Tarjeta POS** y **Plin**.
* **`KPI-ADM-04` Embudo Logístico de Estados:** Cantidad de órdenes en:
  $$\text{Registrado} \longrightarrow \text{Recepcionado} \longrightarrow \text{En Ruta} \longrightarrow \text{En Agencia Destino} \longrightarrow \text{Entregado}$$
* **`KPI-ADM-05` Top 5 Rutas de Mayor Demanda:** Parejas Origen ➔ Destino con mayor volumen (ej. Lima ➔ Arequipa, Lima ➔ Cusco).
* **`KPI-ADM-06` Alerta de Paquetes con Pago Pendiente:** Encomiendas admitidas que viajan con cobro contraentrega o saldo pendiente en destino.

### 2.2. Panel de CAJERO (Nivel Operativo de Mostrador)
* **`KPI-CAJ-01` Total Cobrado Hoy en Agencia (S/):** Dinero ingresado en su sede en el turno actual (Efectivo físico + Yape/Plin verificado).
* **`KPI-CAJ-02` Paquetes Recepcionados en Ventanilla:** Cantidad de bultos pesados en balanza y formalizados durante la jornada.
* **`KPI-CAJ-03` Paquetes Pendientes de Cobro:** Envíos pre-registrados en web que aún no se presentan físicamente en mostrador.
* **`KPI-CAJ-04` Entregas Realizadas con DNI:** Clientes que retiraron su paquete en ventanilla tras validación física de identidad (`BR-ENV-04`).

### 2.3. Panel de ALMACENERO y TRANSPORTISTA (Nivel Logístico y Carga)
* **`KPI-ALM-01` Pendientes de Despacho:** Paquetes en bodega origen recepcionados que esperan ser cargados al camión (`en_almacen_origen` / `recepcionado`).
* **`KPI-ALM-02` En Tránsito (En Carretera):** Paquetes estibados en camiones que viajan hacia las sucursales (`en_ruta`).
* **`KPI-ALM-03` Disponibles en Bodega Destino:** Paquetes descargados del camión y listos en estantería para retiro o reparto (`en_agencia_destino`).
* **`KPI-ALM-04` Kilos Totales Movilizados:** Peso físico acumulado (kg) transportado en el turno actual (sin datos financieros).

### 2.4. Panel de COURIER (Nivel Reparto Domiciliario)
* **`KPI-COU-01` Entregas Domiciliarias Asignadas:** Paquetes con modalidad `domicilio` asignados en la hoja de ruta del día.
* **`KPI-COU-02` Entregas Exitosas:** Paquetes entregados en puerta al receptor con firma/DNI.
* **`KPI-COU-03` Pendientes por Visitar:** Envíos restantes en el trayecto urbano.

---

## 3. Política Operativa: Gestión de Sobrepagos en Billeteras Digitales (Yape / Plin)

Para evitar disputas comerciales y prevenir intentos de fraude o lavado de dinero en ventanilla:

1. **Verificación Bancaria Obligatoria:** El cajero nunca aprueba una devolución mirando la pantalla del cliente; verifica el abono real en el terminal de la empresa mediante el **Número de Operación**.
2. **Tolerancia para Devolución en Efectivo ($\le S/\ 20.00$):**
   * Si la diferencia es menor o igual a S/ 20.00, el cajero puede entregar el vuelto en efectivo de forma inmediata.
   * Se genera un registro de egreso justificado en el arqueo de caja con el tracking del envío.
3. **Paridad de Canal Digital ($> S/\ 20.00$):**
   * **Prohibido entregar efectivo de caja** ante excesos mayores a S/ 20.00.
   * La devolución se realiza mediante re-yapeo inverso al mismo número verificado del emisor, o se acredita como `saldo_a_favor` en la cuenta del cliente para próximos despachos.
4. **Comprobante Fiscal Exacto:** La Boleta o Factura se emite estrictamente por el monto real del servicio ($S/\ 18.00$). El exceso no es gravado con IGV ni considerado venta de la empresa.

---

## 4. Contratos de Datos y Schemas (Backend FastAPI)

### Endpoint Principal: `GET /api/v1/dashboard/resumen`
El backend detecta automáticamente el rol del token JWT del usuario (`current_user.rol`) y entrega un payload estructurado y seguro:

```json
{
  "success": true,
  "data": {
    "rol": "ADMINISTRADOR",
    "fecha_hoy": "miércoles 21 de octubre, 2026",
    "stats_admin": {
      "recaudacion_total": 450.50,
      "envios_totales": 12,
      "envios_hoy": 3,
      "pendientes_pago": 2,
      "ticket_promedio": 37.54,
      "distribucion_pagos": [
        {"medio": "efectivo", "cantidad": 5, "monto": 180.00},
        {"medio": "yape", "cantidad": 6, "monto": 220.50},
        {"medio": "tarjeta", "cantidad": 1, "monto": 50.00}
      ],
      "estados_embudo": {
        "registrado": 2,
        "recepcionado": 2,
        "en_ruta": 3,
        "en_agencia_destino": 2,
        "entregado": 3
      },
      "top_rutas": [
        {"ruta": "Lima ➔ Arequipa", "total_envios": 6, "ingresos": 240.00},
        {"ruta": "Lima ➔ Cusco", "total_envios": 4, "ingresos": 160.00}
      ]
    },
    "stats_cajero": {
      "recaudacion_sede_hoy": 220.50,
      "paquetes_admitidos_hoy": 3,
      "pendientes_cobro_sede": 1,
      "entregas_ventanilla_hoy": 2
    },
    "stats_almacen": {
      "pendientes_despacho": 2,
      "en_transito_carretera": 3,
      "en_bodega_destino": 2,
      "kilos_movilizados_hoy": 35.8
    },
    "ultimos_envios": [...]
  }
}
```

---

## 5. Criterios de Aceptación del Sprint
- [ ] Endpoints analíticos responden en $< 100\text{ ms}$ mediante agregaciones SQL optimizadas en SQLAlchemy 2.0.
- [ ] La interfaz en React ([Dashboard.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/Dashboard.jsx)) renderiza automáticamente las métricas correspondientes al rol del usuario conectado.
- [ ] El rol `ALMACEN` y `TRANSPORTISTA` no visualiza ningún valor en Soles (`PEN`) en su interfaz.
- [ ] Se incorporan barras de progreso y comparativas porcentuales visuales en la consola de Gerencia.
