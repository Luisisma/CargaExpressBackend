# 🔐 Guía Técnica de Exposición 01: Inicio de Sesión, Autenticación 2FA, JWT y Roles (RBAC)

Esta guía explica a profundidad y de forma práctica la arquitectura técnica, los flujos de datos, la criptografía y la persistencia en base de datos del módulo de **Autenticación y Seguridad** de **CargaExpress Perú**.

---

## 1. Resumen Ejecutivo de la Funcionalidad

El sistema implementa un modelo de **autenticación desacoplada y sin estado (Stateless)** bajo el estándar **OAuth2 con JWT (JSON Web Tokens)** y **Autenticación Multifactorial (2FA - TOTP)** compatible con Google Authenticator y Authy.

* **Arquitectura:** Frontend SPA (React + Vite) desacoplado de Backend REST (FastAPI + SQLAlchemy 2.0).
* **Seguridad de Contraseñas:** Hashing no reversible con **Bcrypt** (coste de 12 rondas con salting aleatorio por usuario).
* **2FA Obligatorio / Opcional:** Algoritmo **TOTP (RFC 6238)** con secretos en Base32 y tolerancia temporal de $\pm 30$ segundos.
* **Sesión:** JWT firmado con **HS256**, tokens diferenciados por `scope` (`mfa_pending`, `access`, `refresh`) y revocación activa mediante `sesion_version` en base de datos.
* **Control de Acceso:** **RBAC (Role-Based Access Control)** con autorización granular a nivel de endpoint en Backend y renderizado condicional en Frontend.

---

## 2. Diagrama de Conexión de Componentes (¿Qué se conecta con qué?)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FRONTEND (React + Vite)                                 │
│                                                                                        │
│  [Vista Login: Login.jsx]              [Vista 2FA: Verificacion2FA.jsx]                 │
│             │                                        │                                 │
│             ▼                                        ▼                                 │
│     [authService.js] ◄──────────── [AuthContext.jsx] ────────────► [AdminLayout.jsx]    │
│  (Peticiones fetch HTTP)         (Almacena Tokens/User)          (Filtra Menú por Rol) │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP POST /api/v1/auth/*
                                            │ (JSON Envelope + Bearer Tokens)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                                 BACKEND (FastAPI Core)                                 │
│                                                                                        │
│  [Router: endpoints/auth.py] ────► [Inyección Dependencias: deps.py]                   │
│             │                       (Valida Bearer JWT, Sesión y require_role)         │
│             ▼                                                                          │
│  [Service: auth_service.py] ◄────► [Criptografía: core/security.py]                    │
│   - Control Fuerza Bruta             - Bcrypt (12 rondas)                              │
│   - Emisión de Tokens                - PyJWT (HS256)                                   │
│   - Validación TOTP                  - PyOTP & QrCode Base64                           │
└──────────────────────┬───────────────────────────────────┬─────────────────────────────┘
                       │                                   │
                       ▼                                   ▼
          ┌─────────────────────────┐         ┌─────────────────────────┐
          │  TABLA DB: usuarios     │         │ TABLA DB: auditoria_    │
          │                         │         │           seguridad     │
          │ - Lectura password_hash │         │                         │
          │ - Check totp_secret     │         │ - IP, User-Agent, Fecha │
          │ - Reset intentos_fall   │         │ - Evento y Nivel Riesgo │
          │ - Update ultimo_login   │         │ - Inmutable (OWASP A09) │
          └─────────────────────────┘         └─────────────────────────┘
```

---

## 3. Flujo Paso a Paso de la Autenticación

El proceso se divide en dos pasos orquestados:

### 🟡 Paso 1: Identificación y Credenciales Básicas (`/auth/login`)

1. **Entrada de Datos en Cliente:** El usuario escribe su DNI (8 dígitos) o correo y contraseña en [Login.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/auth/Login.jsx).
2. **Llamada API:** `authService.login()` realiza un `POST /api/v1/auth/login`.
3. **Búsqueda en Base de Datos:** `auth_service.py` busca al usuario en la tabla `usuarios` por DNI o email mediante consulta ORM indexada.
4. **Verificación de Bloqueo:**
   * Si `usuario.bloqueado == True` $\rightarrow$ Retorna `HTTP 423 Locked`.
   * Si `usuario.bloqueado_hasta > datetime.now()` $\rightarrow$ Retorna `HTTP 423 Locked` indicando cuántos minutos restan.
5. **Comprobación de Contraseña:**
   * Se ejecuta `security.verify_password()`.
   * **Si falla:** Se incrementa `usuario.intentos_fallidos`. Si supera 5 intentos fallidos, se fija `bloqueado_hasta = ahora + 15 min`. Se registra en `auditoria_seguridad` con nivel `WARN`/`CRITICAL` y retorna `HTTP 401 Unauthorized` genérico (mitigación de enumeración de usuarios).
   * **Si coincide:** Se resetean `intentos_fallidos = 0`, `bloqueado_hasta = null` y se actualiza `ultimo_login = ahora`.
6. **Bifurcación según Multifactor (2FA):**
   * **Si `totp_configurado == True`:** 
     * Se emite un `temp_token` firmado por JWT con duración estricta de **5 minutos** y `scope = "mfa_pending"`.
     * Se genera la URI `otpauth://` y el código QR en Base64 PNG.
     * Respuesta JSON: `mfa_requerido: true`, `temp_token`, QR y secreto manual.
     * En Frontend, [AuthContext.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/context/AuthContext.jsx) guarda el `temp_token` en `sessionStorage` y redirige a la pantalla `/auth/2fa`.
   * **Si `totp_configurado == False`:**
     * Emite directamente `access_token` (30 min) y `refresh_token` (7 días).
     * Frontend almacena sesión en `localStorage` y da acceso inmediato.

---

### 🟢 Paso 2: Validación del Segundo Factor (`/auth/2fa`)

1. **Lectura del Autenticador:** El usuario abre Google Authenticator o Authy en su smartphone y lee el código rotativo de 6 dígitos.
2. **Envío al Servidor:** Frontend realiza `POST /api/v1/auth/2fa` enviando `{ temp_token, codigo_totp }`.
3. **Validación Criptográfica del Token Temporal:**
   * Backend decodifica el token con la `SECRET_KEY`.
   * Exige estrictamente que el claim contenga `scope == "mfa_pending"`. Un `access_token` o un token manipulado es rechazado.
4. **Validación del Algoritmo TOTP:**
   * `pyotp.TOTP(usuario.totp_secret).verify(codigo, valid_window=1)`.
   * `valid_window=1` proporciona una ventana de tolerancia de $\pm 30$ segundos para compensar desfases de hora entre el celular y el servidor.
5. **Emisión de Sesión Definitiva:**
   * Si el código es correcto, se emite:
     * **Access Token:** Validez de 30 minutos, scope `"access"`, con claims del usuario (`sub: id`, `rol`, `agencia_id`, `sesion_version`).
     * **Refresh Token:** Validez de 7 días, scope `"refresh"`, con claims mínimos (`sub: id`, `sesion_version`).
   * Se registra en `auditoria_seguridad` el evento inmutable `2FA_EXITOSO_SESION_INICIADA`.
6. **Recepción en Frontend:**
   * [AuthContext.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/context/AuthContext.jsx) almacena `ce_access_token`, `ce_refresh_token` y el objeto `ce_user` en `localStorage`.
   * Limpia los tokens temporales de `sessionStorage`.
   * Redirige al usuario al panel administrativo correspondiente según su rol `/admin/dashboard`.

---

## 4. Persistencia en Base de Datos: Tablas y Datos Esenciales

Para sustentar ante el jurado qué viaja por la red y qué se persiste en el motor de base de datos (PostgreSQL / SQLite):

### A. Tabla `usuarios` (Lectura y Actualización)

| Columna | Tipo | Rol en el Flujo de Login |
|:---|:---|:---|
| `id` | `INTEGER PRIMARY KEY` | Identificador único numérico que viaja dentro del JWT en el claim `"sub"`. |
| `dni` / `email` | `VARCHAR` (Unique e Indexados) | Campo de búsqueda de la cuenta en el Login. |
| `password_hash` | `VARCHAR(255)` | Almacena el hash Bcrypt de 60 caracteres (nunca texto plano). |
| `tipo` | `VARCHAR(13)` | Rol del usuario (`administrador`, `cajero`, `supervisor`, `almacen`, `courier`, `transportista`). |
| `totp_secret` | `VARCHAR(32)` | Semilla Base32 para calcular y verificar códigos de Google Authenticator. |
| `totp_configurado` | `BOOLEAN` | Bandera que decide si el login exige el Paso 2 (2FA) o permite ingreso directo. |
| `intentos_fallidos` | `INTEGER` | Contador acumulativo. Se incrementa en passwords erróneos y se resetea a 0 al logear con éxito. |
| `bloqueado_hasta` | `DATETIME` | Marca temporal que congela el acceso durante 15 minutos tras 5 fallos seguidos. |
| `ultimo_login` | `DATETIME` | Timestamp actualizado en cada login exitoso. |
| `sesion_version` | `INTEGER` | Contador de revocación de sesiones. Si el usuario cambia su clave o cierra sesión, este número se incrementa en DB e invalida de inmediato cualquier JWT antiguo en circulación. |

---

### B. Tabla `auditoria_seguridad` (Persistencia Inmutable de Eventos)

Cada intento o éxito de login genera un registro obligatorio de auditoría:

| Columna | Valor Ejemplo | Explicación Técnica |
|:---|:---|:---|
| `usuario_id` | `4` | Clave foránea del usuario (o `NULL` si el usuario no existía). |
| `evento` | `"LOGIN_PASO_1_EXITOSO_REQUIERE_2FA"` o `"LOGIN_FALLIDO_PASSWORD_INCORRECTO"` | Código de auditoría estandarizado según directrices OWASP A09. |
| `direccion_ip` | `"192.168.1.45"` | Extraída de la cabecera `X-Forwarded-For` o conexión directa del cliente. |
| `user_agent` | `"Mozilla/5.0 ... Chrome/120"` | Identificador del navegador o dispositivo del solicitante. |
| `detalles` | `{"intentos": 2}` (Formato JSON) | Metadatos contextuales del evento de seguridad. |
| `nivel_riesgo` | `"INFO"`, `"WARN"` o `"CRITICAL"` | Permite filtrar intentos de ataque de fuerza bruta o intrusión. |
| `creado_en` | `2026-10-13 20:25:00 UTC` | Fecha y hora UTC del servidor. |

---

### C. Datos Esenciales que Viajan en la Red (Payloads de Red)

#### 1. Request Login (Frontend $\rightarrow$ Backend):
```json
{
  "identificador": "47852140",
  "password": "PasswordSeguro2026*"
}
```

#### 2. Response Login (Backend $\rightarrow$ Frontend) cuando 2FA está activo:
```json
{
  "success": true,
  "message": "Se requiere verificación de segundo factor (2FA).",
  "data": {
    "mfa_requerido": true,
    "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiZXhwIjoxNzg5...,InNjb3BlIjoibWZhX3BlbmRpbmcifQ...",
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret_manual": "JBSWY3DPEHPK3PXP",
    "usuario": {
      "id": 4,
      "dni": "47852140",
      "nombre_completo": "Carlos Mendoza",
      "email": "cmendoza@cargaexpress.pe",
      "tipo": "cajero"
    }
  }
}
```

#### 3. Request 2FA (Frontend $\rightarrow$ Backend):
```json
{
  "temp_token": "eyJhbGciOiJIUzI1Ni...",
  "codigo_totp": "584912"
}
```

#### 4. Response 2FA Exitoso:
```json
{
  "success": true,
  "message": "Verificación de doble factor exitosa. Sesión iniciada.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0Iiwicm9sIjoiY2FqZXJvIiwiYWdlbmNpYV9pZCI6MSwic2VzaW9uX3ZlcnNpb24iOjEsImV4cCI6MTc4OS...,InNjb3BlIjoiYWNjZXNzIn0...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0Iiwic2VzaW9uX3ZlcnNpb24iOjEsImV4cCI6MTc4OS...,InNjb3BlIjoicmVmcmVzaCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "usuario": { ... }
  }
}
```

---

## 5. Criptografía y Seguridad Real: Hashing vs Cifrado

Si el jurado pregunta: *¿De verdad utiliza encriptación?* La respuesta técnica precisa es:

> **"Utilizamos dos ramas criptográficas distintas con propósitos específicos: Hashing unidireccional no reversible para contraseñas, y Cifrado/Firma simétrica digital para las credenciales de sesión en tránsito (JWT)."**

1. **Hashing de Contraseñas (Bcrypt):**
   * **No es encriptación reversible:** Una contraseña hasheada nunca se puede "desencriptar". Cuando el usuario inicia sesión, el sistema hashea la contraseña recibida con la misma sal almacenada y compara matemáticamente los hashes (`bcrypt.checkpw`).
   * **Cost Factor = 12 rondas:** Genera $2^{12} = 4,096$ iteraciones criptográficas de la función Blowfish modificada, volviendo inviable ataques de fuerza bruta basados en hardware acelerado (GPU).
   * **Soporte Legacy:** Compatible con usuarios heredados que poseían hashes `scrypt` o `pbkdf2` mediante [app/core/security.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/core/security.py#L22-L36).
2. **Firma Criptográfica JWT (HS256):**
   * El token JWT se compone de `Header.Payload.Signature`.
   * La firma se calcula mediante HMAC con algoritmo SHA-256 (`HMAC-SHA256`) utilizando una clave privada robusta (`SECRET_KEY`).
   * Si un usuario altera su rol en el Payload (por ejemplo de `"cajero"` a `"administrador"`), la firma se rompe de inmediato y FastAPI rechaza el token con `HTTP 401 Unauthorized`.
3. **Algoritmo TOTP (Time-based One-Time Password - RFC 6238):**
   * Es una función que toma la semilla compartida Base32 y el tiempo Unix dividido en épocas de 30 segundos:
     $$T = \lfloor (\text{UnixTime}) / 30 \rfloor$$
     $$\text{TOTP} = \text{Truncar}(\text{HMAC-SHA1}(\text{Secret}, T)) \pmod{10^6}$$
   * El código cambia cada 30 segundos y no requiere conexión a Internet en el teléfono del usuario.

---

## 6. ¿Cómo se Controlan los Roles y Permisos (RBAC)?

El control de roles se aplica en **ambos extremos del sistema** para garantizar seguridad en profundidad:

### En el Backend (Autorización Real Infranqueable)
En [app/api/deps.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/deps.py#L81-L103) se implementa el Dependency Injection `require_role()`:

```python
@router.post("/envios/despachar", dependencies=[Depends(require_role(["ADMINISTRADOR", "ALMACEN"]))])
def despachar_ruta(...):
    # Solo se ejecuta si el JWT pertenece a ADMIN o ALMACEN
```

* Si un usuario con rol `cajero` intenta ejecutar este endpoint mediante Postman o modificando el frontend, el middleware extrae el rol de su token JWT, detecta que no tiene permisos y arroja un error `HTTP 403 Forbidden` (`Acceso denegado`).

### En el Frontend (Experiencia de Usuario Condicional)
En [AdminLayout.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/components/layout/AdminLayout.jsx#L26-L85):
* Se lee el rol activo desde `user.tipo`.
* Se filtran las rutas y los botones del menú lateral según el array de roles autorizados:
  * El **Cajero** solo ve las secciones de **Recepción Mostrador** y **Cierre de Caja**.
  * El de **Almacén** solo ve **Despacho a Ruta**, **Arribos**, **Guías** y **Manifiestos**.
  * El **Administrador** tiene acceso irrestricto a todos los módulos.

---

## 7. Módulos de Código Exactos para Explicar en la Exposición

Si durante la presentación te piden mostrar el código fuente, abre estos archivos en orden:

### Backend (FastAPI):
1. [app/core/security.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/core/security.py):
   * Línea 13: `verify_password()` y Línea 39: `get_password_hash()` con Bcrypt (12 rondas).
   * Línea 46: `create_token()`, `create_temp_token()` y `create_access_token()`.
   * Línea 124: `generate_totp_secret()`, `generate_qr_base64()` y `verify_totp_code()`.
2. [app/services/auth_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py):
   * Línea 42: `procesar_login()` (Manejo de intentos fallidos, bloqueo y emisión de `temp_token`).
   * Línea 191: `procesar_verificacion_2fa()` (Validación del scope y código TOTP).
3. [app/api/deps.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/deps.py):
   * Línea 39: `get_current_user()` (Validación de firma JWT, expiración y `sesion_version`).
   * Línea 81: `require_role()` (Control de acceso RBAC por endpoints).
4. [app/models/usuario.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/usuario.py):
   * Columnas de control: `totp_secret`, `totp_configurado`, `intentos_fallidos`, `bloqueado_hasta`, `sesion_version`.

### Frontend (React):
1. [src/context/AuthContext.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/context/AuthContext.jsx):
   * Línea 57: función `login()` (Diferencia si requiere 2FA o sesión directa).
   * Línea 95: función `verify2FA()` (Envía código TOTP y guarda sesión final).
   * Línea 122: función `logout()` (Revoca sesión en backend y limpia storage).
2. [src/services/authService.js](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/authService.js):
   * Funciones `login()`, `verify2FA()`, `getProfile()`, `refreshToken()`.
3. [src/components/layout/AdminLayout.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/components/layout/AdminLayout.jsx):
   * Líneas 26-85: Matriz `allSections` y filtrado `navSections` según `rolActual`.

---

## 8. Preguntas Clave del Evaluador / Jurado y Cómo Defenderlas

| Pregunta Típica | Respuesta Técnica Recomendada |
|:---|:---|
| **¿Por qué usan JWT en vez de sesiones clásicas en cookies de servidor?** | *"Porque nuestra arquitectura es 100% desacoplada (SPA + API REST). JWT nos proporciona un esquema stateless (sin estado) que escala horizontalmente sin necesidad de compartir memoria de sesión entre réplicas del backend."* |
| **¿Si el token JWT es stateless, cómo cierran sesión o invalidan tokens robados?** | *"Implementamos control de sesión por versión (`sesion_version`). Cuando un usuario hace logout o cambia su contraseña, se incrementa el contador en la tabla `usuarios`. Cualquier token anterior queda invalidado al ser consultado en el middleware `get_current_user`."* |
| **¿Qué pasa si el atacante ingresa contraseñas aleatorias rápidamente?** | *"El sistema cuenta con protección anti-fuerza bruta: tras 5 intentos fallidos consecutivos, el campo `bloqueado_hasta` congela la cuenta durante 15 minutos e inserta un evento de riesgo `CRITICAL` en la tabla `auditoria_seguridad`."* |
| **¿El código 2FA depende de conexión a internet o de enviar SMS?** | *"No. Implementa el estándar RFC 6238 (TOTP). Funciona mediante una semilla secreta compartida y el reloj del sistema. La app Google Authenticator genera los 6 dígitos de forma autónoma sin consumir saldo ni requerir señal de telefonía."* |
| **¿Si alguien manipula el frontend para ver el botón de Almacén siendo Cajero, puede robar datos?** | *"No. El frontend solo oculta elementos visuales para mejorar la experiencia de usuario. La verdadera seguridad está en la inyección de dependencias `require_role()` de FastAPI, que valida criptográficamente los claims del JWT en cada petición HTTP."* |
