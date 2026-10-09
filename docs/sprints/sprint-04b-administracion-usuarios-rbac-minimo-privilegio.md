# Sprint 04B: Administración Central de Usuarios, RBAC y Principio de Mínimo Privilegio

> **Módulo:** Gestión de Personal, Roles RBAC, Políticas de Contraseñas y MFA  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (React 19 + Vite en `http://localhost:5173`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI en `http://localhost:8000/api/v1`)  
> **Base de Datos:** PostgreSQL 17 / SQLite Local ([`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql) & [`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db))  
> **Estado del Sprint:** ✅ **COMPLETADO Y CERTIFICADO END-TO-END**

---

## 1. Resumen Ejecutivo del Hito Alcanzado

En este sprint se consolidó la **gestión centralizada de personal y colaboradores** bajo el **Principio de Mínimo Privilegio (PoLP)** y cumplimiento de estándares **NIST SP 800-63B / OWASP**.

Se retiraron todos los datos simulados en las vistas administrativas y se conectó la arquitectura en vivo:
1. **Acceso Exclusivo al Administrador:** Únicamente el usuario con rol `ADMINISTRADOR` (`DNI: 79665184`) tiene permisos para consultar, crear, modificar, activar/desactivar colaboradores o gestionar su 2FA.
2. **Política Homogénea de Contraseñas Seguras (Mínimo 8 Caracteres):** Se endureció la política eliminando el mínimo de 6 caracteres. Ahora tanto la creación de usuarios, la actualización y la recuperación de contraseña exigen **mínimo 8 caracteres, mayúscula, minúscula, número y símbolo especial**.
3. **Contraseña Segura por Defecto y Generador Dinámico:** La interfaz de creación precarga una contraseña por defecto que cumple al 100% las políticas (`CargaExp#2026`) y cuenta con un generador instantáneo `⚡ Generar segura`.
4. **MFA Administrable por Colaborador:** El Administrador puede activar el segundo factor (2FA/TOTP) a cualquier colaborador en cualquier momento, visualizando de inmediato el **código QR y clave Base32** para sincronización con Google Authenticator o Authy.

---

## 2. Matriz de Roles y Principio de Mínimo Privilegio (RBAC)

| Módulo / Acción | Administrador | Supervisor | Cajero | Almacén | Courier | Transportista |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CRUD de Personal y Usuarios** (`/admin/usuarios`) | ✅ **Total** | ❌ Denegado | ❌ Denegado | ❌ Denegado | ❌ Denegado | ❌ Denegado |
| **Activar / Desactivar MFA (2FA)** | ✅ **Total** | ❌ Denegado | ❌ Denegado | ❌ Denegado | ❌ Denegado | ❌ Denegado |
| **Catálogo de Agencias** (`/admin/agencias`) | ✅ Lectura/Gestión | ✅ Lectura | ❌ Denegado | ❌ Denegado | ❌ Denegado | ❌ Denegado |
| **Dashboard y KPIs Generales** (`/admin/dashboard`) | ✅ Total | ✅ Total | ✅ Operativo | ✅ Operativo | ✅ Entregas | ✅ Rutas |
| **Listado y Ficha de Envíos** (`/admin/envios`) | ✅ Total | ✅ Total | ✅ Local | ✅ Local | ❌ Denegado | ❌ Denegado |
| **Caja y Cobro Presencial** (`/admin/caja`) | ✅ Auditoría | ✅ Supervisión | ✅ Operativo | ❌ Denegado | ❌ Denegado | ❌ Denegado |
| **Almacén, Guías y Manifiestos** (`/admin/almacen`) | ✅ Total | ✅ Total | ❌ Denegado | ✅ Operativo | ❌ Denegado | ❌ Denegado |
| **Rutas y Entregas a Domicilio** (`/admin/courier`) | ✅ Total | ✅ Total | ❌ Denegado | ❌ Denegado | ✅ Operativo | ✅ Operativo |

> **Nota de Seguridad:** Cualquier petición a endpoints de usuarios por parte de un token que no posea rol `ADMINISTRADOR` es rechazada inmediatamente con **HTTP 401 / 403 Forbidden**.

---

## 3. Política de Contraseñas y Complejidad Criptográfica

Tanto en [`app/schemas/usuario.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/schemas/usuario.py) como en [`app/schemas/auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/schemas/auth.py), se unificó el validador estricto:

```python
@field_validator("password")
@classmethod
def validar_complejidad_password(cls, v: str) -> str:
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", v):
        raise ValueError("La contraseña debe incluir al menos una letra mayúscula (A-Z).")
    if not re.search(r"[a-z]", v):
        raise ValueError("La contraseña debe incluir al menos una letra minúscula (a-z).")
    if not re.search(r"\d", v):
        raise ValueError("La contraseña debe incluir al menos un número (0-9).")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\/~`]", v):
        raise ValueError("La contraseña debe incluir al menos un símbolo o carácter especial (!@#$%...).")
    return v
```

### Reglas Validadas:
- **Longitud:** Mínimo 8 caracteres (máximo 100).
- **Mayúsculas:** Al menos una letra `[A-Z]`.
- **Minúsculas:** Al menos una letra `[a-z]`.
- **Dígitos:** Al menos un número `[0-9]`.
- **Símbolos:** Al menos un carácter especial `[!@#$%^&*(),.?":{}|<>\-_+=...]`.
- **Almacenamiento:** Hashing salado con algoritmo `Bcrypt` (factor de costo 12).
- **Revocación:** Al resetear o cambiar la contraseña, se incrementa `sesion_version += 1`, invalidando inmediatamente todas las sesiones JWT previas en circulación.

---

## 4. Endpoints del Backend Certificados

| Método | Endpoint | Rol Requerido | Descripción |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/usuarios` | `ADMINISTRADOR` | Listado completo de colaboradores con filtros por rol y agencia. |
| `POST` | `/api/v1/usuarios` | `ADMINISTRADOR` | Creación de colaborador con correlativo automático de código de trabajador y hash Bcrypt. |
| `GET` | `/api/v1/usuarios/{id}` | `ADMINISTRADOR` | Ficha técnica y datos de auditoría del usuario. |
| `PUT` | `/api/v1/usuarios/{id}` | `ADMINISTRADOR` | Modificación de datos personales, rol asignado, agencia o reseteo de contraseña. |
| `PATCH` | `/api/v1/usuarios/{id}/toggle-activo` | `ADMINISTRADOR` | Habilitación o inhabilitación inmediata del colaborador. |
| `PATCH` | `/api/v1/usuarios/{id}/toggle-2fa` | `ADMINISTRADOR` | Activación de MFA con generación de secreto Base32 y código QR en Base64, o desactivación. |

---

## 5. Auditoría de Operaciones Inmutable

Cada mutación realizada en el módulo de personal se registra de forma obligatoria en la tabla `auditoria_operaciones` mediante [`audit_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/audit_service.py):
- `CREAR_USUARIO`: Registra DNI, correo, rol y el `usuario_id` del administrador responsable.
- `ACTUALIZAR_USUARIO`: Registra los valores previos y nuevos modificados.
- `ACTIVAR_2FA` / `DESACTIVAR_2FA`: Registra la fecha y hora del cambio de factor de autenticación.
- `ACTIVAR_ACCESO` / `DESACTIVAR_ACCESO`: Registra el corte o habilitación de credenciales.

---

## 6. Casos de Prueba Certificados

```text
=== TEST 1: REJECT WEAK PASSWORDS (8 CHARS + COMPLEXITY) ===
  [OK] Short (<8) correctamente rechazado con HTTP 422
  [OK] No uppercase correctamente rechazado con HTTP 422
  [OK] No lowercase correctamente rechazado con HTTP 422
  [OK] No digit correctamente rechazado con HTTP 422
  [OK] No special char correctamente rechazado con HTTP 422

=== TEST 2: ACCEPT ROBUST PASSWORD ===
  [OK] Usuario creado con contraseña robusta: Carlos Alberto Vargas Peña | ID: 5

=== TEST 3: LEAST PRIVILEGE ENFORCEMENT ===
  [OK] Cajero rechazado de GET /usuarios con HTTP 401/403 Forbidden
  [OK] Cajero rechazado de POST /usuarios con HTTP 401/403 Forbidden
  [OK] Administrador 79665184 autorizado y verificado con 2FA real
```
