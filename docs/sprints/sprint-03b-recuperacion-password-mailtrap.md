# Sprint 03B: Recuperación Segura de Contraseña con Mailtrap API y Flujo 2FA

> **Módulo:** Autenticación y Recuperación de Credenciales (`/api/v1/auth/recuperar-password` & `/restablecer-password`)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (React 19 + Vite)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + Mailtrap SDK + SQLAlchemy 2.0)  
> **Canal de Correo:** Mailtrap Email Sandbox (API HTTPS / Inbox `4950980`)  
> **Estado del Sprint:** ✅ **100% COMPLETADO Y CERTIFICADO END-TO-END**

---

## 1. Arquitectura del Flujo de Recuperación

```text
  [ CLIENTE / FRONTEND ]                     [ FASTAPI API ]                          [ MAILTRAP SANDBOX ]
           │                                        │                                          │
           │ 1. POST /auth/recuperar-password       │                                          │
           │    { "identificador": DNI o Email }    │                                          │
           ├───────────────────────────────────────>│ 2. Busca usuario y genera token JWT       │
           │                                        │    (scope="password_reset", 15 min)      │
           │                                        │ 3. Envía email vía MailtrapClient API    │
           │                                        ├─────────────────────────────────────────>│
           │ 4. 200 OK                              │                                          │
           │    { "solicitud_procesada": true }     │                                          │
           │<───────────────────────────────────────┤                                          │
           │                                                                                   │
           │                                        5. Usuario abre email y hace clic          │
           │<──────────────────────────────────────────────────────────────────────────────────┤
           │
           │ 6. Carga /auth/restablecer-password?token=...
           │    Ingresa: Nueva contraseña (+ TOTP 6 dígitos si tiene 2FA)
           │
           │ 7. POST /auth/restablecer-password
           │    { token, nueva_password, codigo_totp }
           ├───────────────────────────────────────>│ 8. Valida token JWT y sesion_version
           │                                        │ 9. Valida TOTP si corresponde (pyotp)
           │                                        │ 10. Actualiza Bcrypt hash y sesion_version++
           │                                        │ 11. Registra en auditoria_seguridad
           │ 12. 200 OK                             │
           │<───────────────────────────────────────┤
           │
           │ 13. Redirige a /auth/login listo para iniciar sesión
```

---

## 2. Controles de Seguridad OWASP Aplicados

1. **OWASP API3: Protección contra Enumeración de Usuarios:**
   * La respuesta pública de `POST /auth/recuperar-password` es idéntica si el usuario existe o no, impidiendo que terceros determinen qué DNIs o correos están dados de alta.
2. **Token de Un Solo Uso (Anti-Replay):**
   * El token contiene la claim `"sesion_version": usuario.sesion_version`.
   * En cuanto se aplica la nueva contraseña, `sesion_version += 1`, invalidando inmediatamente el token de recuperación y cerrando cualquier sesión activa en otros navegadores.
3. **Doble Capa de Verificación si el Usuario tiene 2FA Activo:**
   * Si la cuenta tiene configurado Google Authenticator, se exige el código de 6 dígitos para autorizar el cambio de contraseña.
4. **Política Estricta de Complejidad de Contraseña (NIST SP 800-63B / OWASP):**
   * Longitud mínima: 8 caracteres.
   * Obligatorio: Letras mayúsculas `[A-Z]`, minúsculas `[a-z]`, números `[0-9]` y caracteres especiales `[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\/~`]`.
   * Feedback reactivo en Frontend con medidor de fortaleza de 5 puntos y lista de requisitos en tiempo real.
   * Validación estricta en Backend con Pydantic v2 `field_validator`.
5. **Alineación Visual y Diseño Responsivo (100% Homogéneo al Login):**
   * Integración de `form-panel`, `curved-divider` y `mobile-cover` idéntico a `Login.jsx` y `Verificacion2FA.jsx`.
   * Vista optimizada para monitores de escritorio (PC) y dispositivos móviles.
6. **Transporte Seguro HTTPS:**
   * La integración con Mailtrap Sandbox se ejecuta mediante API REST HTTPS sobre el puerto 443, inmune a bloqueos de puertos SMTP tradicionales.
7. **Trazabilidad y Auditoría Inmutable:**
   * Eventos auditados: `RECUPERACION_PASSWORD_SOLICITADA`, `PASSWORD_RESTABLECIDO_EXITOSO`, `RESTABLECER_PASSWORD_TOKEN_REUTILIZADO_RECHAZADO`.

---

## 3. Componentes Implementados

| Archivo | Rol y Funcionalidad |
| :--- | :--- |
| [`app/core/config.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/core/config.py) | Parámetros `MAILTRAP_API_TOKEN`, `MAILTRAP_INBOX_ID`, `RESET_TOKEN_EXPIRE_MINUTES`. |
| [`app/services/email_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/email_service.py) | Cliente de Mailtrap SDK y plantilla HTML corporativa de CargaExpress Perú. |
| [`app/core/security.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/core/security.py) | Emisión de token temporal `create_password_reset_token`. |
| [`app/schemas/auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/schemas/auth.py) | DTOs `SolicitarRecuperacionSchema` y `RestablecerPasswordSchema`. |
| [`app/services/auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | Lógica de emisión, envío y restablecimiento atómico. |
| [`app/api/v1/endpoints/auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | Endpoints `/recuperar-password` y `/restablecer-password`. |
| [`src/services/authService.js`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/authService.js) | Métodos cliente `solicitarRecuperacionPassword` y `restablecerPassword`. |
| [`src/pages/auth/RecuperarPassword.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/auth/RecuperarPassword.jsx) | Formulario reactivo para solicitud con feedback y visualización de estado. |
| [`src/pages/auth/RestablecerPassword.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/auth/RestablecerPassword.jsx) | Formulario con validación de contraseñas, soporte 2FA y redirección automática. |
| [`src/pages/auth/Login.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/auth/Login.jsx) | Enlace activado hacia `/auth/recuperar-password`. |
| [`src/routes/AppRouter.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/routes/AppRouter.jsx) | Registro de rutas en React Router. |
