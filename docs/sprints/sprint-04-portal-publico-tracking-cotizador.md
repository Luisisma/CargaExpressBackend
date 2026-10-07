# Sprint 04: Migración del Portal Público, Cotizador, Rastreo (Tracking) y Registro Web

> **Módulo:** Portal Público y Clientes (`/api/v1/publico/*`)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (Vistas en `src/pages/public/`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + SQLAlchemy 2.0)  
> **Monolito de Referencia:** [cargaexpress-](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress-) (`app/modules/publico/`)  
> **Base de Datos:** PostgreSQL 17 ([`cargaexpress.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress.sql))  
> **Estado del Sprint:** 📋 **PLANIFICADO Y ESPECIFICADO (SDD)**

---

## 1. Justificación y Objetivos del Sprint

Tras conectar y certificar el módulo de autenticación (Sprint 03), el siguiente paso en la migración desacoplada es el **Portal Público de Autoservicio**. Este módulo permite a clientes no autenticados interactuar con el sistema sin riesgo para la infraestructura interna ni exposición indebida de datos sensibles.

### Objetivos Clave:
1. **Migrar Modelos SQLAlchemy 2.0:**
   * Crear [`app/models/cliente.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/cliente.py) (`clientes`).
   * Crear [`app/models/envio.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/envio.py) (`envios`, `historial_envios`).
2. **Implementar Endpoints REST Seguros (`/api/v1/publico/*`):**
   * `GET /api/v1/publico/agencias`: Catálogo de agencias activas agrupadas por departamento para los selectores del frontend.
   * `POST /api/v1/publico/cotizar`: Motor de cálculo server-side aplicando peso volumétrico `(L * A * H) / 6000`, tarifa base, peso extra y recargo a domicilio.
   * `GET /api/v1/publico/tracking/{codigo}`: Consulta del estado de envío en tiempo real con línea de tiempo histórica y **enmascaramiento estricto de PII (OWASP API1 / API3)**.
   * `GET /api/v1/publico/buscar-cliente/{documento}`: Consulta de cliente recurrente (DNI/RUC) para autocompletar formularios, protegiendo datos de contacto.
   * `POST /api/v1/publico/pedidos/registrar`: Registro de nuevo envío web con transacción ACID, alta o actualización de clientes y generación correlativa segura del código de tracking (`CE-YYYY-NNNNN`).
3. **Conectar Vistas en Frontend (`CargaExpressFront`):**
   * `src/pages/public/Cotizador.jsx`: Consumir `/api/v1/publico/cotizar` y agencias reales.
   * `src/pages/public/Tracking.jsx`: Consumir `/api/v1/publico/tracking/{codigo}` mostrando hitos reales de la base de datos.
   * `src/pages/public/RegistrarPedido.jsx`: Consumir `/api/v1/publico/pedidos/registrar` y redirigir a `/pedido-exitoso/:tracking`.

---

## 2. Matriz de Endpoints y Controles de Seguridad OWASP

| Endpoint | Método | Acceso | Controles OWASP | DTO / Esquema |
| :--- | :---: | :---: | :--- | :--- |
| `/api/v1/publico/agencias` | `GET` | Público | Solo agencias activas (`estado = 'habilitado'`), proyección de datos públicos sin IDs de auditoría interna. | `AgenciaPublicaResponse` |
| `/api/v1/publico/cotizar` | `POST` | Público | Validación estricta de rangos (`peso > 0`, `dimensiones > 0`), prevención de manipulación de tarifas client-side (OWASP A04). | `CotizacionRequest` -> `CotizacionResponse` |
| `/api/v1/publico/tracking/{codigo}` | `GET` | Público | Sanitización regex `^[A-Za-z0-9-]{8,20}$`, enmascaramiento de nombres y teléfonos (PII Protection), nunca exponer precios ni DNIs. | `TrackingPublicoResponse` |
| `/api/v1/publico/buscar-cliente/{doc}` | `GET` | Público | Validación de formato DNI (8 dígitos) / RUC (11 dígitos). Rate limiting. Enmascaramiento de email. | `ClientePublicoResponse` |
| `/api/v1/publico/pedidos/registrar` | `POST` | Público | Transacción atómica en PostgreSQL, DTO con `extra='forbid'`, cálculo server-side obligatorio de importes contables. | `RegistroPedidoRequest` -> `PedidoCreadoResponse` |

---

## 3. Especificaciones Técnicas Detalladas (SDD)

### 3.1. Cotizador Seguro (`POST /api/v1/publico/cotizar`)

```python
# Fórmula oficial de CargaExpress Perú:
peso_volumetrico = round((largo_cm * ancho_cm * alto_cm) / 6000.0, 2)
peso_liquidable = max(peso_kg, peso_volumetrico)
tarifa_base = 8.00  # Tarifa base provincial
tarifa_peso_adicional = round(peso_liquidable * 2.50, 2)
recargo_domicilio = 12.00 if tipo_envio == "agencia_domicilio" else 0.00
total_bruto = tarifa_base + tarifa_peso_adicional + recargo_domicilio
```

* **DTO Entrada:**
  ```python
  class CotizacionRequest(BaseModel):
      agencia_origen_id: int = Field(..., gt=0)
      agencia_destino_id: int = Field(..., gt=0)
      tipo_envio: Literal["agencia_agencia", "agencia_domicilio"]
      peso_kg: float = Field(..., gt=0, le=1000)
      largo_cm: float = Field(..., gt=0, le=300)
      ancho_cm: float = Field(..., gt=0, le=300)
      alto_cm: float = Field(..., gt=0, le=300)
      model_config = ConfigDict(extra="forbid")
  ```

### 3.2. Rastreo Público de Envíos (`GET /api/v1/publico/tracking/{codigo}`)

* **Protección de Datos Personales (PII):**
  * Remitente `Juan Carlos Pérez` -> `J*** C***** P****`
  * Destinatario `María Gómez` -> `M**** G****`
  * Dirección de entrega solo muestra distrito/provincia, omitiendo la calle exacta.
  * Los montos (`precio_envio`, `monto_subtotal`) **NO** se exponen en la API pública de tracking.
* **Línea de Tiempo:**
  * Lista ordenada de hitos en `historial_envios` con fecha, hito (`REGISTRADO`, `EN_TRANSITO`, `EN_AGENCIA`, `ENTREGADO`) y sede actual.

### 3.3. Registro Web de Encomiendas (`POST /api/v1/publico/pedidos/registrar`)

* **Flujo Transaccional:**
  1. Validar que la agencia de origen y destino existan y estén habilitadas.
  2. Buscar o crear el cliente remitente en `clientes` usando DNI/RUC.
  3. Buscar o crear el cliente destinatario en `clientes`.
  4. Generar el código correlativo de tracking: `CE-YYYY-XXXXX`.
  5. Calcular importes contables en el backend:
     * `monto_subtotal = round(precio_total / 1.18, 2)`
     * `monto_igv = round(precio_total - monto_subtotal, 2)`
     * `monto_descuento = 0.00`
  6. Insertar registro en `envios` con `estado = 'registrado'`, `registrado_web = true`, `estado_pago = 'pendiente'`.
  7. Insertar primer hito en `historial_envios` (`estado = 'registrado'`, descripción: *"Envío pre-registrado vía portal web"*).
  8. Commit atómico. En caso de error, rollback completo sin dejar registros huérfanos.

---

## 4. Plan de Ejecución Paso a Paso

1. **Paso 4.1 (Backend):** Crear modelos SQLAlchemy 2.0 [`app/models/cliente.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/cliente.py) y [`app/models/envio.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/envio.py).
2. **Paso 4.2 (Backend):** Crear esquemas Pydantic v2 en `app/schemas/publico.py`.
3. **Paso 4.3 (Backend):** Implementar servicio `app/services/publico_service.py` con lógica de negocio y cálculos.
4. **Paso 4.4 (Backend):** Crear router y endpoints en `app/api/v1/endpoints/publico.py` y montarlo en `app/api/v1/router.py`.
5. **Paso 4.5 (Backend):** Tests unitarios automatizados con pytest cubriendo cotización, tracking y registro.
6. **Paso 4.6 (Frontend):** Conectar `publicService.js` en `CargaExpressFront` hacia los nuevos endpoints y validar con el servidor en ejecución.
