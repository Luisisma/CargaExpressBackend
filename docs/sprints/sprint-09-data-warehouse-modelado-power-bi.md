# Sprint 09: Data Warehouse (DWH) y Modelado Analítico para Power BI

> **Módulos:**
> 1. Arquitectura de Datos Desacoplada (OLTP vs OLAP)
> 2. Modelo Dimensional de Kimball (Esquema Estrella en PostgreSQL)
> 3. Vistas Materializadas y Vistas SQL Analíticas (`vw_powerbi_*`)
> 4. Conexión DirectQuery / Import mediante conector nativo de PostgreSQL en Power BI Desktop
> 5. Catálogo de Medidas DAX Esenciales  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (PostgreSQL 17 / SQLAlchemy)  
> **BI Engine:** Microsoft Power BI Desktop / Service  
> **Estado del Sprint:** 📋 **ESPECIFICADO Y LISTO PARA EJECUCIÓN (SDD)**

---

## 1. Justificación y Objetivos de Negocio

El crecimiento sostenido de **CargaExpress Perú** exige una capacidad analítica avanzada para directivos y gerencia comercial que permita:
1. **Analítica sin Impacto en Operaciones:** Evitar que las consultas masivas de reportes analíticos ralenticen las operaciones transaccionales diarias (admisión en balanza, lectura láser en bodega y cobros en caja).
2. **Esquema Dimensional Optimizado (Kimball):** Transformar la base de datos relacional normalizada (3NF) en un **Esquema Estrella (Star Schema)** intuitivo y rápido para agregaciones multidimensionales en Power BI.
3. **Mapas de Calor y Rutas Provinciales:** Visualizar en Power BI mapas interactivos de rutas con mayor rentabilidad, densidad de paquetes por departamento y tiempos de tránsito (*Lead Time*).

---

## 2. Arquitectura Dimensional (Esquema Estrella)

```text
                            ┌────────────────────────┐
                            │       dim_tiempo       │
                            ├────────────────────────┤
                            │ tiempo_id (PK: YYYYMMDD│
                            │ fecha, anio, mes,      │
                            │ nombre_mes, trimestre, │
                            │ dia_semana, es_laboral │
                            └───────────┬────────────┘
                                        │
┌────────────────────────┐              │              ┌────────────────────────┐
│      dim_agencia       │              │              │      dim_cliente       │
├────────────────────────┤              ▼              ├────────────────────────┤
│ agencia_id (PK)        │◄─────┌───────────────┐─────►│ cliente_id (PK)        │
│ codigo_agencia         │      │  fact_envios  │      │ tipo_documento (DNI/RUC│
│ nombre_sucursal        │      ├───────────────┤      │ tipo_persona (Nat/Jur) │
│ departamento           │      │ envio_id (PK) │      │ departamento_cliente   │
│ provincia, distrito    │      │ tiempo_id (FK)│      │ es_frecuente (Boolean) │
└────────────────────────┘      │ origen_id (FK)│      └────────────────────────┘
                                │ destino_id(FK)│
┌────────────────────────┐      │ cliente_id(FK)│      ┌────────────────────────┐
│      dim_servicio      │      │ subtotal (S/) │      │       dim_estado       │
├────────────────────────┤◄─────│ igv (S/)      │─────►├────────────────────────┤
│ servicio_id (PK)       │      │ precio_total  │      │ estado_id (PK)         │
│ tipo_envio (ag-ag, etc)│      │ peso_fisico_kg│      │ estado_actual          │
│ tipo_paquete (caja...) │      │ peso_vol_kg   │      │ estado_pago            │
│ es_reparto_domicilio   │      │ lead_time_hrs │      │ canal_pago (Yape, POS) │
└────────────────────────┘      └───────────────┘      └────────────────────────┘
```

---

## 3. Vistas SQL Especializadas para Power BI

En PostgreSQL se implementan vistas analíticas de solo lectura optimizadas con índices:

### 3.1. `vw_powerbi_fact_envios`
```sql
CREATE OR REPLACE VIEW vw_powerbi_fact_envios AS
SELECT 
    e.id AS envio_id,
    e.codigo_tracking,
    TO_CHAR(e.creado_en, 'YYYYMMDD')::INTEGER AS tiempo_id,
    e.agencia_origen_id AS origen_id,
    e.agencia_destino_id AS destino_id,
    e.remitente_id AS cliente_remitente_id,
    e.destinatario_id AS cliente_destinatario_id,
    e.tipo_envio,
    e.tipo_paquete,
    e.peso_kg AS peso_fisico_kg,
    e.peso_volumetrico AS peso_vol_kg,
    e.monto_subtotal AS subtotal_pen,
    e.monto_igv AS igv_pen,
    e.precio_envio AS total_flete_pen,
    e.forma_pago,
    e.estado_pago,
    e.estado AS estado_logistico,
    ROUND(EXTRACT(EPOCH FROM (e.fecha_entrega_real - e.creado_en)) / 3600, 2) AS tiempo_entrega_horas
FROM envios e;
```

### 3.2. `vw_powerbi_dim_agencias`
```sql
CREATE OR REPLACE VIEW vw_powerbi_dim_agencias AS
SELECT 
    a.id AS agencia_id,
    a.codigo_agencia,
    a.nombre AS nombre_agencia,
    a.departamento,
    a.provincia,
    a.distrito,
    a.estado AS estado_operativo
FROM agencias a;
```

---

## 4. Conexión de Power BI Desktop a PostgreSQL

1. **Tipo de Conexión:** Conector nativo de PostgreSQL (`DirectQuery` para datos en vivo o `Import` para modelos en memoria de alta velocidad).
2. **Seguridad y Usuario Dedicado:**
   * Creación de usuario de solo lectura para evitar alteraciones de datos desde Power BI:
     ```sql
     CREATE USER powerbi_reader WITH PASSWORD 'CargaExpress2026_BI_Seguro!';
     GRANT CONNECT ON DATABASE cargaexpress TO powerbi_reader;
     GRANT USAGE ON SCHEMA public TO powerbi_reader;
     GRANT SELECT ON ALL TABLES IN SCHEMA public TO powerbi_reader;
     ```

---

## 5. Catálogo de Medidas DAX Oficiales

* **Facturación Acumulada (S/):**
  ```dax
  Facturacion_Total = SUM(vw_powerbi_fact_envios[total_flete_pen])
  ```
* **Crecimiento Mensual (MoM %):**
  ```dax
  Crecimiento_MoM_% = 
  DIVIDE(
      [Facturacion_Total] - CALCULATE([Facturacion_Total], DATEADD(dim_tiempo[fecha], -1, MONTH)),
      CALCULATE([Facturacion_Total], DATEADD(dim_tiempo[fecha], -1, MONTH))
  )
  ```
* **Tasa de Efectividad de Entrega (%):**
  ```dax
  Efectividad_Entrega_% = 
  DIVIDE(
      CALCULATE(COUNTROWS(vw_powerbi_fact_envios), vw_powerbi_fact_envios[estado_logistico] = "entregado"),
      COUNTROWS(vw_powerbi_fact_envios)
  ) * 100
  ```
* **Tiempo Promedio de Entrega (Horas):**
  ```dax
  Lead_Time_Promedio_Hrs = AVERAGE(vw_powerbi_fact_envios[tiempo_entrega_horas])
  ```
