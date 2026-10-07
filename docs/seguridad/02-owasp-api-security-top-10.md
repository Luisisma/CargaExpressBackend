# OWASP API Security Top 10 (2023) - Protección de Endpoints y Conexiones

Este documento define la especificación técnica para blindar los endpoints REST del backend **CargaExpress**, mitigando de forma sistemática los 10 riesgos más críticos del estándar **OWASP API Security Top 10: 2023**.

---

## Matriz de Cumplimiento OWASP API Security Top 10: 2023

| Código | Riesgo API | Escenario en CargaExpress | Estrategia de Mitigación en FastAPI |
| :--- | :--- | :--- | :--- |
| **API1:2023** | **Broken Object Level Authorization (BOLA)** | Un cliente o empleado cambia el ID en `/api/v1/envios/542` y visualiza la encomienda de otro usuario. | Validación de propiedad a nivel de objeto: la consulta SQLAlchemy incluye el filtro del usuario autenticado o de su agencia (`where(Envio.id == id, Envio.agencia_id == current_user.agencia_id)`). |
| **API2:2023** | **Broken Authentication** | Fuga de credenciales, tokens sin expiración, o bypass del segundo factor (2FA). | Flujo de autenticación OAuth2 Bearer con JWT firmado criptográficamente, validación obligatoria de TOTP en `/auth/2fa`, y expiración estricta. |
| **API3:2023** | **Broken Object Property Level Authorization (BOPLA)** | Envío masivo de campos (*Mass Assignment*): un cliente envía `"estado": "ENTREGADO"` o `"es_admin": true` en el JSON de registro. | Esquemas Pydantic diferenciados para Create/Update con `model_config = ConfigDict(extra='forbid')`. Los campos de control de estado se gestionan únicamente por endpoints específicos de cambio de estado. |
| **API4:2023** | **Unrestricted Resource Consumption** | Ataques DoS mediante consultas sin límite de paginación (`limit=999999`) o subida de ficheros pesados. | Paginación obligatoria con tope máximo (`limit: int = Query(default=20, le=100)`), middleware de Rate Limiting por IP/Token, y límite estricto de tamaño de payload HTTP (ej. máx 2MB). |
| **API5:2023** | **Broken Function Level Authorization (BFLA)** | Un cajero envía una petición `POST /api/v1/admin/usuarios` reservada para Administradores Generales. | Dependencias jerárquicas de autorización por rol (`Security(require_role(["ADMIN"]))`) ejecutadas a nivel de router y endpoint antes de la lógica de negocio. |
| **API6:2023** | **Unrestricted Access to Sensitive Business Flows** | Bots automatizados generan miles de cotizaciones o rastrean números de tracking masivos para extraer información comercial. | Rate limiting granular en endpoints públicos (`/publico/cotizar`, `/publico/tracking`), verificación CAPTCHA / Cloudflare Turnstile en registro masivo si se detecta abuso. |
| **API7:2023** | **Server Side Request Forgery (SSRF)** | Envío de URLs manipuladas en webhooks o consultas de servicios externos. | Deshabilitar el procesamiento de URLs externas no controladas; uso de clientes HTTP seguros (`httpx`) con lista blanca estricta de dominios y desactivación de redirecciones automáticas. |
| **API8:2023** | **Security Misconfiguration** | CORS configurado con `Allow-Origins: *`, métodos HTTP no implementados expuestos, o headers de seguridad faltantes. | Middleware de CORS restringido a los orígenes del frontend (`http://localhost:5173`, dominio de producción), headers de seguridad HTTP inyectados automáticamente (`X-Content-Type-Options`, `Content-Security-Policy`, etc.). |
| **API9:2023** | **Improper Inventory Management** | Coexistencia de endpoints huérfanos, versiones obsoletas sin parches (`/api/v0/`) o endpoints de prueba expuestos. | Versionado formal en la URL (`/api/v1/`), esquema OpenAPI centralizado y actualizado automáticamente por FastAPI, y política de descontinuación controlada. |
| **API10:2023** | **Unsafe Consumption of APIs** | Confianza ciega en las respuestas de servicios externos (RENIEC, SUNAT, Pasarelas de Pago). | Validación de esquemas Pydantic en las respuestas recibidas de terceros antes de persistir o procesar la información en la base de datos. |

---

## 1. API1:2023 - Broken Object Level Authorization (BOLA / IDOR)

BOLA es la vulnerabilidad número 1 en APIs modernas. Se produce cuando el servidor no valida si el usuario autenticado tiene derecho legítimo a acceder o manipular un recurso específico identificado por un parámetro (ej. `/api/v1/envios/{id}`).

### Regla de Implementación
1. **Nunca confiar en el ID proporcionado por la URL sin validar contexto:**
   ```python
   # app/api/deps.py o service
   async def get_envio_for_user(
       envio_id: int, 
       current_user: Usuario = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ) -> Envio:
       stmt = select(Envio).where(Envio.id == envio_id)
       
       # Si no es ADMIN GENERAL, se restringe a su agencia
       if current_user.rol != "ADMIN":
           stmt = stmt.where(
               (Envio.agencia_origen_id == current_user.agencia_id) |
               (Envio.agencia_destino_id == current_user.agencia_id)
           )
       
       envio = await db.scalar(stmt)
       if not envio:
           # Retornar 404 para evitar revelación de existencia de recursos
           raise HTTPException(status_code=404, detail="Envío no encontrado")
       return envio
   ```
2. Para endpoints públicos de rastreo (`/api/v1/publico/tracking/{codigo}`), solo se deben retornar datos de estado logístico y fechas, **ocultando datos sensibles** como DNI, teléfonos o precios finales pagados a visitantes no autenticados.

---

## 2. API2:2023 - Broken Authentication (Fallas en la Autenticación de APIs)

### Regla de Implementación
1. **Tokens Bearer Stateless:** Uso exclusivo de JSON Web Tokens (JWT) con claims estándar:
   - `sub`: Identificador único del usuario (ID).
   - `rol`: Rol del usuario en el sistema.
   - `agencia_id`: Sede o agencia asignada.
   - `exp`: Tiempo de expiración estricto (máximo 30 minutos).
   - `iat`: Momento de emisión.
2. **Proceso 2FA en dos etapas:**
   - Paso 1: `POST /api/v1/auth/login` valida usuario y contraseña. Si son correctos y el usuario tiene 2FA habilitado, emite un `temp_token` (vida útil: 5 minutos) con alcance único para `/auth/2fa`.
   - Paso 2: `POST /api/v1/auth/2fa` valida el código TOTP de 6 dígitos junto al `temp_token`. Solo tras el éxito de esta etapa se emite el `access_token` operativo y el `refresh_token`.

---

## 3. API3:2023 - Broken Object Property Level Authorization (BOPLA / Mass Assignment)

Ocurre cuando un atacante envía propiedades no autorizadas en el cuerpo de la petición HTTP (JSON) y el backend las mapea directamente al modelo de base de datos.

### Regla de Implementación
1. **Prohibición de Entrada Adicional en Schemas Pydantic:**
   ```python
   from pydantic import BaseModel, ConfigDict

   class EnvioCreateSchema(BaseModel):
       remitente_dni: str
       destinatario_dni: str
       paquete_peso_kg: float
       agencia_destino_id: int
       
       model_config = ConfigDict(
           extra="forbid",            # Rechaza peticiones con campos no declarados (HTTP 422)
           str_strip_whitespace=True  # Limpieza de espacios en blanco
       )
   ```
2. **Esquemas Segregados para Creación vs Actualización:** Nunca reutilizar el modelo de entidad ORM como esquema de entrada de la API.
3. **Restricción de Modificación de Estado:** El estado de un envío (`REGISTRADO`, `EN_TRANSITO`, `RECIBIDO`, `ENTREGADO`) **no puede** modificarse a través de un simple `PUT /envios/{id}` genérico. Debe existir un endpoint específico (`POST /envios/{id}/cambiar-estado`) con autorización estricta del personal de almacén/reparto.

---

## 4. API4:2023 - Unrestricted Resource Consumption (Consumo No Restringido)

### Regla de Implementación
1. **Paginación Forzada:** Ningún endpoint que devuelva listados (`GET /envios`, `GET /clientes`, `GET /guias`) puede responder sin paginación:
   ```python
   from fastapi import Query

   class PaginationParams:
       def __init__(
           self,
           skip: int = Query(default=0, ge=0),
           limit: int = Query(default=20, ge=1, le=100) # Máximo 100 registros por llamada
       ):
           self.skip = skip
           self.limit = limit
   ```
2. **Rate Limiting:**
   - Endpoints públicos de cotización y rastreo: 30 peticiones por minuto por IP.
   - Endpoint de login: 5 intentos fallidos por minuto por IP.
   - Endpoints administrativos: 120 peticiones por minuto por token de usuario.
3. **Timeouts en Operaciones de Base de Datos:** Establecer `statement_timeout` en PostgreSQL y en el engine de SQLAlchemy para abortar consultas que superen los 5 segundos.

---

## 5. API5:2023 - Broken Function Level Authorization (BFLA)

### Regla de Implementación
1. **Matriz de Control de Acceso Basada en Roles (RBAC):**
   - `ADMIN`: Control total de catálogos, personal, sucursales y reportes.
   - `CAJERO`: Emisión de envíos, cotización, cobro en caja y arqueos de su propio turno.
   - `ALMACENERO`: Recepción de bultos, asignación de precintos, carga de manifiestos y cambio de estado a "En Tránsito".
   - `CONDUCTOR / COURIER`: Hoja de ruta local, confirmación de entrega con firma/foto.
2. Cada endpoint declara sus permisos explícitamente:
   ```python
   @router.post("/usuarios", dependencies=[Depends(require_role(["ADMIN"]))])
   async def crear_usuario(...):
       ...
   ```

---

## 6. API8:2023 - Security Misconfiguration en APIs

### Regla de Implementación
1. **Política de CORS (Cross-Origin Resource Sharing):**
   - Configuración explícita en `main.py`.
   - Prohibido el uso de `allow_origins=["*"]` en producción cuando se manejan credenciales o encabezados de autorización.
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:5173", "https://app.cargaexpress.pe"]
       allow_credentials=True,
       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
       allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
   )
   ```
2. **Restricción de Métodos HTTP (Verb Tampering):** Si un recurso solo admite `GET`, cualquier intento con `POST`, `DELETE` o `HEAD` debe retornar `405 Method Not Allowed`.

---

## 7. API9:2023 - Gestión Inadecuada de Inventario (Inventory Management)

### Regla de Implementación
1. **Prefijo Único de Versión:** Todas las rutas del backend deben iniciar con `/api/v1/`.
2. **Desactivación de Rutas Huérfanas:** Cada endpoint migrado desde el código legacy debe documentarse en el router v1. Las rutas antiguas deben ser desmanteladas o redireccionadas con código `301/308` o `410 Gone`.
3. **Esquema OpenAPI Completo:** Cada endpoint debe tener descripciones claras, códigos de respuesta documentados (`responses={400: ..., 404: ..., 422: ...}`) y etiquetas descriptivas (*tags*).
