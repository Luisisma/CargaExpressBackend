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
│                        ESTADO TÉCNICO DEL MÓDULO COURIER                               │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│  🟢 IMPLEMENTADO EN CÓDIGO ACTIVO      │  🟡 PENDIENTE / EN HOJA DE RUTA               │
├────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Rol 'courier' en RBAC y JWT          │ • Vista interactiva de ruta en móvil          │
│ • Campo 'licencia_conducir' en Usuario │ • Endpoint específico 'iniciar-reparto'       │
│ • Foreign Key 'courier_id' en Envíos   │ • Subida Multipart de foto de constancia      │
│ • Columnas 'imagen_evidencia' en DB    │ • Canvas de firma táctil digital en pantalla  │
│ • Recargo por delivery (+S/ 12.00)     │ • Geolocalización GPS en vivo del motorizado  │
│ • Soporte de estado 'en_reparto'       │                                               │
│ • Cierre con DNI y parentesco          │                                               │
└────────────────────────────────────────┴───────────────────────────────────────────────┘
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

## 4. Lo que está Pendiente (En Roadmap para Siguiente Fase)

Para defender el proyecto ante un jurado técnico sin falsear información, estos son los componentes planificados para el siguiente sprint:

### 1. Vista de Hoja de Reparto en Frontend ([`CourierRepartos.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/courier/CourierRepartos.jsx))
* **Estado Actual:** Componente contenedor informativo (plantilla básica de presentación).
* **Pendiente:** Integrar la lista de encomiendas asignadas al motorizado con botones de acción rápida (*"Llamar al cliente"*, *"Marcar no responde"*, *"Entregar"*).

### 2. Endpoint Específico de Asignación y Salida a Ruta
* **Pendiente:** Implementar `POST /api/v1/envios/{id}/iniciar-reparto`:
  * Asignar `envio.courier_id = motorizado_id`.
  * Transicionar el estado de `'en_agencia_destino'` a `'en_reparto'`.
  * Registrar hito en `historial_envios`: *"Paquete en poder del courier para reparto a domicilio."*

### 3. Carga de Archivos de Evidencia (Upload de Fotos)
* **Estado Actual:** Las columnas `imagen_recepcion` e `imagen_evidencia` existen en la base de datos como cadenas de texto.
* **Pendiente:** Crear endpoint `POST /api/v1/envios/{id}/evidencia` que reciba `UploadFile` (FastAPI) y guarde la fotografía del paquete entregado en almacenamiento local o cloud (S3 / Cloudinary).

### 4. Firma Digital Táctil en Navegador
* **Pendiente:** Integrar librería de canvas táctil (ej. `react-signature-canvas`) en el cliente para capturar la firma digitalizada del receptor en la pantalla del celular del motorizado.

---

## 5. Módulos de Código Exactos para Mostrar en la Exposición

Si el jurado consulta por el estado de este módulo:

1. [app/models/envio.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/envio.py):
   * Línea 58: Columna `courier_id`.
   * Líneas 48-49: Columnas `imagen_recepcion` e `imagen_evidencia`.
2. [app/models/usuario.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/usuario.py):
   * Línea 20: Rol `courier` y `transportista`.
   * Línea 22: Columna `licencia_conducir`.
3. [app/services/envio_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py):
   * Línea 140: Validación de precondición `en_reparto` para entrega formal.
4. [app/services/publico_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py):
   * Líneas 27-28 del cotizador: Recargo por entrega a domicilio (S/ 12.00) y recojo (S/ 15.00).
5. [src/pages/admin/courier/CourierRepartos.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/courier/CourierRepartos.jsx):
   * Estructura base de la vista en Frontend.

---

## 6. Preguntas Frecuentes del Jurado y Cómo Defenderlas

| Pregunta Típica | Respuesta Transparente y Técnica |
|:---|:---|
| **¿El courier ya puede salir con una app móvil y tomar fotos?** | *"La arquitectura de backend y base de datos ya está completamente preparada (columnas `courier_id`, `imagen_evidencia`, recargos de delivery en el motor tarifario y soporte del estado `en_reparto`). La captura de foto y la interfaz móvil del motorizado corresponden a la siguiente fase de desarrollo de clientes móviles."* |
| **¿Cómo se calcula el costo de un envío con entrega a domicilio?** | *"El cotizador evalúa el campo `tipo_envio`. Si es `agencia_domicilio`, suma una tarifa plana de S/ 12.00 por última milla al costo base del flete y peso volumétrico, desglosando el 18% de IGV correspondiente."* |
| **¿Por qué decidieron separar Almacén de Courier?** | *"Por especialización operativa: Almacén gestiona bodega y transporte interprovincial pesado en camiones; Courier gestiona la distribución urbana ligera de última milla. Ambos cuentan con roles RBAC independientes en el sistema."* |
