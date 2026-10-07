# Sprint 01: Especificación SDD - Autenticación Multifactor (MFA/2FA) y Auditoría

> **Módulo:** Autenticación, Sesión y Trazabilidad de Accesos  
> **Versión de API:** `/api/v1/auth`  
> **Estándares:** OWASP Top 10 (2021) A01, A02, A07, A09 | OWASP API Security (2023) API1, API2, API3, API5

---

## 1. Arquitectura y Flujo de Autenticación en 2 Fases

Para cumplir con **OWASP API2:2023 (Broken Authentication)** y la política institucional de seguridad de CargaExpress:

```text
  [ CLIENTE FRONTEND ]                          [ BACKEND FASTAPI ]                      [ POSTGRESQL 17 ]
           │                                             │                                       │
           │  1. POST /api/v1/auth/login                 │                                       │
           │     { "identificador", "password" }         │                                       │
           ├────────────────────────────────────────────>│  2. Busca usuario por DNI/Email       │
           │                                             ├──────────────────────────────────────>│
           │                                             │<──────────────────────────────────────┤
           │                                             │  3. Verifica hash & intentos          │
           │                                             │  4. Inserta 'auditoria_seguridad'     │
           │                                             ├──────────────────────────────────────>│
           │                                             │                                       │
           │  5. 200 OK                                  │                                       │
           │     { "mfa_requerido": true,                │                                       │
           │       "temp_token": "jwt_5_minutos" }       │                                       │
           │<────────────────────────────────────────────┤                                       │
           │                                             │                                       │
           │  6. POST /api/v1/auth/2fa                   │                                       │
           │     { "temp_token", "codigo_totp": "123456" }                                       │
           ├────────────────────────────────────────────>│  7. Valida TOTP con pyotp             │
           │                                             │  8. Inserta '2FA_EXITOSO'             │
           │                                             ├──────────────────────────────────────>│
           │  9. 200 OK                                  │                                       │
           │     { "access_token", "refresh_token",      │                                       │
           │       "usuario": { ... } }                  │                                       │
           │<────────────────────────────────────────────┤                                       │
```

---

## 2. Contratos de Datos (Pydantic v2 Schemas)

### 2.1. Login Request (`LoginRequestSchema`)
```python
class LoginRequestSchema(BaseModel):
    identificador: str = Field(..., min_length=3, max_length=150, description="DNI (8 dígitos) o Correo Electrónico")
    password: str = Field(..., min_length=6, max_length=100)
    
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```

### 2.2. Login Response (`LoginResponseSchema`)
```python
class LoginResponseSchema(BaseModel):
    mfa_requerido: bool
    temp_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    mensaje: str
```

### 2.3. Verificación 2FA Request (`TwoFactorVerifySchema`)
```python
class TwoFactorVerifySchema(BaseModel):
    temp_token: str = Field(..., description="Token temporal emitido tras login")
    codigo_totp: str = Field(..., pattern=r"^\d{6}$", description="Código numérico TOTP de 6 dígitos")
    
    model_config = ConfigDict(extra="forbid")
```

### 2.4. Perfil de Usuario (`UserProfileSchema`)
```python
class UserProfileSchema(BaseModel):
    id: int
    codigo_trabajador: int
    dni: str
    nombres: str
    apellidos: str
    email: str
    tipo: str
    agencia_id: Optional[int] = None
    numero_caja: Optional[int] = None
    totp_configurado: bool
    activo: bool
```

---

## 3. Especificación Técnica de Endpoints

### 3.1. `POST /api/v1/auth/login`
- **Acceso:** Público (con Rate Limiting: 5 peticiones/minuto por IP).
- **Lógica:**
  1. Busca al usuario activo por `dni` o por `email`.
  2. Si el usuario está `bloqueado` o `bloqueado_hasta > NOW()`, rechazar con `423 Locked` y registrar evento `CUENTA_BLOQUEADA`.
  3. Verifica contraseña:
     - Admite hashes seguros `bcrypt` y hashes heredados `werkzeug` (PBKDF2/Scrypt) para compatibilidad total con usuarios de `cargaexpress.sql`.
     - Si la clave es incorrecta, incrementa `intentos_fallidos`. Si supera 5 intentos, actualiza `bloqueado = True` o `bloqueado_hasta = NOW() + 15 min`. Registra `LOGIN_FALLIDO` en auditoría y responde `401 Unauthorized`.
  4. Si la clave es correcta:
     - Resetea `intentos_fallidos = 0`.
     - Actualiza `ultimo_login = NOW()`.
     - Registra `LOGIN_EXITOSO` en `auditoria_seguridad`.
     - Si `totp_configurado == True`: Emite `temp_token` JWT con claim `"scope": "mfa_pending"` y expiración de 5 minutos.
     - Si `totp_configurado == False`: Emite `access_token` y `refresh_token` directos.

### 3.2. `POST /api/v1/auth/2fa`
- **Acceso:** Público con `temp_token`.
- **Lógica:**
  1. Decodifica `temp_token`. Si es inválido, expiró o su claim `"scope"` no es `"mfa_pending"`, responde `401 Unauthorized`.
  2. Obtiene al usuario de la base de datos y su `totp_secret`.
  3. Valida `codigo_totp` usando `pyotp.TOTP(secret).verify(codigo, valid_window=1)`.
  4. Si es inválido: Registra `2FA_FALLIDO` y responde `400 Bad Request` ("Código de verificación inválido o expirado").
  5. Si es válido:
     - Registra `2FA_EXITOSO` en `auditoria_seguridad`.
     - Emite `access_token` (30 min) y `refresh_token` (7 días) con claims completos (`sub`, `rol`, `agencia_id`, `sesion_version`).

### 3.3. `POST /api/v1/auth/refresh`
- **Acceso:** Requiere Bearer Refresh Token válido.
- **Lógica:**
  1. Decodifica token con claim `"scope": "refresh"`.
  2. Valida que `sesion_version` en el token coincida con el `sesion_version` actual del usuario en BD.
  3. Emite un nuevo `access_token`.

### 3.4. `GET /api/v1/auth/me`
- **Acceso:** Autenticado (Bearer `access_token`).
- **Lógica:**
  1. Extrae usuario de la inyección de dependencias `get_current_user`.
  2. Retorna DTO `UserProfileSchema` (sin exponer `password_hash` ni `totp_secret`).

### 3.5. `POST /api/v1/auth/2fa/setup`
- **Acceso:** Autenticado.
- **Lógica:**
  1. Genera un nuevo secreto TOTP `pyotp.random_base32()`.
  2. Construye la URI otpauth estándar (`otpauth://totp/CargaExpress:{email}?secret={secret}&issuer=CargaExpress`).
  3. Retorna el secreto en texto y el código QR generado en formato Base64.
  4. Al recibir la primera confirmación válida, marca `totp_configurado = True`.

---

## 4. Checklist de Seguridad del Sprint 01

- [ ] Rate limiting activo en `/api/v1/auth/login`.
- [ ] Detección y bloqueo temporal por fuerza bruta (> 5 intentos).
- [ ] Registro en `auditoria_seguridad` con IP, User-Agent y Request-ID.
- [ ] Claims estrictos en JWT: `sub`, `rol`, `agencia_id`, `sesion_version`, `exp`, `iat`.
- [ ] Validación de `sesion_version` en cada petición para revocación global.
- [ ] No revelación de información sensible en respuestas de error (evitar enumeración de usuarios).
- [ ] Compatibilidad dual de hashing (Bcrypt + Werkzeug de base de datos existente).
