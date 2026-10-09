# Arquitectura de Seguridad, Autenticación y Control de Acceso (RBAC)

> **Módulo:** Capa de Seguridad Transversal del Backend  
> **Estándares:** OWASP Top 10 (2021) | OWASP API Security Top 10 (2023) | RFC 7519 (JWT) | RFC 6238 (TOTP)  
> **Librerías Core:** `python-jose`, `passlib[bcrypt]`, `pyotp`  
> **Estado:** 🛡️ **ESPECIFICACIÓN OFICIAL DE SEGURIDAD**

---

## 1. Esquema de Autenticación y Gestión de Tokens

El backend utiliza tokens **JSON Web Tokens (JWT)** firmados con algoritmo simétrico HMAC SHA-256 (`HS256`), configurado con una clave maestra (`SECRET_KEY`) robusta y tiempos de expiración acotados para minimizar ventanas de ataque.

### Tipos de Tokens Emitidos:
1. **Access Token (`scope: access`):**
   - **Expiración:** 30 minutos (`ACCESS_TOKEN_EXPIRE_MINUTES`).
   - **Payload:** `sub` (ID de usuario en BD), `rol` (tipo de usuario), `agencia_id`, `sesion_version`, `exp`, `iat`.
   - **Uso:** Presentado en la cabecera `Authorization: Bearer <token>` para consumir endpoints protegidos de la Intranet.
2. **Refresh Token (`scope: refresh`):**
   - **Expiración:** 7 días (`REFRESH_TOKEN_EXPIRE_DAYS`).
   - **Uso:** Empleado exclusivamente en el endpoint `/api/v1/auth/refresh` para renovar el par de tokens sin forzar al empleado a reingresar sus credenciales.
3. **MFA Token Temporal (`scope: mfa_pending`):**
   - **Expiración:** 5 minutos estrictos.
   - **Uso:** Emitido durante el primer paso del login si el usuario tiene el segundo factor activado. Solo autoriza el consumo del endpoint `/api/v1/auth/2fa`.

---

## 2. Invalidación Global Reactiva de Sesiones (`sesion_version`)

Uno de los mayores riesgos en arquitecturas JWT puras es la incapacidad de revocar tokens antes de su expiración física sin recurrir a una base de datos en memoria pesada. CargaExpress implementa el patrón **Versionado de Sesión por Usuario**:

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  JWT emitido    │       │ Usuario en DB   │       │ Resultado en    │
│  sesion_version │       │ sesion_version  │       │ deps.py         │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│        1        │ <===> │        1        │  ==>  │  200 OK         │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│        1        │ <===> │        2        │  ==>  │  401 Revocado   │
│ (desactualizado)│       │ (tras logout o  │       │  "Sesión ha     │
│                 │       │  cambio clave)  │       │   sido revocada"│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

Cuando un usuario:
* Pulsa **Cerrar Sesión (Logout)**
* Cambia su contraseña o solicita recuperación
* Es suspendido o despedido por un Administrador

La base de datos incrementa el contador:
```sql
UPDATE usuarios SET sesion_version = sesion_version + 1 WHERE id = :user_id;
```
Cualquier petición con el token anterior es rechazada instantáneamente con código HTTP `401 Unauthorized`.

---

## 3. Matriz de Roles y Autorización Basada en Roles (RBAC)

El acceso a los endpoints se controla mediante la dependencia `require_role(allowed_roles: List[str])` ubicada en [`app/api/deps.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/deps.py). El sistema implementa el principio de **Mínimo Privilegio**:

| Rol del Empleado | Alcance Funcional Permitido | Endpoints Principales Permitidos |
| :--- | :--- | :--- |
| **`ADMINISTRADOR`** | Acceso total al sistema, gestión de usuarios, auditoría forense, agencias y configuración global. | `/usuarios/*`, `/auditoria/*`, `/envios/*`, `/agencias/*` |
| **`SUPERVISOR`** | Supervisión operativa de sede, consulta consolidada de envíos, arqueos de caja y reasignaciones. | `/dashboard/*`, `/envios/*`, `/caja/resumen`, `/clientes/*` |
| **`CAJERO`** | Atención al público en ventanilla, pesaje físico y cobro presencial, recepción y entrega de paquetes. | `/envios/{id}/recepcionar`, `/envios/{id}/entregar`, `/caja/aperturas`, `/caja/cobrar` |
| **`ALMACEN`** | Clasificación de carga en bodega, consolidación de bultos y asignación a manifiesto de ruta. | `/envios/{id}/recepcionar`, `/envios/{id}/despachar`, `/envios/{id}/arribar` |
| **`TRANSPORTISTA`** | Conducción interprovincial, traslado de ruta nacional y reporte de tránsito. | `/envios/{id}/despachar`, `/manifiestos/*` |
| **`COURIER`** | Reparto y recojo en última milla (domicilio de remitente o destinatario). | `/envios/{id}/entregar`, `/envios/reparto` |

---

## 4. Mitigación contra BOLA / IDOR (Broken Object Level Authorization)

Para evitar que un usuario de la **Agencia Arequipa** modifique o consulte envíos de la **Agencia Trujillo** simplemente alterando el ID en la URL (OWASP API1:2023):
1. **Atribución de Usuario:** Cada usuario operativo posee `agencia_id` no nulo en su perfil.
2. **Filtro Forzoso en Repositorio/Servicio:**
   ```python
   # Si el usuario no es ADMINISTRADOR global, sus consultas se circunscriben a su agencia
   if current_user.tipo != "ADMINISTRADOR":
       stmt = stmt.where(
           or_(
               Envio.agencia_origen_id == current_user.agencia_id,
               Envio.agencia_destino_id == current_user.agencia_id
           )
       )
   ```

---

## 5. Enmascaramiento y Protección de Datos Personales (PII Data Masking)

El endpoint público de tracking (`/api/v1/publico/tracking/{codigo}`) puede ser consultado por cualquier persona con el código de seguimiento. Para cumplir con la **Ley N° 29733 (Protección de Datos Personales en Perú)** y prevenir la recolección masiva de identidades (Scraping):

* **Nombre de Remitente / Destinatario:** Se exponen únicamente las iniciales seguidas de asteriscos. Ej: `Juan Pérez` ➔ `J*** P****`.
* **Teléfonos:** Se ocultan todos los dígitos excepto los tres últimos. Ej: `987654321` ➔ `******321`.
* **Correos Electrónicos:** Se protegen las letras centrales del usuario. Ej: `carlos@empresa.com` ➔ `c****s@empresa.com`.
* **DNI / RUC:** **No se exponen bajo ninguna circunstancia** en los endpoints públicos de tracking.
