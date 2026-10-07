# Sprint 03: Integración End-to-End de Autenticación (Frontend React + Backend FastAPI)

> **Módulo:** Autenticación, JWT, 2FA y Control de Acceso  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (React 19 + Vite en `http://localhost:5173`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI en `http://localhost:8000/api/v1`)  
> **Base de Datos:** PostgreSQL 17 / SQLite Local ([`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql) & [`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db))  
> **Estado del Sprint:** ✅ **COMPLETADO Y CERTIFICADO END-TO-END**

---

## 1. Resumen Ejecutivo del Hito Alcanzado

Se logró conectar exitosamente la arquitectura desacoplada de CargaExpress Perú. El flujo de autenticación, verificación de doble factor (2FA/TOTP), almacenamiento seguro de credenciales JWT y protección de rutas administrativas quedó **100% operativo y probado en vivo** desde el navegador hasta la base de datos relacional.

```text
┌────────────────────────┐      HTTP POST /login      ┌────────────────────────┐      SQLAlchemy ORM      ┌────────────────────────┐
│   CargaExpressFront    │ ─────────────────────────> │   CargaExpressBackend  │ ───────────────────────> │  cargaexpress.db / PG  │
│  (React 19 + Vite)     │ <───────────────────────── │     (FastAPI API)      │ <─────────────────────── │  (Tablas Normalizadas) │
│                        │       temp_token + QR      │                        │     Usuario + Hash OK    └────────────────────────┘
│                        │                            │                        │
│   Escaneo de QR con    │       HTTP POST /2fa       │                        │      INSERT INTO         ┌────────────────────────┐
│  Google Authenticator  │ ─────────────────────────> │     Valida pyotp       │ ───────────────────────> │  auditoria_seguridad   │
│   (Código 6 dígitos)   │ <───────────────────────── │    y emite JWTs        │ <─────────────────────── │ (Pistas Inmutables)    │
│                        │     Access/Refresh Token   └────────────────────────┘                          └────────────────────────┘
│                        │
│ Redirige a /dashboard  │
│  con Sesión Iniciada   │
└────────────────────────┘
```

---

## 2. Componentes Implementados y Certificados

### 2.1. Frontend (`CargaExpressFront`)
| Archivo | Funcionalidad Clave Certificada |
| :--- | :--- |
| [`src/services/authService.js`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/authService.js) | Cliente HTTP con control de Envelope, tokens Bearer y captura de excepciones. |
| [`src/context/AuthContext.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/context/AuthContext.jsx) | Gestión reactiva de tokens (`localStorage`), token temporal y código QR de vinculación (`sessionStorage`). |
| [`src/pages/auth/Login.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/auth/Login.jsx) | Formulario con feedback visual, detección automática de MFA requerido y redirección al paso 2. |
| [`src/pages/auth/Verificacion2FA.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/auth/Verificacion2FA.jsx) | **Visualizador interactivo de Código QR en pantalla** para Google Authenticator, clave manual y validación en 2 clics. Redirección protegida al dashboard sin condiciones de carrera. |
| [`src/components/layout/AdminLayout.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/components/layout/AdminLayout.jsx) | Panel protegido que muestra nombre real del usuario (`Administrador CargaExpress`), iniciales (`AC`), rol asignado y botón de cierre de sesión con revocación en servidor. |

### 2.2. Backend (`CargaExpressBackend`)
| Archivo | Funcionalidad Clave Certificada |
| :--- | :--- |
| [`app/core/security.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/core/security.py) | Criptografía con Bcrypt, soporte legado Werkzeug, generación de QR en Base64 (`generate_qr_base64`) y validación TOTP (`pyotp`). |
| [`app/services/auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | Lógica de 2 fases, generación de QR durante el login, emisión de tokens con scope (`mfa_pending`) y emisión final de JWT. |
| [`app/api/v1/endpoints/auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | Endpoints `/login`, `/2fa`, `/refresh`, `/me`, `/2fa/setup`, `/2fa/confirm`, `/logout`. |
| [`init_local_db.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/init_local_db.py) | Script de aprovisionamiento inmediato que inicializa SQLite con las tablas 3NF y usuarios semilla listos con Bcrypt. |

---

## 3. Pruebas Reales Ejecutadas y Resultados

### Caso 1: Detección de Contraseña Errónea y Auditoría de Seguridad
* **Entrada:** DNI `82922603` con contraseña incorrecta.
* **Respuesta API:** `HTTP 401 Unauthorized`.
* **Registro en Base de Datos:**
  ```sql
  INSERT INTO auditoria_seguridad (usuario_id, evento, nivel_riesgo)
  VALUES (2, 'LOGIN_FALLIDO_PASSWORD_INCORRECTO', 'WARN');
  ```
* **Interfaz de Usuario:** Alerta roja con mensaje amigable sin exponer información sensible interna.

### Caso 2: Login con 2FA y Escaneo de Código QR (Administrador)
* **Entrada:** DNI `79665184` + Contraseña `password123`.
* **Respuesta Paso 1:** `HTTP 200 OK` con `mfa_requerido = true`, `temp_token` y código QR Base64.
* **Frontend:** Redirección a `/auth/2fa`, despliegue de imagen QR en pantalla para escaneo con Google Authenticator.
* **Validación Paso 2:** Ingreso de 6 dígitos producidos por la app móvil.
* **Respuesta Paso 2:** `HTTP 200 OK` emitiendo `access_token` y `refresh_token`.
* **Registro en Base de Datos:**
  ```sql
  INSERT INTO auditoria_seguridad (usuario_id, evento, detalles, nivel_riesgo)
  VALUES (1, '2FA_EXITOSO_SESION_INICIADA', '{"metodo": "TOTP"}', 'INFO');
  ```
* **Resultado:** Redirección automática al Dashboard administrativo desplegando la sesión del Administrador.

---

## 4. Estado de Cumplimiento OWASP en este Sprint

* [x] **A01: Broken Access Control:** Rutas `/admin/*` inaccesibles sin Bearer Token válido.
* [x] **A02: Cryptographic Failures:** Contraseñas hasheadas con Bcrypt; JWTs firmados con HS256 y secretos de 64 caracteres.
* [x] **A07: Identification and Authentication Failures:** Soporte TOTP (RFC 6238) nativo y anti-fuerza bruta con contador de intentos.
* [x] **A09: Security Logging and Monitoring:** Registro inmutable de cada intento y éxito de autenticación en `auditoria_seguridad`.
* [x] **API2: Broken Authentication:** Separación de tokens (Access 30 min, Refresh 7 días, Temp 5 min) con rotación y control de versión de sesión.
