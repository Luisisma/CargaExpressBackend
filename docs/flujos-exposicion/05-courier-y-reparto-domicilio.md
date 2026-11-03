# 🛵 Guía Técnica de Exposición 05: Courier, Reparto a Domicilio y Última Milla

Esta guía documenta con **total transparencia técnica y rigor arquitectónico** el estado actual del módulo de **Courier y Reparto a Domicilio (Última Milla)** en **CargaExpress Perú**, delimitando con precisión **lo que está implementado y operativo** frente a **lo que se encuentra pendiente en la hoja de ruta (Roadmap)**.

---

## 1. Visión General del Módulo

El servicio de entrega de última milla abarca las modalidades:
* **Agencia a Domicilio (`agencia_domicilio`):** El remitente entrega el paquete en una agencia origen y un motorizado lo lleva a la puerta del destinatario en la ciudad destino.
* **Domicilio a Domicilio (`domicilio_domicilio`):** Recojo en casa del remitente y entrega directa en la vivienda del destinatario.

---

## 2. Radiografía Técnica: Estado de Implementación Real

Para la sustentación o auditoría de código, el estado del módulo se desglosa así:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ESTADO TÉCNICO DEL MÓDULO COURIER (100% OPERATIVO)              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  🟢 IMPLEMENTADO Y CONECTADO E2E                                                       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • Roles 'courier', 'transportista', 'administrador' y 'supervisor' en RBAC            │
│ • Foreign Key 'courier_id' y columnas 'imagen_evidencia', 'imagen_recepcion' en DB     │
│ • Endpoint 'GET /api/v1/envios/courier/mis-entregas' (filtrado por courier y sede)     │
│ • Endpoint 'POST /api/v1/envios/{id}/iniciar-reparto' con autoasignación inteligente   │
│ • Endpoint 'POST /api/v1/envios/{id}/entregar-domicilio' con desacople a disco local   │
│ • Servicio desacoplado 'CourierService' en 'app/services/courier_service.py'          │
│ • Persistencia física de POD en 'uploads/evidencias/' y montaje de StaticFiles         │
│ • Compresión reactiva de foto en navegador (Canvas HTML5: de 5MB a ~80KB en JPEG 75%) │
│ • Selector y validador estricto de documentos (DNI 8 dígitos, C.E., Pasaporte)         │
│ • Canvas interactivo táctil para firma digital en 'CourierRepartos.jsx'                │
│ • Confirmación de cobranza contraentrega en puerta (efectivo / Yape / Plin)           │
│ • Recargo por delivery (+S/ 12.00) en motor tarifario SUNAT e IATA                     │
│ • Trazabilidad inmutable en 'historial_envios' y 'auditoria_seguridad'                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Lo que SÍ está Construido e Implementado Actualmente

### A. Modelo de Datos y Esquema 3NF ([`app/models/envio.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/envio.py))
La tabla `envios` ya cuenta con toda la infraestructura relacional requerida para soportar entregas motorizadas:

| Columna | Tipo | Implementación Actual |
|:---|:---|:---|
| `courier_id` | `INTEGER (FK -> usuarios.id)` | Vincula la encomienda con el repartidor asignado. |
| `direccion_entrega`| `VARCHAR(300)` | Dirección exacta provista por el remitente para el delivery. |
| `tipo_envio` | `VARCHAR(19)` | Admite `'agencia_domicilio'` y `'domicilio_domicilio'`. |
| `imagen_recepcion`| `VARCHAR(300)` | Campo preparado para almacenar la URL o path de la foto al recibir. |
| `imagen_evidencia`| `VARCHAR(300)` | Campo preparado para almacenar la URL o path de la foto de entrega. |
| `fecha_entrega_real`| `DATETIME` | Registra el timestamp exacto en que se concretó la entrega. |

---

### B. Rol `courier` y RBAC en Backend y Frontend
* **Backend:** En [`app/models/usuario.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/usuario.py) el campo `tipo` acepta `'courier'` y `'transportista'`. Incluye el campo `licencia_conducir` para almacenar el brevete MTC del repartidor.
* **Control de Acceso:** En [`app/api/v1/endpoints/envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py), los endpoints de consulta y entrega validan al rol:
  ```python
  current_user: Usuario = Depends(require_role(["CAJERO", "ADMINISTRADOR", "SUPERVISOR", "COURIER", "ALMACEN"]))
  ```
* **Frontend:** En [`AdminLayout.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/components/layout/AdminLayout.jsx#L70), el menú lateral incluye la sección exclusiva **ENTREGAS** (`/admin/courier`) filtrada para usuarios con rol `courier`.

---

### C. Motor Tarifario y Recargos de Última Milla ([`app/services/publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py))
El cálculo oficial incluye los recargos automáticos por entrega urbana motorizada:

$$\text{Recargo Delivery} = \begin{cases} \text{S/ 12.00} & \text{si } \text{tipo\_envio} \in \{\text{'agencia\_domicilio'}, \text{'domicilio\_domicilio'}\} \\ \text{S/ 0.00} & \text{en envíos agencia a agencia} \end{cases}$$

$$\text{Recargo Recojo} = \begin{cases} \text{S/ 15.00} & \text{si } \text{tipo\_envio} \in \{\text{'domicilio\_agencia'}, \text{'domicilio\_domicilio'}\} \\ \text{S/ 0.00} & \text{en otros casos} \end{cases}$$

---

### D. Soporte del Estado `en_reparto` en el Servicio ([`app/services/envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py#L140))
La máquina de estados del método `EnvioService.entregar()` está expresamente programada para permitir la entrega tanto desde ventanilla como desde ruta de courier:

```python
if envio.estado not in ["en_agencia_destino", "en_reparto"]:
    raise ValueError(f"El envío se encuentra en estado '{envio.estado}'. Debe estar 'en_agencia_destino' o 'en_reparto' para ser entregado.")
```

Al entregarse, se asienta en `historial_envios`:
* Nombre del receptor (`req.nombre_receptor`).
* Documento de identidad (`req.dni_receptor`).
* Vínculo / parentesco (`req.parentesco_o_relacion`).
* Observaciones de la entrega.

---

## 4. Endpoints y Componentes del Flujo E2E Implementados

El flujo de última milla opera de extremo a extremo con los siguientes componentes:

### 1. Vista de Hoja de Reparto en Frontend ([`CourierRepartos.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/courier/CourierRepartos.jsx))
* **Estado:** ✅ **100% Implementado y Conectado**.
* **Capacidades:** Tarjetas reactivas con datos del destinatario, llamada rápida con 1 clic (`tel:`), alertas de cobro contraentrega, filtros por estado (`en_agencia_destino`, `en_reparto`, `entregado`) y buscador.

### 2. Endpoint Específico de Asignación y Salida a Ruta
* **Endpoint:** `POST /api/v1/envios/{identificador}/iniciar-reparto`.
* **Servicio:** [`CourierService.iniciar_reparto`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py).
* **Acciones ACID y Soporte de Roles:**
  * Si el usuario es `COURIER` o `TRANSPORTISTA` sin especificar `courier_id`, se autoasigna su ID.
  * Si el usuario es `ADMINISTRADOR` o `SUPERVISOR` y no provee `courier_id`, el sistema le autoasigna su propio ID de colaborador, permitiendo realizar auditorías, soporte y pruebas operativas inmediatas sin bloqueos.
  * Transiciona el estado de `'en_agencia_destino'` a `'en_reparto'`.
  * Registra hito en `historial_envios`: *"Paquete retirado de bodega e iniciado en ruta de reparto a domicilio..."*.

### 3. Carga y Desacople de Evidencia Digital (POD - Proof of Delivery)
* **Endpoint:** `POST /api/v1/envios/{identificador}/entregar-domicilio`.
* **Servicio:** [`CourierService.entregar_domicilio`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py).
* **Arquitectura de Almacenamiento Desacoplado:**
  * **Problema mitigado:** Guardar texto Base64 crudo en base de datos saturaría el almacenamiento y los backups de PostgreSQL.
  * **Solución técnica implementada:** El método auxiliar `_guardar_evidencia_fisica()` decodifica los bytes de la firma (PNG) y la fotografía (JPG), los guarda físicamente en `uploads/evidencias/{tracking}_{tipo}_{timestamp}.ext` y almacena **únicamente la ruta relativa corta** en las columnas `imagen_evidencia` e `imagen_recepcion` (`VARCHAR(300)`).
  * En [`main.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/main.py) se monta `app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")` para servir los archivos directamente.
  * **Migración a la Nube (GCP):** La arquitectura está desacoplada para que en producción solo se sustituya la escritura en disco local por una subida a bucket de Google Cloud Storage (`gs://cargaexpress-evidencias/`).
* **Acciones ACID:**
  * Valida identidad y documento del receptor (DNI, C.E. o Pasaporte).
  * Liquida el pago contraentrega si estaba pendiente (`estado_pago = 'pagado'`).
  * Transiciona a `'entregado'` y registra timestamp `fecha_entrega_real`.

### 4. Firma Digital Táctil y Compresión de Imagen en Navegador
* **Canvas HTML5 Nativo:** Implementado directamente en React con soporte para trazo táctil con el dedo en teléfonos y puntero en escritorio, con botón de borrado y exportación instantánea a PNG.
* **Compresión Reactiva en Cliente:** Al capturar la foto con la cámara móvil, el frontend la procesa en un Canvas en memoria, redimensionando a un máximo de 1024px y comprimiendo en JPEG al 75%. Esto reduce fotos pesadas de 5 MB a tan solo **~80 KB**, ahorrando el 98% del consumo de datos móviles del repartidor.
* **Selector de Documentos Seguro:** Validador estricto que exige 8 dígitos numéricos para DNI y excluye el uso de RUC corporativo como documento de recepción personal.

---

## 5. Módulos de Código Exactos para Mostrar en la Exposición

Si el jurado consulta por el estado de este módulo:

1. [app/models/envio.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/envio.py):
   * Línea 58: Columna `courier_id`.
   * Líneas 48-49: Columnas `imagen_recepcion` e `imagen_evidencia` (`VARCHAR(300)` para rutas/URLs de archivo).
2. [app/models/usuario.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/usuario.py):
   * Línea 20: Rol `courier` y `transportista`.
   * Línea 22: Columna `licencia_conducir`.
3. [app/services/courier_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py):
   * Líneas 58-95: Decodificación y guardado físico desacoplado en `uploads/evidencias/`.
   * Líneas 215-225: Regla RBAC inteligente para asignación de salida a reparto (`ADMINISTRADOR`, `SUPERVISOR`, `COURIER`).
   * Líneas 315-325: Registro de entrega domiciliaria con liquidación contraentrega y sello temporal.
4. [app/services/publico_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py):
   * Líneas 27-28 del cotizador: Recargo por entrega a domicilio (S/ 12.00) y recojo (S/ 15.00).
5. [src/pages/admin/courier/CourierRepartos.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/courier/CourierRepartos.jsx):
   * Canvas táctil de firma digital, compresión automática de foto en cliente (JPEG 75% max 1024px) y selector estricto de documentos.

---

## 6. Preguntas Frecuentes del Jurado y Cómo Defenderlas

| Pregunta Típica | Respuesta Transparente y Técnica |
|:---|:---|
| **¿El courier ya puede salir con una app móvil y tomar fotos?** | *"Sí, la interfaz responsiva en React permite abrir la cámara con `capture='environment'`, comprime la imagen a ~80 KB en el propio navegador del celular antes de transmitirla, captura la firma digital táctil y el backend guarda el archivo físico en el servidor."* |
| **¿Cómo se almacenan las fotos y firmas para no saturar la base de datos?** | *"Se diseñó un desacople arquitectónico: la base de datos solo almacena rutas relativas `VARCHAR(300)`. Los archivos binarios se persisten físicamente en disco (`uploads/evidencias/`), lo cual permite migrar inmediatamente a Google Cloud Storage (GCP) en producción sin modificar el esquema relacional."* |
| **¿Por qué el campo de receptor no admite RUC?** | *"Porque un RUC pertenece a una persona jurídica que no puede firmar ni recibir físicamente. Por normativa de transporte (MTC) y responsabilidad civil, quien recibe en puerta debe ser una persona natural identificada con su DNI, Carné de Extranjería o Pasaporte."* |
| **¿Cómo se calcula el costo de un envío con entrega a domicilio?** | *"El cotizador evalúa el campo `tipo_envio`. Si es `agencia_domicilio`, suma una tarifa plana de S/ 12.00 por última milla al costo base del flete y peso volumétrico, desglosando el 18% de IGV correspondiente."* |
| **¿Por qué decidieron separar Almacén de Courier?** | *"Por especialización operativa: Almacén gestiona bodega y transporte interprovincial pesado en camiones; Courier gestiona la distribución urbana ligera de última milla. Ambos cuentan con roles RBAC independientes en el sistema."* |
