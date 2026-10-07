# OWASP Top 10 (2021) - Guía de Seguridad para Desarrollo Backend

Este documento establece las especificaciones obligatorias para mitigar las 10 vulnerabilidades críticas de aplicaciones web (**OWASP Top 10: 2021**) en el backend de **CargaExpress**, implementado con **FastAPI**, **SQLAlchemy 2.0** y **PostgreSQL 17**.

---

## Matriz de Cumplimiento OWASP Top 10: 2021

| Código | Categoría OWASP | Riesgo en CargaExpress | Medida de Mitigación Obligatoria en Backend |
| :--- | :--- | :--- | :--- |
| **A01:2021** | **Broken Access Control** (Control de Acceso Roto) | Un cajero accede a finanzas globales o un usuario modifica envíos de otra agencia. | Dependencias de autorización por rol (`deps.py`), verificación de agencia/usuario asignado en cada consulta de base de datos. |
| **A02:2021** | **Cryptographic Failures** (Fallas Criptográficas) | Fuga de contraseñas de personal, tokens JWT débiles o llaves en texto plano. | Hashing de passwords con `bcrypt` / `argon2`, JWT firmado con algoritmo `HS256`/`RS256` y clave secreta de alta entropía desde variables de entorno. |
| **A03:2021** | **Injection** (Inyección SQL / Comandos) | Manipulación de campos de búsqueda (tracking, DNI) para ejecutar SQL malicioso. | Uso estricto del ORM SQLAlchemy 2.0 con consultas parametrizadas. Prohibida la interpolación de cadenas (`f"SELECT... {input}"`). |
| **A04:2021** | **Insecure Design** (Diseño Inseguro) | Falta de límites en cotización o manipulación de importes de flete desde el cliente. | Recálculo forzoso del precio de flete en servidor (`pricing_service.py`). El cliente nunca envía el precio a cobrar. |
| **A05:2021** | **Security Misconfiguration** (Configuración Errónea) | Modo debug activo en producción, CORS abierto con `*`, trazas de error expuestas. | `DEBUG=False` en producción, CORS limitado exclusivamente a los dominios del frontend, middleware para capturar excepciones sin exponer stack traces. |
| **A06:2021** | **Vulnerable and Outdated Components** (Componentes Vulnerables) | Dependencias de Python con vulnerabilidades conocidas (CVEs). | Auditoría de dependencias obligatoria (`pip-audit` o `safety`) y congelamiento estricto de versiones en `requirements.txt`. |
| **A07:2021** | **Identification and Authentication Failures** (Fallas de Autenticación) | Fuerza bruta sobre login de empleados, tokens sin expiración, 2FA eludible. | Rate limiting en `/auth/login`, expiración corta de Access Token (15-30 min), Refresh Token seguro, validación forzosa de 2FA TOTP con `pyotp`. |
| **A08:2021** | **Software and Data Integrity Failures** (Fallas de Integridad) | Deserialización insegura de payloads o manipulación de estados de guías. | Validación estricta con Pydantic v2 en todas las entradas (`schema.model_validate`), transacciones ACID con `db.commit()` y rollback automático ante errores. |
| **A09:2021** | **Security Logging and Monitoring Failures** (Fallas de Registro) | Intentos de intrusión o accesos no autorizados sin registrar en bitácora. | Logger estructurado en formato JSON con registro de eventos críticos (intentos fallidos de login, cambios de estado en envíos, aperturas de caja), enmascarando contraseñas y datos personales. |
| **A10:2021** | **Server-Side Request Forgery (SSRF)** | Solicitudes a servicios externos (APIs RENIEC/SUNAT) manipuladas para acceder a la red interna. | Lista blanca estricta de dominios permitidos para llamadas salientes con `httpx`, timeouts definidos y validación de URLs destino. |

---

## 1. A01:2021 - Control de Acceso Roto (Broken Access Control)

### Regla de Especificación
El backend debe implementar el principio de **Mínimo Privilegio** y **Defensa en Profundidad**:
1. Ningún endpoint administrativo puede depender únicamente de que la ruta esté oculta en el frontend.
2. Cada endpoint protegido debe verificar el token JWT mediante inyección de dependencias:
   ```python
   # app/api/deps.py
   async def get_current_user(...) -> Usuario:
       ...
   async def require_role(allowed_roles: list[str]):
       ...
   ```
3. **Aislamiento por Agencia / Sucursal:** Los usuarios con rol `CAJERO` o `ALMACENERO` solo pueden consultar o alterar registros asociados a su `agencia_id`. Si intentan acceder al registro de otra agencia, el sistema debe responder `403 Forbidden` o `404 Not Found` (para evitar enumeración).

---

## 2. A02:2021 - Fallas Criptográficas (Cryptographic Failures)

### Regla de Especificación
1. **Contraseñas:** Se utilizará exclusivamente `passlib[bcrypt]` o `argon2-cffi` con factor de coste de trabajo adecuado (mínimo 12 rondas para bcrypt).
2. **Tokens JWT:** 
   - Algoritmo: `HS256` o `RS256`. Prohibido el uso de `none`.
   - Duración del token de acceso (`access_token`): máximo **30 minutos**.
   - Secreto de firma (`SECRET_KEY`): mínimo 64 caracteres de alta entropía, proveniente de variables de entorno (`.env`), nunca quemado en el código fuente (*hardcoded*).
3. **Transporte de Datos:** Todo el tráfico debe ser forzado sobre HTTPS (TLS 1.3 recomendado, mínimo TLS 1.2).

---

## 3. A03:2021 - Inyección (Injection)

### Regla de Especificación
1. **Inyección SQL:** Está terminantemente prohibido construir consultas SQL mediante concatenación de strings o formateo `f"{variable}"`.
   - **Correcto (SQLAlchemy 2.0):**
     ```python
     stmt = select(Envio).where(Envio.codigo_seguimiento == codigo_seguimiento)
     result = await session.execute(stmt)
     ```
   - **Prohibido:**
     ```python
     # NUNCA HACER ESTO:
     session.execute(text(f"SELECT * FROM envios WHERE tracking = '{codigo}'"))
     ```
2. **Inyección de Comandos del Sistema:** No se deben invocar funciones como `os.system()` o `subprocess.Popen()` con parámetros provenientes de peticiones HTTP.

---

## 4. A04:2021 - Diseño Inseguro (Insecure Design)

### Regla de Especificación
1. **Cálculo de Precios e Importes:** El cliente web nunca envía el precio final a cobrar en un envío. El backend debe ejecutar la fórmula de tarifario oficial:
   $$\text{Peso Facturable} = \max\left(\text{Peso Físico}, \frac{L \times A \times H}{6000}\right)$$
   y multiplicar por la tarifa base de la ruta entre agencias en `pricing_service.py`.
2. **Generación de Códigos de Seguimiento:** Los códigos de tracking (ej. `CE-2026-XXXXX`) deben ser generados de manera controlada y transaccional, evitando colisiones y patrones fácilmente predecibles sin validación.

---

## 5. A05:2021 - Configuración Errónea de Seguridad (Security Misconfiguration)

### Regla de Especificación
1. **Ambientes Segregados:** La variable `DEBUG` debe ser `False` en cualquier entorno fuera de desarrollo local.
2. **Documentación Swagger / OpenAPI:**
   - En producción, los endpoints `/docs` y `/redoc` deben estar protegidos mediante autenticación o desactivados en la inicialización de FastAPI si las políticas de auditoría lo exigen:
     ```python
     app = FastAPI(docs_url=None if settings.ENVIRONMENT == "production" else "/docs")
     ```
3. **Manejo Centralizado de Excepciones:** No devolver trazas de error de Python (*stack traces*) al cliente. Las respuestas de error deben ser normalizadas bajo el esquema estándar:
   ```json
   {
     "success": false,
     "error": {
       "code": "RESOURCE_NOT_FOUND",
       "message": "El recurso solicitado no existe o no tiene permisos para acceder a él."
     }
   }
   ```

---

## 6. A06:2021 - Componentes Vulnerables y Desactualizados

### Regla de Especificación
1. Bloqueo de versiones en `requirements.txt` con operadores estrictos (`==` o rangos compatibles certificados).
2. Ejecución de análisis de vulnerabilidades en el flujo de CI/CD:
   ```bash
   pip install pip-audit
   pip-audit -r requirements.txt
   ```
3. Mantener actualizadas las versiones de FastAPI, SQLAlchemy y Psycopg a versiones con parches de seguridad activos.

---

## 7. A07:2021 - Fallas de Identificación y Autenticación

### Regla de Especificación
1. **Protección contra Fuerza Bruta:** Implementar límite de tasa de solicitudes (*rate limiting*) sobre `/api/v1/auth/login` (máximo 5 intentos fallidos por minuto por IP/usuario).
2. **Mecanismo 2FA Obligatorio para Personal:**
   - La autenticación de administradores y cajeros requiere dos fases: contraseña válida + código TOTP de 6 dígitos (`pyotp`).
   - El token de sesión final solo se emite cuando la fase 2FA ha sido validada satisfactoriamente.
3. **Invalidación de Sesión:** Mecanismo de revocación o lista negra de Refresh Tokens para logout efectivo.

---

## 8. A08:2021 - Fallas en Integridad de Software y Datos

### Regla de Especificación
1. **Validación de Tipos y Datos de Entrada:** Toda entrada JSON debe ser validada contra un modelo Pydantic v2 antes de llegar a la lógica de negocio o base de datos.
2. **Transaccionalidad en Operaciones Críticas:** Registrar un envío implica inserciones simultáneas (remitente, destinatario, paquete, guía, hito de tracking inicial). Estas operaciones deben ejecutarse en un bloque transaccional atómico:
   ```python
   try:
       # operaciones SQLAlchemy
       await session.commit()
   except Exception:
       await session.rollback()
       raise
   ```

---

## 9. A09:2021 - Fallas en Registro y Monitoreo de Seguridad

### Regla de Especificación
1. **Eventos que DEBEN registrarse:**
   - Inicios de sesión exitosos y fallidos (con IP y User-Agent).
   - Intentos de acceso denegados (código HTTP 403).
   - Aperturas, movimientos y cierres de caja.
   - Cambios de estado de encomiendas (especialmente anulaciones o entregas).
2. **Información Prohibida en Logs:**
   - Contraseñas en texto plano o hashes.
   - Tokens JWT completos.
   - Números de tarjetas o códigos CVV.
   - Claves privadas o credenciales de servicios externos.

---

## 10. A10:2021 - Falsificación de Petición del Lado del Servidor (SSRF)

### Regla de Especificación
1. Cuando el backend realice consultas HTTP salientes (por ejemplo, a APIs externas de consulta de DNI/RUC o geolocalización):
   - La URL de destino no debe ser suministrada arbitrariamente por el usuario.
   - Solo se deben consumir endpoints definidos en el archivo de configuración central (`settings.RENIEC_API_URL`, etc.).
   - Bloquear peticiones dirigidas a `localhost`, `127.0.0.1`, `169.254.169.254` (metadata cloud) o rangos de red privada (`10.0.0.0/8`, `192.168.0.0/16`).
