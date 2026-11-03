# 07. Gestión de Sesiones JWT, Control de Expiración e Interceptores HTTP

> **Estándar:** OWASP ASVS v4.0 (V3: Session Management) / OWASP API Security 2023 (API2: Broken Authentication)  
> **Componentes Afectados:**  
> - Frontend: `CargaExpressFront` (`src/utils/token.js`, `src/services/apiClient.js`, `src/context/AuthContext.jsx`, `src/components/layout/AdminLayout.jsx`, `src/pages/auth/Login.jsx`)  
> - Backend: `CargaExpressBackend` (`app/api/deps.py`, `app/core/security.py`, `app/api/v1/endpoints/auth.py`)  
> **Fecha de Implementación:** Octubre 2026  
> **Estado:** ✅ **SUPERADO Y VERIFICADO EN PRODUCCIÓN/DEV**

---

## 1. Contexto y Diagnóstico del Incidente

### 1.1. Síntoma Reportado
Al acceder al sistema con un token JWT ya vencido en el almacenamiento del navegador (`localStorage`), la aplicación frontend permitía el ingreso visual a la ruta protegida `/admin/dashboard`. Una vez dentro del panel administrativo, las tarjetas de métricas se mostraban vacías (`S/ 0.00`, `0 envíos`) y la interfaz presentaba una alerta roja de error:
> *"Credenciales de autenticación inválidas o sesión expirada."*

El usuario no era expulsado ni redirigido a la pantalla de inicio de sesión (`/auth/login`), lo que representaba un fallo de experiencia de usuario y de seguridad en el ciclo de vida de la sesión (OWASP API2:2023).

### 1.2. Análisis de Causa Raíz (RCA)
1. **Verificación Superficial en `AuthContext.jsx`:**
   El estado `isAuthenticated` se inicializaba exclusivamente mediante la comprobación de existencia de la cadena:
   ```javascript
   // CÓDIGO VULNERABLE ANTERIOR
   const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('ce_access_token'));
   ```
   No se examinaba el payload interno del token ni el claim estándar de expiración (`exp`), considerando válido cualquier token por el simple hecho de existir en el almacenamiento local.
2. **Efecto Rebote en `Login.jsx`:**
   En la vista de login, un efecto de navegación redirigía al dashboard si `isAuthenticated` era verdadero:
   ```javascript
   useEffect(() => {
     if (isAuthenticated) navigate('/admin/dashboard', { replace: true });
   }, [isAuthenticated]);
   ```
   Al intentar iniciar sesión, el usuario era repelido hacia el dashboard con el token caducado anterior.
3. **Ausencia de Interceptor HTTP Global:**
   Los servicios API consumían `fetch` de manera independiente sin un interceptor global que reaccionara ante respuestas `401 Unauthorized` del backend. El error era simplemente capturado como un mensaje de texto plano en lugar de disparar una invalidación y redirección forzosa.

---

## 2. Arquitectura de la Solución Implementada

La solución adopta un enfoque de **defensa en profundidad** con dos capas de validación: **proactiva (cliente)** y **reactiva (servidor/interceptor)**.

```
       [ Navegador / Usuario ]
                  │
        (Acceso a /admin/*)
                  │
     ┌────────────▼─────────────┐
     │ ¿Token expiró en cliente?│── SÍ ──► [ Purgar LocalStorage ]
     │ (isTokenExpired() < now) │                   │
     └────────────┬─────────────┘                   ▼
                  │ NO                  [ Redirigir a /auth/login?expired=1 ]
                  ▼
     ┌──────────────────────────┐
     │ Ejecutar Petición API    │
     │ con Bearer Token         │
     └────────────┬─────────────┘
                  │
     ┌────────────▼─────────────┐
     │ ¿Backend responde 401?   │── SÍ ──► [ Interceptor apiClient.js ]
     │ (Sesión revocada o firma)│                   │
     └────────────┬─────────────┘                   ▼
                  │ NO                  [ Purgar credenciales y evento ce_session_expired ]
                  ▼                                 │
     [ Renderizar Métricas OK ]                     ▼
                                        [ Redirigir a /auth/login?expired=1 ]
```

---

## 3. Especificación de Componentes Modificados

### 3.1. Utilidad Criptosegura de Validación JWT (`src/utils/token.js`)
Decodifica en Base64 URL el payload del token y evalúa el claim `exp` en milisegundos contra el reloj actual, incorporando un margen de seguridad (*clock skew*) de 5 segundos:
```javascript
export function isTokenExpired(token, bufferSeconds = 5) {
  const payload = decodeJwt(token);
  if (!payload || typeof payload.exp !== 'number') return true;
  const expirationMs = payload.exp * 1000;
  const nowWithBufferMs = Date.now() + (bufferSeconds * 1000);
  return nowWithBufferMs >= expirationMs;
}
```

### 3.2. Cliente HTTP Centralizado con Interceptor 401 (`src/services/apiClient.js`)
Unifica todas las llamadas fetch del frontend.
- **Antes de enviar:** Si el token ya venció, cancela la solicitud, limpia el almacenamiento y redirige.
- **Al recibir respuesta:** Si el código HTTP es `401`, ejecuta `forzarCierrePorSesionExpirada()`, limpia almacenamiento y envía a `/auth/login?expired=1`.
- Migración de servicios: `dashboardService`, `envioService`, `usuarioService`, `clienteService` y `authService` ahora consumen exclusivamente este cliente.

### 3.3. Sincronización Reactiva en `AuthContext.jsx`
- Al inicializar, ejecuta `getInitialToken()`: si el token expiró, limpia `localStorage` y define `isAuthenticated = false` y `user = null`.
- Registra un listener al evento custom de ventana `'ce_session_expired'` para reflejar la pérdida de sesión en toda la jerarquía de React inmediatamente.

### 3.4. Guarda Estricta en `AdminLayout.jsx`
- Si el usuario no está autenticado o su token ha vencido, el layout **no monta ni renderiza los componentes hijos** (`<Outlet />`). Esto evita que se disparen llamadas fallidas a endpoints protegidos.
- Muestra una pantalla transitoria de carga mientras redirige a login con parámetro `?expired=1`.

### 3.5. Alerta Amigable en `Login.jsx`
- Detecta el parámetro `?expired=1` en la URL y muestra un banner amigable informando el motivo:
  > *🕒 Tu sesión anterior ha expirado por seguridad. Ingresa tus credenciales para renovarla.*
- Al ingresar credenciales correctas, el backend emite un token de 30 minutos nuevo, ingresando exitosamente al panel operativo.

---

## 4. Matriz de Pruebas de Verificación

| ID Caso | Escenario de Prueba | Comportamiento Esperado | Resultado |
|---|---|---|---|
| **SEC-SES-01** | Acceso directo a `/admin/dashboard` con token expirado en `localStorage`. | No carga el dashboard; purga `localStorage` y redirige de inmediato a `/auth/login?expired=1`. | **PASÓ** ✅ |
| **SEC-SES-02** | Expiración de token mientras el usuario navega en el panel. | El primer request recibe HTTP 401, el interceptor limpia credenciales y redirige a login. | **PASÓ** ✅ |
| **SEC-SES-03** | Intento de entrar a `/auth/login` teniendo un token caducado en caché. | No hace rebote hacia `/admin/dashboard`; limpia el estado y muestra el formulario de inicio de sesión con aviso. | **PASÓ** ✅ |
| **SEC-SES-04** | Inicio de sesión con usuario administrador válido sin MFA. | Genera token nuevo con 30 min de vigencia, redirige al dashboard y carga todas las métricas en verde sin alertas rojas. | **PASÓ** ✅ |
