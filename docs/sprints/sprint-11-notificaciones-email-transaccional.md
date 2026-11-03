# Sprint 11: Motor de Notificaciones por Correo Electrónico Real (SMTP TLS / Gmail)

> **Módulos:** 
> 1. Motor Híbrido de Envíos Transaccionales (`app/services/email_service.py`)
> 2. Disparadores del Ciclo de Vida: Pre-registro Web, Admisión en Balanza y Entrega de Encomienda
> 3. Seguridad de Acceso: Recuperación de Contraseña con enlace temporal firmado  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + `smtplib` TLS nativo + SQLAlchemy 2.0)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (React 19 + Vite)  
> **Proveedor Principal de Producción/Pruebas:** Gmail SMTP con Contraseña de Aplicación (Coste S/ 0.00)  
> **Proveedores Secundarios (Fallbacks):** Resend API, Mailtrap Sandbox, Registro Estructurado en Consola  
> **Estado del Sprint:** ✅ **100% IMPLEMENTADO Y CERTIFICADO E2E CON GMAIL SMTP REAL**

---

## 1. Justificación y Objetivos de Negocio

El objetivo del **Sprint 11** es dotar a **CargaExpress Perú** de un sistema de notificaciones por correo electrónico que llegue a **bandejas de entrada reales** (Gmail, Outlook, Yahoo, correos institucionales universitarios), sin costo alguno para el equipo y con las máximas garantías de seguridad criptográfica y privacidad de datos.

### Beneficios Clave:
1. **Impacto Inmediato en la Sustentación:** Durante la exposición en vivo, el docente o jurado puede ingresar su correo personal en el cotizador o registro web, y recibir en menos de 5 segundos el correo oficial de CargaExpress con su código de seguimiento y QR.
2. **Cero Dependencia de Dominios de Pago:** El uso del canal SMTP autenticado de Google permite enviar hasta 500 correos reales al día sin comprar dominios `.pe` ni contratar servidores de correo de pago.
3. **Resiliencia Operativa (Patrón Estrategia):** Si la red se desconecta o falla el proveedor SMTP, el sistema no interrumpe la transacción de la encomienda ni arroja error 500 al cliente; conmuta automáticamente a fallback seguro en log para auditoría.

---

## 2. Arquitectura del Flujo de Notificaciones

```text
┌────────────────────────┐
│ DISPARADOR EN FASTAPI  │
│ (Endpoints de Negocio) │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     EMAIL SERVICE      │ ──► Evalúa variables configuradas en .env
│(Patrón Estrategia SDD) │
└───────────┬────────────┘
            │
            ├─────────────────────────────────────────────┐
            │ (Si SMTP_HOST = 'smtp.gmail.com')           │ (Si no hay SMTP configurado)
            ▼                                             ▼
┌────────────────────────┐                   ┌────────────────────────┐
│   GMAIL SMTP (TLS)     │                   │  FALLBACK DE SEGURIDAD │
│  Puerto 587 STARTTLS   │                   │  (Mailtrap / Consola)  │
└───────────┬────────────┘                   └────────────────────────┘
            │
            ▼
┌────────────────────────┐
│   BANDEJA DEL CLIENTE  │
│(Gmail / Outlook Móvil) │
└────────────────────────┘
```

---

## 3. Matriz de Notificaciones Transaccionales del Sistema

| Evento de Negocio | Disparador API Backend | Destinatario | Asunto del Correo | Contenido Principal del Correo |
| :--- | :--- | :--- | :--- | :--- |
| **1. Pre-registro Web Exitoso** | `POST /api/v1/publico/pedidos/registrar` | Remitente y Destinatario | *CargaExpress - Pre-registro Exitoso [CE-2026-XXXX]* | Código de tracking, agencia origen/destino, tarifa estimada, enlace de seguimiento y recordatorio de acercarse a agencia. |
| **2. Admisión en Balanza y Pago** | `POST /api/v1/envios/{id}/recepcionar` | Remitente | *CargaExpress - Encomienda Recepcionada y Pagada* | Confirmación de flete pagado en mostrador, medidas de balanza certificadas, desglose IGV 18% SUNAT y número de boleta. |
| **3. En Reparto Domiciliario** | `POST /api/v1/envios/{id}/iniciar-reparto` | Destinatario | *CargaExpress - ¡Tu encomienda va en camino!* | Aviso de salida a ruta de última milla, nombre del courier asignado y dirección de entrega confirmada. |
| **4. Encomienda Entregada Conforme** | `POST /api/v1/envios/{id}/entregar` o `/entregar-domicilio` | Remitente y Destinatario | *CargaExpress - Encomienda Entregada con Éxito* | Notificación de entrega con DNI del receptor, hora exacta y cierre de la cadena de custodia. |
| **5. Seguridad: Recuperación de Acceso**| `POST /api/v1/auth/solicitar-recuperacion` | Colaborador / Usuario | *CargaExpress - Restablecimiento de Contraseña* | Enlace único de un solo uso con expiración a los 15 minutos (anti-enumeración). |

---

## 4. Marco de Seguridad y Normativas Aplicadas (OWASP & RFC)

Para blindar el servidor y cumplir con las mejores prácticas de seguridad informática:

1. **Protección Criptográfica en Tránsito (OWASP API8 / A02: Cryptographic Failures):**
   * Conexión obligatoria con **STARTTLS sobre puerto 587** o **SSL sobre puerto 465**, cifrando la comunicación entre el backend FastAPI y los servidores de correo. Queda prohibido el puerto 25 sin cifrar.
2. **Prevención de Inyección de Cabeceras (CRLF / Email Header Injection):**
   * Sanitización estricta de variables de entrada (`destinatario_email`, `asunto`) eliminando caracteres de salto de línea `\r` y `\n` para evitar que un atacante inyecte cabeceras maliciosas (`Bcc:`, `Cc:`).
3. **Aislamiento Absoluto de Secretos (OWASP A05: Security Misconfiguration):**
   * La contraseña de aplicación de 16 caracteres jamás se escribe en el código fuente. Se inyecta exclusivamente mediante variables de entorno en el archivo `.env` (el cual está ignorado en `.gitignore`).
4. **Protección contra Anti-Spam y Phishing:**
   * Las plantillas HTML utilizan estilos CSS inline, sin etiquetas `<script>` ni elementos externos sospechosos, garantizando que el correo ingrese a la **Bandeja Principal** y no a la carpeta de Correo No Deseado / Spam.
5. **No Bloqueo del Hilo Principal (Asincronía / Background Tasks):**
   * El envío de correos se procesa en segundo plano (`FastAPI BackgroundTasks` o sub-proceso) para que la respuesta HTTP al usuario sea instantánea ($< 200\text{ ms}$) y no espere la latencia de red del servidor SMTP.

---

## 5. Especificación de Parámetros en `.env`

El backend soportará las siguientes variables en el archivo `.env`:

```env
# ==============================================================================
# CONFIGURACIÓN DE CORREO TRANSACCIONAL REAL (SMTP GMAIL)
# ==============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo_personal@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
SMTP_FROM_NAME=CargaExpress Perú
SMTP_FROM_EMAIL=tu_correo_personal@gmail.com
EMAIL_ENABLED=true

# ==============================================================================
# FALLBACK SECUNDARIO (MAILTRAP SANDBOX)
# ==============================================================================
MAILTRAP_API_TOKEN=
MAILTRAP_INBOX_ID=4950980
FRONTEND_URL=http://localhost:5173
```

---

## 6. ¿Qué Necesitas Hacer Tú Antes de Implementar? (Paso a Paso)

Para poder probar el envío de correos con tu propia cuenta de Gmail en menos de 3 minutos:

### Paso 1: Activar la Verificación en 2 Pasos de tu Cuenta de Google
1. Entra a tu navegador e inicia sesión en [Google Account Security](https://myaccount.google.com/security).
2. En la sección **"Cómo inicias sesión en Google"**, asegúrate de que la **Verificación en dos pasos** esté activada. (Si ya la tienes activada, pasa al Paso 2).

### Paso 2: Generar tu Contraseña de Aplicación de 16 letras
1. En la barra de búsqueda de tu cuenta de Google, escribe: **Contraseñas de aplicaciones**  
   *(O accede directo a: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords))*.
2. Te pedirá confirmar tu contraseña habitual de Gmail.
3. En el campo *"Nombre de la aplicación"*, escribe: **`CargaExpress`** y presiona **Crear**.
4. Google te mostrará una ventana con una clave amarilla de **16 caracteres** dividida en 4 grupos (ejemplo: `xyza bcde fghi jklm`).
5. **Copia esa clave de 16 caracteres** (sin espacios o con espacios, el backend la procesa igual).

### Paso 3: Guardar en el `.env`
Esa clave de 16 caracteres es la que colocaremos en la variable `SMTP_PASSWORD` de tu `.env`.  
*(Nota de seguridad: Nunca compartas esa clave en repositorios públicos de GitHub; se mantiene privada en tu máquina local).*

---

## 7. Criterios de Aceptación (Checklist de Validación SDD)

- [x] **Envío Real:** Al solicitar recuperación de contraseña y pre-registro web, el correo llega a la bandeja de entrada de Gmail en $< 5\text{ segundos}$ (`metodo: smtp_tls_real`).
- [x] **Diseño Responsivo:** El correo se visualiza con diseño corporativo institucional en la app móvil de Gmail y en la versión web de escritorio.
- [x] **Resiliencia (Fallback):** Si se ingresa una contraseña SMTP errónea o se corta internet, el endpoint de FastAPI no se cae con error 500; conmuta al fallback seguro de Mailtrap o consola.
- [x] **Seguridad OWASP:** Cabeceras de correo sanitizadas contra inyección CRLF y tokens con expiración forzada de 15 minutos.

