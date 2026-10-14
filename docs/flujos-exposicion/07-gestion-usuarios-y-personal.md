# 👥 Guía Técnica de Exposición 07: Gestión de Personal, Usuarios y Seguridad Administrativa

Esta guía explica detalladamente la arquitectura, los flujos operativos, las medidas de seguridad y la persistencia en base de datos del módulo de **Gestión de Usuarios y Personal Operativo** (`/admin/usuarios`) en **CargaExpress Perú**.

---

## 1. Visión General del Módulo

El módulo de **Gestión de Personal** es el panel de control central mediante el cual el **Administrador del Sistema**:
1. Da de alta a nuevos colaboradores (Cajeros, Almaceneros, Supervisores, Couriers y Transportistas).
2. Asigna o reubica colaboradores entre agencias provinciales (Lima, Arequipa, Cusco).
3. Gestiona credenciales seguras (generación de contraseñas hasheadas con Bcrypt).
4. Administra la **Autenticación de Dos Factores (2FA/TOTP)** para cada empleado (generando el código QR para vincular en Google Authenticator).
5. Ejecuta la **desactivación inmediata o desbloqueo** de cuentas con **revocación instantánea de sesiones JWT en circulación** (`sesion_version`).
6. Registra cada alteración administrativa en la tabla inmutable `auditoria_operaciones` con respaldo JSON de valores anteriores y nuevos.

---

## 2. Diagrama de Conexión de Componentes (Frontend ⇄ Backend ⇄ Base de Datos)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                                   │
│                                                                                        │
│   [Vista Principal: UsuariosList.jsx] ────────► [Servicio: usuarioService.js]          │
│   - Tabla de Colaboradores con badges          - Métodos HTTP (GET, POST, PUT, PATCH)  │
│   - Modal Crear/Editar Usuario                 - Inyección de Bearer Token JWT         │
│   - Modal QR 2FA para Google Authenticator                                             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP REST (Headers: Authorization Bearer)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                              BACKEND (FastAPI Core)                                    │
│                                                                                        │
│   [Router: endpoints/usuarios.py] ◄──────────► [Control de Acceso: deps.py]            │
│   - GET    /api/v1/usuarios                      - Exige require_role(["ADMINISTRADOR"])│
│   - POST   /api/v1/usuarios                      - Valida firma y sesion_version        │
│   - PUT    /api/v1/usuarios/{id}                                                       │
│   - PATCH  /api/v1/usuarios/{id}/toggle-activo                                         │
│   - PATCH  /api/v1/usuarios/{id}/toggle-2fa                                            │
│                         │                                                              │
│                         ▼                                                              │
│            [Criptografía: security.py]                                                 │
│            - Bcrypt (12 rondas con salting)                                            │
│            - PyOTP (Base32) & QRCode (Base64 PNG)                                      │
└─────────────────────────┬───────────────────────────────────┬──────────────────────────┘
                          │                                   │
                          ▼                                   ▼
             ┌─────────────────────────┐         ┌─────────────────────────┐
             │    TABLA: usuarios      │         │    TABLA: auditoria_    │
             │                         │         │           operaciones   │
             │ - codigo_trabajador (UQ)│         │                         │
             │ - dni, email, password  │         │ - tabla_afectada        │
             │ - tipo (rol RBAC)       │         │ - registro_id, accion   │
             │ - sesion_version (+1)   │         │ - valores_nuevos (JSON) │
             │ - totp_secret, activo   │         │ - usuario_id (Admin)    │
             └─────────────────────────┘         └─────────────────────────┘
```

---

## 3. Flujo Paso a Paso de las Operaciones Administrativas

### 🟡 Operación 1: Alta de Nuevo Colaborador (`POST /usuarios`)
1. **Entrada de Datos:** El administrador abre el modal en [UsuariosList.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/usuarios/UsuariosList.jsx) e ingresa: DNI, Nombres, Apellidos, Email, Rol (`cajero`, `almacen`, `courier`, etc.), Agencia asignada y Contraseña inicial.
2. **Campos Condicionales por Especialidad:**
   * Si el rol es `cajero`: se habilita y exige el campo `numero_caja`.
   * Si el rol es `courier` o `transportista`: se habilita el campo `licencia_conducir` (Brevete MTC).
3. **Validaciones en Backend:**
   * **Unicidad de DNI:** Comprueba que no exista otro trabajador con el mismo documento.
   * **Unicidad de Email:** Comprueba que el correo no esté duplicado.
   * **Existencia de Agencia:** Valida que el `agencia_id` pertenezca a una sede habilitada.
4. **Generación de Código Correlativo de Trabajador:**
   * El sistema consulta `MAX(codigo_trabajador)` y asigna automáticamente el siguiente entero único (ej. `1001`, `1002`).
5. **Criptografía de Contraseña:**
   * Ejecuta `usuario.set_password(plain_password)`, generando un hash con **Bcrypt a 12 rondas con salting**.
   * Fija `sesion_version = 1`.
6. **Auditoría Obligatoria:**
   * Inserta un registro en `auditoria_operaciones` con la acción `CREAR_USUARIO` y el JSON de datos nuevos.

---

### 🟠 Operación 2: Inhabilitación Rápida y Revocación de Sesiones (`PATCH /usuarios/{id}/toggle-activo`)
Esta es una de las características de seguridad más avanzadas del sistema:

1. **Protección Anti-Bloqueo de Administrador:**
   * El backend valida: `if id == current_user.id: raise HTTPException(400, "No puedes desactivar tu propia cuenta.")`.
2. **Inversión de Estado:** `usuario.activo = not usuario.activo`.
3. **Revocación Inmediata de Tokens JWT Activos:**
   * Si el usuario es desactivado (ej. por despido o sanción), el servidor ejecuta:
     $$\text{usuario.sesion\_version} \mathrel{+}= 1$$
   * **Efecto de Seguridad:** Aunque el empleado tenga un `access_token` JWT guardado en su navegador que teóricamente expire en 30 minutos, en la siguiente petición HTTP el middleware `get_current_user` detectará que la versión del token no coincide con la versión en base de datos y **bloqueará el acceso de inmediato arrojando HTTP 401 Unauthorized**.

---

### 🟣 Operación 3: Activación y Reset de 2FA / TOTP (`PATCH /usuarios/{id}/toggle-2fa`)
Permite al administrador enrolar o resetear el segundo factor de autenticación de cualquier colaborador:

1. **Si el usuario ya tenía 2FA activo:**
   * Se desactiva fijando `usuario.totp_configurado = False` y `usuario.totp_secret = None`.
   * Queda registrado en auditoría como `DESACTIVAR_2FA`.
2. **Si el usuario no tenía 2FA:**
   * Backend genera una nueva semilla aleatoria Base32: `secret = pyotp.random_base32()`.
   * Construye la URI oficial: `otpauth://totp/CargaExpress%20Peru:email?secret=...&issuer=CargaExpress%20Peru`.
   * Genera el código QR en imagen **Base64 PNG**.
   * Retorna el secreto manual y la imagen QR al frontend.
   * En [UsuariosList.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/usuarios/UsuariosList.jsx), se abre un modal con el código QR para que el colaborador lo escanee con su aplicación **Google Authenticator** o **Authy**.

---

## 4. Persistencia en Base de Datos: Tablas y Datos Esenciales

### A. Tabla `usuarios` (Estructura de Personal)

| Columna | Tipo | Función en la Gestión de Personal |
|:---|:---|:---|
| `codigo_trabajador` | `INTEGER UNIQUE` | Identificador institucional correlativo del colaborador. |
| `dni` | `VARCHAR(8) UNIQUE` | Documento de identidad verificado. |
| `nombres` / `apellidos`| `VARCHAR(100)` | Nombre completo del colaborador. |
| `email` | `VARCHAR(150) UNIQUE` | Correo institucional o personal usado para login y recuperación. |
| `password_hash` | `VARCHAR(255)` | Hash Bcrypt unidireccional. |
| `tipo` | `VARCHAR(13)` | Rol del sistema: `'administrador'`, `'supervisor'`, `'cajero'`, `'almacen'`, `'courier'`, `'transportista'`. |
| `agencia_id` | `INTEGER (FK)` | Agencia física a la que está adscrito. |
| `numero_caja` | `INTEGER NULL` | Número de ventanilla asignada (solo cajeros). |
| `licencia_conducir`| `VARCHAR(20) NULL` | Brevete MTC (solo couriers y choferes). |
| `activo` | `BOOLEAN` | Bandera de habilitación en el sistema. |
| `bloqueado` | `BOOLEAN` | Indica si fue congelado por intentos fallidos de login. |
| `totp_configurado` | `BOOLEAN` | Indica si tiene segundo factor activo. |
| `totp_secret` | `VARCHAR(32)` | Semilla Base32 para TOTP. |
| `sesion_version` | `INTEGER` | Contador incremental que revoca JWTs al modificarse. |

---

### B. Tabla `auditoria_operaciones` (Trazabilidad Administrativa)

Cada creación, edición, activación o enrolamiento 2FA genera una fila inmutable:

| Columna | Ejemplo de Registro | Significado Técnico |
|:---|:---|:---|
| `tabla_afectada` | `"usuarios"` | Entidad modificada. |
| `registro_id` | `5` | ID del colaborador afectado. |
| `accion` | `"ACTUALIZAR_USUARIO"` o `"ACTIVAR_2FA"` | Operación realizada. |
| `usuario_id` | `1` | ID del Administrador que ejecutó la acción. |
| `valores_nuevos` | `{"rol": "cajero", "agencia_id": 1, "activo": true}` | Contenido JSON estructurado. |
| `creado_en` | `2026-10-13 21:10:00 UTC` | Timestamp inmutable. |

---

## 5. Módulos de Código Exactos para Mostrar en la Exposición

### Backend:
1. [app/api/v1/endpoints/usuarios.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/usuarios.py):
   * Líneas 47-70: `listar_usuarios()` con filtros por rol y agencia.
   * Líneas 73-151: `crear_usuario()` (Validaciones, generación de código y hashing Bcrypt).
   * Líneas 175-241: `actualizar_usuario()` (Modificación de datos y roles).
   * Líneas 244-285: `toggle_activo()` (Revocación inmediata mediante `sesion_version += 1`).
   * Líneas 287-359: `toggle_2fa()` (Generación de semilla Base32 y código QR PNG Base64).
2. [app/models/usuario.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/usuario.py):
   * Líneas 55-63: Método `set_password()` (Hashing e incremento de versión de sesión).

### Frontend:
1. [src/pages/admin/usuarios/UsuariosList.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/usuarios/UsuariosList.jsx):
   * Tabla interactiva con badges de roles, agencias, estado activo y 2FA.
   * Modal dinámico de creación/edición con campos condicionales.
   * Modal visual con imagen QR para escaneo con Google Authenticator.
2. [src/services/usuarioService.js](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/usuarioService.js):
   * Llamadas `getUsuarios()`, `crearUsuario()`, `actualizarUsuario()`, `toggleActivo()`, `toggle2FA()`.

---

## 6. Preguntas Frecuentes del Jurado / Evaluador y Cómo Responderlas

| Pregunta Típica | Respuesta Técnica y de Seguridad |
|:---|:---|
| **¿Cómo aseguran que solo un Administrador pueda crear o editar usuarios?** | *"Mediante la inyección de dependencias `require_role(["ADMINISTRADOR"])` en todos los endpoints de `/api/v1/usuarios`. Si un cajero o usuario de almacén intenta invocar estas rutas mediante Postman o script, el backend intercepta el JWT y arroja `HTTP 403 Forbidden`."* |
| **¿Qué pasa con la sesión de un empleado despedido si aún le quedaban 25 minutos de token JWT?** | *"Al hacer clic en 'Desactivar', el backend ejecuta `usuario.sesion_version += 1`. Dado que el token antiguo conserva la versión previa en su payload, cualquier petición subsiguiente es rechazada al instante en el middleware `get_current_user`, impidiendo cualquier fuga o manipulación de datos."* |
| **¿Dónde se guarda el código QR del 2FA? ¿Se almacena como imagen en el servidor?** | *"No se guarda como archivo en disco para optimizar espacio y seguridad. El backend genera la imagen en memoria usando la librería `qrcode` y la codifica en un string Data URI Base64 (`data:image/png;base64,...`) que se transmite en el payload JSON directo a la pantalla del administrador."* |
| **¿El administrador puede ver las contraseñas de sus trabajadores?** | *"No. Las contraseñas se procesan con Bcrypt (12 rondas con salting aleatorio). Ni el administrador ni nadie con acceso a la base de datos puede ver la contraseña en texto plano; solo es posible reasignar una nueva clave."* |
