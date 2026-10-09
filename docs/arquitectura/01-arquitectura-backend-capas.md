# Arquitectura de Software Backend: Enfoque Modular y Capas Limpias

> **Módulo:** Arquitectura Central del Sistema  
> **Framework:** FastAPI (Python 3.11+) | SQLAlchemy 2.0 | Pydantic v2  
> **Motor de Base de Datos:** PostgreSQL 17 (Producción / Canónica) & SQLite (Entorno Local Ágil)  
> **Metodología:** Spec-Driven Development (SDD) & Clean Layered Architecture  
> **Estado:** 🏛️ **DOCUMENTACIÓN DE ARQUITECTURA VIVA Y VIGENTE**

---

## 1. Visión y Principios Arquitectónicos

El backend de **CargaExpress Perú** está diseñado bajo los principios de **separación de responsabilidades**, **alta cohesión**, **bajo acoplamiento** e **inmutabilidad de eventos críticos**. 

A diferencia de las arquitecturas monolíticas desorganizadas, el backend actúa como un **servidor de dominio puro**, desacoplado de la interfaz de usuario (React Vite) y orientado a la protección estricta de las reglas del negocio de encomiendas y logística interprovincial.

### Principios Fundamentales:
1. **Spec-First (SDD):** Todo endpoint cuenta con un contrato tipado en Pydantic v2 antes de codificar la lógica de negocio.
2. **Fat Services, Thin Controllers:** Los controladores (FastAPI Routers) solo validan HTTP, deserializan esquemas y delegan la ejecución a los servicios (`app/services`). Ninguna regla fiscal o tarifaria se escribe directamente en un router.
3. **Persistencia Transaccional Aislada:** Las operaciones que alteran el estado físico o financiero de una encomienda se ejecutan en transacciones ACID atómicas (`db.commit()` / `db.rollback()`).
4. **Pista de Auditoría por Defecto:** Cualquier mutación sobre envíos, pagos o usuarios genera un hito cronológico inmutable.

---

## 2. Diagrama de Capas de la Aplicación

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   CLIENTES (Frontend React Vite / APIs)                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON / Bearer JWT
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  CAPA 1: PRESENTACIÓN Y ROUTING                        │
│                     [app/api/v1/endpoints/*.py]                        │
│  - Enrutamiento REST (/auth, /envios, /publico, /usuarios, etc.)       │
│  - Inyección de dependencias: Sesión DB (get_db), Roles (require_role) │
│  - Mapeo de Códigos HTTP (200, 201, 400, 401, 403, 404, 422, 500)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA 2: CONTRATOS Y VALIDACIÓN                       │
│                        [app/schemas/*.py]                              │
│  - Pydantic v2 Models: Input DTOs, Output DTOs, Common Responses        │
│  - Validación estricta: regex DNI/RUC, números positivos, extra=forbid │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Datos Limpios y Validados
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                CAPA 3: SERVICIOS Y REGLAS DE NEGOCIO                   │
│                       [app/services/*.py]                              │
│  - EnvioService: Recepción en balanza, despacho, arribo, entrega       │
│  - PublicoService: Motor tarifario volumétrico, tracking con PII mask   │
│  - AuthService: Criptografía Argon2/Bcrypt, 2FA TOTP, sesion_version   │
│  - AuditService: Inserción en auditoria_seguridad y operaciones        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ ORM Entities
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 CAPA 4: ACCESO A DATOS Y PERSISTENCIA                  │
│                     [app/models/*.py, app/db/]                         │
│  - SQLAlchemy 2.0 Declarative Mapped Types                             │
│  - Restricciones FK ON DELETE RESTRICT, checks e inmutabilidad         │
│  - PostgreSQL 17 / SQLite                                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Desglose y Responsabilidad por Directorio

```text
CargaExpressBackend/app/
├── api/
│   ├── deps.py                 # Inyección de dependencias centrales (Auth, DB, Roles, IP cliente)
│   └── v1/
│       ├── router.py           # Agregador del enrutador API v1
│       └── endpoints/          # Controladores HTTP delgados (REST)
│           ├── auth.py         # Login, MFA, refresh tokens, logout
│           ├── envios.py       # Listado, detalle, recepcionar, despachar, arribar
│           ├── publico.py      # Cotizador público, tracking público, agencias
│           ├── usuarios.py     # CRUD de personal, gestión de roles y contraseñas
│           ├── clientes.py     # Búsqueda y gestión de remitentes/destinatarios
│           ├── pagos.py        # Webhooks de pasarela y registro de cobros
│           └── dashboard.py    # KPIs consolidados para supervisión
├── core/
│   ├── config.py               # Variables de entorno cargadas con pydantic-settings (.env)
│   └── security.py             # Funciones criptográficas: bcrypt, pyotp, generación JWT
├── db/
│   ├── base.py                 # DeclarativeBase centralizada de SQLAlchemy
│   └── session.py              # Engine y SessionLocal configurado según DATABASE_URL
├── models/                     # Entidades ORM relacionales
│   ├── agencia.py              # Agencias, ciudades y dependencias operativas
│   ├── cliente.py              # Remitentes y destinatarios (personas y empresas)
│   ├── envio.py                # Envio y HistorialEnvio (núcleo operativo)
│   ├── usuario.py              # Personal interno con control de roles y agencia
│   └── auditoria.py            # AuditoriaSeguridad y AuditoriaOperaciones
├── schemas/                    # Contratos de datos (Pydantic v2)
│   ├── auth.py                 # DTOs de login, 2FA, tokens
│   ├── common.py               # SuccessResponse, ErrorResponse estándar
│   ├── envio.py                # DTOs para envíos, recepción y despacho
│   ├── publico.py              # DTOs para cotización, tracking y pedidos web
│   └── usuario.py              # DTOs de creación, edición y perfil de usuarios
└── services/                   # Dominio y Reglas de Negocio puras
    ├── auth_service.py         # Lógica de credenciales, rate limiting y 2FA
    ├── envio_service.py        # Transiciones de estado del paquete y pesaje
    ├── publico_service.py      # Lógica de tarifario, tracking seguro y pedidos
    ├── email_service.py        # Despacho de notificaciones vía Mailtrap/SMTP
    ├── audit_service.py        # Registro automático de eventos auditables
    └── consulta_documento_service.py # Integración oficial DNI/RUC
```

---

## 4. Flujo de Vida de una Petición HTTP (Request Lifecycle)

1. **Ingreso y Middleware:**
   - La petición ingresa al servidor ASGI Uvicorn.
   - El middleware CORS valida que el origen pertenezca a la lista de permitidos en `settings.BACKEND_CORS_ORIGINS`.
2. **Inyección de Dependencias (`deps.py`):**
   - Si el endpoint es privado, `get_current_user` intercepta el token `Bearer`.
   - Se valida la firma JWT con `settings.SECRET_KEY`.
   - Se consulta al usuario en la base de datos y se compara `sesion_version` (prevención de tokens revocados tras logout).
   - Se ejecuta el guardia `require_role(["ROLES_PERMITIDOS"])` para verificar autorización RBAC.
   - Se abre una sesión de base de datos dedicada mediante `get_db()`.
3. **Validación de Esquema (Pydantic):**
   - El cuerpo de la petición se valida contra el Schema correspondiente.
   - Si los datos son inconsistentes (por ejemplo, dimensiones negativas o DNI con formato erróneo), FastAPI retorna inmediatamente `422 Unprocessable Entity` sin tocar la base de datos.
4. **Capa de Servicio (Lógica de Dominio):**
   - El controlador llama al método estático o de clase en `services`.
   - El servicio aplica las reglas de negocio (ej. verificar que un envío no se despache si no está recepcionado, recalcular tarifa según balanza física).
   - Si una regla es violada, el servicio lanza un `ValueError` con un mensaje descriptivo.
5. **Transacción y Persistencia:**
   - Si todo es exitoso, se ejecutan las sentencias SQL y se registra el hito en `historial_envios`.
   - Se realiza `db.commit()` y `db.refresh()`.
6. **Respuesta Canónica:**
   - Se formatea la respuesta en el wrapper estándar `SuccessResponse[T](success=True, data=..., message=...)` retornando código HTTP `200` o `201`.

---

## 5. Manejo Unificado de Respuestas y Errores

Para garantizar previsibilidad al cliente Frontend y sistemas externos:

### Respuesta Exitosa Estándar:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operación completada exitosamente."
}
```

### Respuesta de Error Estándar:
```json
{
  "detail": "El envío se encuentra en estado 'en_ruta', no puede ser recepcionado nuevamente."
}
```

Los códigos de estado HTTP se respetan estrictamente según RFC 9110:
* **`200 OK`**: Lectura o actualización exitosa.
* **`201 Created`**: Creación exitosa de recurso (nuevo pedido, usuario, apertura de caja).
* **`400 Bad Request`**: Violación de regla de negocio o incompatibilidad de estado.
* **`401 Unauthorized`**: Token ausente, firma inválida o sesión expirada/revocada.
* **`403 Forbidden`**: Usuario autenticado pero sin rol suficiente (RBAC).
* **`404 Not Found`**: El recurso (envío, usuario, cliente) no existe.
* **`422 Unprocessable Entity`**: Error de validación de sintaxis o tipo en Pydantic.
* **`500 Internal Server Error`**: Excepción no controlada del sistema (reportada a logs).
