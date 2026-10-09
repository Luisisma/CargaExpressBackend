# Checklist de Seguridad para Migración Backend CargaExpress

Este documento es la **bitácora operativa de validación Spec-Driven Development (SDD)**. Cada vez que se migre o implemente un endpoint en [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend), el desarrollador debe verificar y marcar cada uno de los controles antes de dar por completada la tarea y someter el código a escáneres de seguridad (SAST/DAST).

---

## 1. Criterios de Aceptación Universales por Endpoint (Gate de Seguridad)

Antes de marcar cualquier endpoint como `✅ Completado`, se debe certificar el cumplimiento de este gate:

- [ ] **Validación de Entrada Estricta:** DTO Pydantic v2 con tipos exactos, límites (`le`, `ge`, `max_length`) y `extra='forbid'` configurado.
- [ ] **Sanitización:** Se eliminan espacios en blanco y se validan formatos regex (DNI 8 dígitos, RUC 11 dígitos, celular 9 dígitos).
- [ ] **Prevención de Inyecciones (A03 / SQLi):** Uso exclusivo de consultas ORM parametrizadas con SQLAlchemy 2.0. Cero interpolaciones de cadenas.
- [ ] **Autorización y BOLA (API1 / A01):** Verificación de propiedad del recurso (`user_id` o `agencia_id`) en la cláusula `where()`.
- [ ] **Control de Roles (BFLA / API5):** Restricción de acceso con dependencia `require_role([...])`.
- [ ] **Manejo Seguro de Errores (A05 / API8):** Las excepciones no exponen stack traces ni información interna de la base de datos al cliente.
- [ ] **Registro de Auditoría (A09):** Operaciones de escritura (crear, modificar estado, abrir caja) generan un log estructurado con `user_id`, `client_ip` y `request_id`.
- [ ] **Respuesta Uniforme:** Esquema Envelope `{"success": true, "data": ...}` o `{"success": false, "error": ...}`.

---

## 2. Matriz de Migración y Estado de Módulos

### Módulo 1: Autenticación y Seguridad (`/api/v1/auth/*`) - [Certificado en Sprint 03](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-03-conexion-autenticacion-frontend.md)

| Endpoint | Método | Roles Permitidos | Controles OWASP Clave | Estado | Observaciones |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/api/v1/auth/login` | `POST` | Público | Rate limiting, anti-fuerza bruta, verificación segura bcrypt + soporte legado. Generación QR Base64. | ✅ Certificado E2E | Probado en vivo: emite temp_token + QR si requiere 2FA; tokens directos si no. |
| `/api/v1/auth/2fa` | `POST` | Público (temp token) | Validación TOTP con `pyotp`, emisión de access y refresh tokens. | ✅ Certificado E2E | Probado en vivo: registra 2FA_EXITOSO en auditoria_seguridad y entra al Dashboard. |
| `/api/v1/auth/refresh` | `POST` | Autenticado | Rotación de Refresh Token, verificación de sesion_version contra BD. | ✅ Certificado E2E | Invalida refresh tokens tras cambio de clave o logout. |
| `/api/v1/auth/me` | `GET` | Cualquier rol | Validación de JWT activo, retorno de datos de perfil y agencia. | ✅ Certificado E2E | Protege password_hash y totp_secret (DTO seguro). |
| `/api/v1/auth/2fa/setup` | `POST` | Autenticado | Generación de secreto TOTP Base32 y código QR en Base64. | ✅ Certificado E2E | Flujo de vinculación para Google Authenticator / Authy. |
| `/api/v1/auth/2fa/confirm` | `POST` | Autenticado | Verificación del primer código de 6 dígitos y activación de flag 2FA. | ✅ Certificado E2E | Registra evento ACTIVACION_2FA_EXITOSA en auditoría. |
| `/api/v1/auth/logout` | `POST` | Autenticado | Cierre de sesión y revocación global incrementando sesion_version. | ✅ Certificado E2E | Probado: invalida de inmediato todos los JWT previos del usuario. |

---

### Módulo 2: Portal Público y Clientes (`/api/v1/publico/*`) - [Certificado en Sprint 04](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-04-portal-publico-tracking-cotizador.md)

| Endpoint | Método | Roles Permitidos | Controles OWASP Clave | Estado | Observaciones |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/api/v1/publico/agencias` | `GET` | Público | Consulta agencias activas, ocultar campos de auditoría interna. | ✅ Certificado E2E | Probado en vivo: lista agencias operativas habilitadas en BDD. |
| `/api/v1/publico/cotizar` | `POST` | Público | Cálculo seguro en servidor (A04), peso volumétrico, extra='forbid'. | ✅ Certificado E2E | Probado en vivo: cálculo server-side tarifario y volumétrico SUNAT. |
| `/api/v1/publico/tracking/{codigo}` | `GET` | Público | Enmascaramiento de PII (API1/API3), sanitización regex `^CE-\d{4}-\d{5}$`. | ✅ Certificado E2E | Probado en vivo: línea de tiempo y protección de datos personales. |
| `/api/v1/publico/buscar-cliente/{doc}` | `GET` | Público | Validación DNI/RUC, tasa limitada, protección de contactos. | ✅ Certificado E2E | Probado en vivo: autocompleta clientes frecuentes sin exponer PII. |
| `/api/v1/publico/pedidos/registrar` | `POST` | Público | Transacción ACID, desglose SUNAT, correlativo CE-YYYY-NNNNN. | ✅ Certificado E2E | Probado en vivo: persistió encomienda CE-2026-00003 e hito histórico. |

---

### Módulo 3: Operaciones y Envíos (`/api/v1/admin/envios/*`)

| Endpoint | Método | Roles Permitidos | Controles OWASP Clave | Estado | Observaciones |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/api/v1/admin/envios` | `GET` | `ADMIN`, `CAJERO`, `ALMACENERO` | Filtro obligatorio por `agencia_id` del usuario (BOLA), paginación obligatoria (API4). | ⏳ Pendiente | Admin general puede consultar todas las sedes. |
| `/api/v1/admin/envios/{id}` | `GET` | `ADMIN`, `CAJERO`, `ALMACENERO` | Validación de pertenencia a la agencia del operador (BOLA). | ⏳ Pendiente | Retorna 404 si el envío pertenece a otra sede no autorizada. |
| `/api/v1/admin/envios/nuevo` | `POST` | `ADMIN`, `CAJERO` | Transacción ACID con inserción de clientes, paquete y primer hito. | ⏳ Pendiente | Emisión de comprobante y cálculo de flete en backend. |
| `/api/v1/admin/envios/{id}/cambiar-estado` | `PATCH` | `ADMIN`, `ALMACENERO`, `COURIER` | Transición válida de máquina de estados, registro obligatorio de operador en tracking. | ⏳ Pendiente | Prohibido saltar de REGISTRADO a ENTREGADO directamente. |

---

### Módulo 4: Caja, Cobros y Webhook (`/api/v1/caja/*` y `/api/v1/pagos/*`) - [Especificación Sprint 05](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-05-caja-cobros-recepcion-comprobantes.md)

| Endpoint | Método | Roles Permitidos | Controles OWASP Clave | Estado | Observaciones |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/api/v1/caja/aperturar` | `POST` | `CAJERO`, `ADMIN` | Bloqueo de doble apertura por usuario, validación de saldo `>= 0.00`. | 📋 Especificado SDD | Registra apertura en aperturas_caja en Soles. |
| `/api/v1/caja/estado-actual` | `GET` | `CAJERO`, `ADMIN` | BOLA: Consulta exclusiva del turno del cajero autenticado. | 📋 Especificado SDD | Calcula balance vivo de efectivo, POS y Yape/Plin. |
| `/api/v1/caja/cerrar` | `POST` | `CAJERO`, `ADMIN` | Arqueo final inmutable, cálculo de descuadres. | 📋 Especificado SDD | Cierra la sesión activa del usuario. |
| `/api/v1/caja/cobrar-presencial` | `POST` | `CAJERO`, `ADMIN` | Transacción ACID: Cobro físico + inserción en movimientos_caja + emisión de Boleta/Factura. | 📋 Especificado SDD | Dispara correo 2 (pago confirmado y comprobante). |
| `/api/v1/pagos/webhook-simulado` | `POST` | Público / HMAC | Firma criptográfica HMAC-SHA256 (`X-Webhook-Signature`), validación de idempotencia. | 📋 Especificado SDD | Emula pasarela Culqi/Niubiz y actualiza estado a pagado. |

---

### Módulo 5: Almacén, Guías y Manifiestos (`/api/v1/admin/*`)

| Endpoint | Método | Roles Permitidos | Controles OWASP Clave | Estado | Observaciones |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/api/v1/admin/almacen/stock` | `GET` | `ADMIN`, `ALMACENERO` | Filtro por almacén de la agencia actual, paginación obligatoria. | ⏳ Pendiente | Visualización de estantes y precintos. |
| `/api/v1/admin/guias` | `GET` / `POST` | `ADMIN`, `ALMACENERO` | Control de integridad de guía electrónica y numeración correlativa. | ⏳ Pendiente | Cumplimiento con estructura fiscal estándar. |
| `/api/v1/admin/manifiestos` | `GET` / `POST` | `ADMIN`, `ALMACENERO` | Consolidación de bultos asociados al vehículo/conductor asignado. | ⏳ Pendiente | Verificación de capacidad de carga máxima del camión. |
| `/api/v1/admin/courier/rutas` | `GET` / `PATCH` | `ADMIN`, `COURIER` | Hoja de ruta exclusiva para el repartidor autenticado. | ⏳ Pendiente | Confirmación de entrega con coordenadas o firma. |

---

### Módulo 6: Mantenimiento y Usuarios (`/api/v1/admin/*`)

| Endpoint | Método | Roles Permitidos | Controles OWASP Clave | Estado | Observaciones |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/api/v1/admin/agencias` | `GET` / `POST` / `PUT` | `ADMIN` (escritura) | Validación de ubigeo peruano, dirección y coordenadas. | ⏳ Pendiente | Solo lectura para cajeros/almaceneros. |
| `/api/v1/admin/clientes` | `GET` / `POST` / `PUT` | `ADMIN`, `CAJERO` | Validación estricta DNI/RUC, unicidad de documento de identidad. | ⏳ Pendiente | Prevención de duplicados con constraints en BD. |
| `/api/v1/admin/usuarios` | `GET` / `POST` / `PUT` | `ADMIN` estricto | BFLA (API5): Prohibido acceso a cualquier otro rol. | ⏳ Pendiente | Asignación de rol y reseteo de 2FA supervisado. |

---

## 3. Plantilla de Especificación SDD para Nuevo Endpoint

Al iniciar la migración de un endpoint, copie esta plantilla en el archivo de especificación correspondiente:

```markdown
### Especificación: [MÉTODO] /api/v1/[ruta]

1. **Propósito de Negocio:**
   - Descripción clara del flujo que atiende este endpoint.

2. **Control de Acceso y Roles:**
   - Requiere Token: Sí / No
   - Roles autorizados: [`ADMIN`, `CAJERO`, ...]
   - Restricción de Objeto (BOLA): ¿Cómo se valida la pertenencia del recurso?

3. **Esquema de Entrada (Pydantic DTO):**
   - Nombre: `[Nombre]CreateSchema` / `[Nombre]UpdateSchema`
   - Campos requeridos, tipos y regex de validación:
   - Configuración: `model_config = ConfigDict(extra="forbid")`

4. **Reglas de Negocio y Transaccionalidad:**
   - Validaciones previas a la base de datos.
   - Operaciones atómicas (`session.commit()` / `session.rollback()`).

5. **Respuestas HTTP:**
   - `200` / `201`: Envelope de datos devuelto.
   - `400`: Error de lógica de negocio.
   - `401`: Token ausente o expirado.
   - `403`: Rol o sucursal insuficiente.
   - `404`: Recurso no encontrado o no perteneciente al usuario.
   - `422`: Formato de datos JSON inválido.

6. **Evento de Auditoría:**
   - ¿Qué mensaje estructurado se envía al logger de seguridad?
```
