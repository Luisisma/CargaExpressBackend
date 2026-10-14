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

## 4. Payloads de Red (API REST)

#### Petición del Cliente:
```http
GET /api/v1/dashboard/resumen HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
```

#### Respuesta JSON Estructurada:
```json
{
  "success": true,
  "data": {
    "stats": {
      "envios_total": 5,
      "envios_hoy": 2,
      "ingresos_hoy": 37.25,
      "pendientes_pago": 1
    },
    "ultimos_envios": [
      {
        "id": 5,
        "codigo_tracking": "CE-2026-00005",
        "remitente": "Carlos Alberto Mendoza",
        "destino": "AGENCIA CUSCO - AGENCIA CUSCO",
        "estado": "Entregado",
        "estado_pago": "pagado",
        "precio_envio": 15.5,
        "fecha": "08/10 18:22"
      }
    ],
    "fecha_hoy": "martes 13 de octubre, 2026"
  }
}
```

---

## 5. Módulos de Código Exactos para Mostrar en la Exposición

### Backend:
1. [app/api/v1/endpoints/dashboard.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/dashboard.py):
   * Líneas 16-106: Endpoint `obtener_resumen_dashboard()` con todas las agregaciones `func.count()`, `func.sum()` y límite ordenado descendente.

### Frontend:
1. [src/pages/admin/Dashboard.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/Dashboard.jsx):
   * Líneas 24-39: Función `cargarDashboard()` que sincroniza métricas con el servidor.
   * Líneas 80-160: Tarjetas KPI de resumen gerencial.
   * Líneas 180-280: Tabla reactiva de encomiendas recientes con badges de estado.
2. [src/services/dashboardService.js](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/dashboardService.js):
   * Llamada a `/dashboard/resumen`.

---

## 6. Preguntas Frecuentes del Jurado / Evaluador y Respuestas

| Pregunta Típica | Respuesta Técnica y de Negocio |
|:---|:---|
| **¿Por qué las métricas se calculan en base de datos y no trayendo todos los envíos al frontend?** | *"Por eficiencia y escalabilidad (Principio de Carga Mínima). Si la empresa tuviera 100,000 encomiendas, traerlas al navegador colapsaría el ancho de banda y la memoria del cliente. Enviar `func.count()` y `func.sum()` permite que el motor relacional procese los números en milisegundos y devuelva un payload liviano de menos de 1 KB."* |
| **¿Qué roles tienen permiso para ver el Dashboard?** | *"Todos los roles operativos (`ADMINISTRADOR`, `SUPERVISOR`, `CAJERO`, `ALMACEN`, `COURIER`, `TRANSPORTISTA`) tienen acceso de lectura al Dashboard para conocer el pulso diario de la empresa, pero el menú lateral y las acciones operativas se filtran según sus privilegios RBAC específicos."* |
