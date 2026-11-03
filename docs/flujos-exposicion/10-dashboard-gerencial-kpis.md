# 📊 Guía Técnica de Exposición 10: Dashboard Gerencial, KPIs y Métricas Operacionales

Esta guía documenta la arquitectura técnica, las consultas de agregación SQL y la visualización de datos en tiempo real del **Dashboard Operativo y Métricas** (`/admin/dashboard`) en **CargaExpress Perú**.

---

## 1. Visión General del Negocio

El **Dashboard Administrativo** es el centro de comando diario de los directivos, supervisores y personal de CargaExpress.

### Objetivos del Módulo:
1. **Monitoreo Ejecutivo en Tiempo Real:** Visualizar el volumen de paquetes admitidos hoy y la facturación acumulada del turno en Soles (`PEN`).
2. **Alertas Operativas:** Detección inmediata de encomiendas con **pago pendiente** para evitar que salgan a ruta sin cobrar.
3. **Flujo Reciente de Paquetes:** Tabla en vivo con los últimos envíos admitidos, sus orígenes, destinos y estados logísticos.

---

## 2. Diagrama de Conexión de Componentes (Frontend ⇄ Backend ⇄ Base de Datos)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                                   │
│                                                                                        │
│   [Vista Principal: Dashboard.jsx] ──────────► [Servicio: dashboardService.js]         │
│   - Tarjetas KPI (Total, Hoy, Ingresos, Pend.) - GET /api/v1/dashboard/resumen        │
│   - Tabla de Últimos 8 Envíos Recientes        - Inyección de Token Bearer JWT         │
│   - Saludo personalizado y fecha en español                                            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP GET (Headers: Authorization Bearer)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                              BACKEND (FastAPI Core)                                    │
│                                                                                        │
│   [Router: endpoints/dashboard.py] ◄─────────► [Control de Acceso: deps.py]            │
│   - Agrupación temporal: inicio_hoy a mañana   - require_role([ADMIN, SUPERVISOR,      │
│   - Agregaciones: COUNT(), SUM(precio_envio)     CAJERO, ALMACEN, COURIER, TRANSPORT]) │
│   - Subconsultas SQL optimizadas en SQLAlchemy                                         │
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
                             │ estado (registrado, etc.)      │
                             └────────────────────────────────┘
```

---

## 3. Consultas de Agregación y Métricas Calculadas en Servidor

En [`app/api/v1/endpoints/dashboard.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/dashboard.py), el backend no traslada el procesamiento al navegador; ejecuta consultas SQL analíticas de alto rendimiento calculando ventanas temporales en zona horaria UTC:

```python
ahora = datetime.now(timezone.utc)
inicio_hoy = datetime(ahora.year, ahora.month, ahora.day, 0, 0, 0, tzinfo=timezone.utc)
inicio_manana = inicio_hoy + timedelta(days=1)
```

### 1. Total Histórico de Envíos:
$$\text{SELECT COUNT(id) FROM envios;}$$

### 2. Envíos Registrados Hoy:
$$\text{SELECT COUNT(id) FROM envios WHERE creado\_en} \ge \text{inicio\_hoy AND creado\_en} < \text{inicio\_manana;}$$

### 3. Recaudación en Soles de Hoy:
$$\text{SELECT COALESCE(SUM(precio\_envio), 0.0) FROM envios WHERE estado\_pago = 'pagado' AND creado\_en} \ge \text{inicio\_hoy;}$$

### 4. Paquetes con Pago Pendiente:
$$\text{SELECT COUNT(id) FROM envios WHERE estado\_pago = 'pendiente';}$$

### 5. Últimos 8 Envíos Recientes:
$$\text{SELECT * FROM envios ORDER BY creado\_en DESC LIMIT 8;}$$

---

## 4. Payloads de Red Segregados por Rol (API REST)

#### Petición del Cliente:
```http
GET /api/v1/dashboard/resumen HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
```

#### Respuesta JSON Estructurada por Rol (Ejemplo Administrador):
```json
{
  "success": true,
  "data": {
    "rol": "ADMINISTRADOR",
    "fecha_hoy": "miércoles 21 de octubre, 2026",
    "stats": {
      "envios_total": 5,
      "envios_hoy": 2,
      "ingresos_hoy": 37.25,
      "pendientes_pago": 1
    },
    "stats_admin": {
      "recaudacion_total": 84.75,
      "recaudacion_hoy": 37.25,
      "envios_totales": 5,
      "envios_hoy": 2,
      "pendientes_pago": 1,
      "ticket_promedio": 16.95,
      "distribucion_pagos": [
        {"medio": "EFECTIVO", "cantidad": 1, "monto": 20.5, "porcentaje": 38.9},
        {"medio": "YAPE", "cantidad": 2, "monto": 32.25, "porcentaje": 61.1}
      ],
      "estados_embudo": {
        "registrado": 2,
        "recepcionado": 0,
        "en_ruta": 1,
        "en_agencia_destino": 0,
        "entregado": 2
      },
      "top_rutas": [
        {"ruta": "Lima ➔ Arequipa", "total_envios": 3, "ingresos": 52.75},
        {"ruta": "Lima ➔ Cusco", "total_envios": 2, "ingresos": 32.0}
      ]
    },
    "stats_cajero": null,
    "stats_almacen": null,
    "ultimos_envios": [...]
  }
}
```

---

## 5. Módulos de Código Exactos para Mostrar en la Exposición

### Backend:
1. [app/api/v1/endpoints/dashboard.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/dashboard.py):
   * Endpoint `obtener_resumen_dashboard()`: Segrega cálculos SQL automáticos según `current_user.tipo`.
   * Agrupaciones analíticas de `forma_pago`, conteo de embudo de estados y agregación inter-agencias para `top_rutas`.
2. [app/schemas/dashboard.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/schemas/dashboard.py):
   * Contratos Pydantic v2: `AdminStats`, `CajeroStats`, `AlmacenStats`, `DistribucionPagoItem` y `TopRutaItem`.

### Frontend:
1. [src/pages/admin/Dashboard.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/Dashboard.jsx):
   * Vista condicional por rol:
     * **ADMINISTRADOR / SUPERVISOR:** Consola global con facturación total, ticket promedio, embudo de estados logísticos, mix de medios de pago y top 5 rutas interprovinciales.
     * **CAJERO:** Métricas de sede, recaudación del día en ventanilla, paquetes admitidos en balanza y entregas con DNI.
     * **ALMACÉN:** Métricas estrictamente físicas y logísticas (bultos pendientes de estiba, camiones en tránsito, carga en bodega y peso en kg), sin exposición de cifras de dinero (Principio del Menor Privilegio).

---

## 6. Preguntas Frecuentes del Jurado / Evaluador y Respuestas

| Pregunta Típica | Respuesta Técnica y de Negocio |
|:---|:---|
| **¿Por qué el personal de almacén no ve montos de recaudación en el Dashboard?** | *"Por el Principio de Privilegio Mínimo (NIST / OWASP API5). Los operarios de bodega y transportistas gestionan carga física, manifiestos y cubicaje; exponer la facturación monetaria representaría un riesgo innecesario de fuga de información corporativa y potenciales riesgos de seguridad."* |
| **¿Cómo se calculan las rutas más demandadas?** | *"Mediante un JOIN optimizado entre la tabla `envios` y los alias de la tabla `agencias` (origen y destino), agrupando por departamento y ordenando por `COUNT(envios.id) DESC` con límite de 5 registros."* |
| **¿Qué ocurre si un cliente yapea de más en ventanilla?** | *"Se aplica la Política de Paridad de Pago: el cajero valida el Número de Operación en el terminal de la empresa. Si la diferencia es menor o igual a S/ 20, se emite un egreso de caja en ventanilla; si es mayor, se restituye por la misma vía digital (re-yapeo inverso) para evitar estafas de lavado de dinero en efectivo."* |
