# ✉️ Guía Técnica de Exposición 05: Notificaciones Transaccionales y Motor de Correo

Esta guía documenta la arquitectura técnica, las **rutas HTTP**, los **servicios involucrados** y las **funciones de código exactas** que orquestan el subsistema de correos electrónicos en **CargaExpress Perú**.

---

## 1. Arquitectura del Motor Híbrido de Envíos (Patrón Estrategia Resiliente)

El envío de correos opera bajo un principio de **alta resiliencia y desacoplamiento**: si el servidor SMTP falla o la conexión a internet de la agencia fluctúa, **la transacción operativa en la base de datos NUNCA se cancela**. El correo se procesa con captura segura de excepciones.

```text
                               ┌────────────────────────────────┐
                               │  Evento Transaccional Disparado │
                               │ (Pre-registro, Recepción, etc.)│
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                             ┌──────────────────────────────────┐
                             │    1. Servidor SMTP Real         │
                             │ (Gmail STARTTLS Puerto 587)      │
                             └─────────┬──────────────┬─────────┘
                                       │              │
                                  ¿Éxito?         ¿Fallo?
                                       │              │
                       ┌───────────────┘              └────────────────┐
                       ▼                                               ▼
     ┌──────────────────────────────────┐            ┌──────────────────────────────────┐
     │ Correo entregado a bandejas      │            │ 2. Sandbox Mailtrap API          │
     │ reales (Gmail, Outlook, etc.)    │            │ (Bandeja de Pruebas Seguras)     │
     └──────────────────────────────────┘            └─────────┬──────────────┬─────────┘
                                                               │              │
                                                          ¿Éxito?         ¿Fallo?
                                                               │              │
                                               ┌───────────────┘              └────────┐
                                               ▼                                       ▼
                             ┌──────────────────────────────────┐    ┌──────────────────────────────────┐
                             │ Correo interceptado en           │    │ 3. Fallback Consola              │
                             │ Sandbox Mailtrap ID: 4950980     │    │ (Impresión estructurada en logs) │
                             └──────────────────────────────────┘    └──────────────────────────────────┘
```

---

## 2. Mapa de Rutas HTTP, Servicios y Funciones de Correo

Para responder con solvencia ante el evaluador: *"¿En qué ruta se dispara el correo y qué función del código lo ejecuta?"*:

| Evento de Negocio | Ruta HTTP (FastAPI) | Archivo Controlador (`endpoints/`) | Capa de Servicio (`services/`) | Función Exacta de Correo (`email_service.py`) | Destinatario Principal |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pre-registro Web (Remitente)** | `POST /api/v1/publico/pedidos/registro` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `enviar_correo_preregistro(...)` | Remitente (`remitente.email`) |
| **Alerta Pre-registro (Destinatario)** | `POST /api/v1/publico/pedidos/registro` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `enviar_correo_preregistro_destinatario(...)` | Destinatario (`destinatario.email`) |
| **Recepción en Balanza y Cobro** | `POST /api/v1/envios/{id}/pesar-recepcionar` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `enviar_correo_cambio_estado(...)` | Remitente y Destinatario |
| **Despacho Troncal (En Ruta)** | `POST /api/v1/envios/despachar-lote` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `enviar_correo_cambio_estado(...)` | Ambos clientes |
| **Arribo a Bodega Destino** | `POST /api/v1/envios/{id}/recibir-agencia-destino` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `enviar_correo_cambio_estado(...)` | Destinatario (Aviso de retiro) |
| **Entrega en Domicilio (Courier)** | `POST /api/v1/envios/{id}/entregar-domicilio` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`courier_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py) | `enviar_correo_cambio_estado(...)` | Remitente (Confirmación entrega) |
| **Declaración de Siniestro** | `POST /api/v1/envios/{id}/declarar-siniestro` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `enviar_correo_cambio_estado(...)` | Ambos clientes (Alerta roja) |
| **Recuperación de Contraseña** | `POST /api/v1/auth/recuperar-password` | [`auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | [`auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | `enviar_correo_recuperacion(...)` | Usuario que solicita reset |

---

## 3. Explicación de Código: ¿Cómo opera cada función en `email_service.py`?

El archivo responsable es [`app/services/email_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/email_service.py). Se estructura en 4 funciones clave:

### 1. `_enviar_smtp_real(...)` (Línea 20):
Es el motor de transporte base. Utiliza la librería estándar de Python `smtplib` con protocolo seguro **STARTTLS en el puerto 587**:
* Sanitiza encabezados contra ataques de inyección **CRLF / Header Injection** (`_sanitizar_header`).
* Codifica en formato MIME multipart (`alternative`), adjuntando versión en texto plano y versión HTML con diseño corporativo.
* Codifica asunto y remitente en **UTF-8 nativo (RFC 2047)** para que las tildes y caracteres peruanos no aparezcan corruptos en la bandeja de entrada.

### 2. `enviar_correo_preregistro(...)` (Línea 110):
Se dispara cuando el cliente completa el formulario web en `PedidoNuevo.jsx`:
* Arma la plantilla HTML con el código de tracking en grande (`CE-2026-XXXXXXX`).
* Incluye un botón interactivo que redirige directamente a la URL de rastreo público.
* Adjunta el resumen de tarifas (Tarifa base S/ 8.00 + flete por kilo + IGV 18%).

### 3. `enviar_correo_cambio_estado(...)` (Línea 220):
Es la función camaleónica del sistema. Se adapta visualmente según el nuevo estado de la encomienda:
* Si el estado es `ENTREGADO`: Cabecera en verde `#10b981` felicitando la recepción conforme.
* Si el estado es `EN_AGENCIA_DESTINO`: Notifica la dirección de la sede provincial para retiro con DNI.
* Si el estado es `SINIESTRADO`: Cambia dinámicamente el banner a **rojo crítico `#dc2626`**, adjuntando el motivo oficial (accidente / asalto) y el número de denuncia policial para reclamo ante el seguro.

### 4. `enviar_correo_recuperacion(...)` (Línea 380):
* Genera el enlace con token criptográfico temporal JWT de 15 minutos (OWASP A07).
* Previene ataques de enumeración respondiendo siempre con éxito sin revelar si el correo existe o no en la base de datos.

---

## 4. Preguntas Típicas del Evaluador / Jurado

#### Pregunta 1: "¿Qué pasa si se cae el servicio de internet o falla el servidor de correo al momento de registrar un envío?"
> **Respuesta:**  
> *"El sistema implementa un bloque `try/except` desacoplado alrededor de la llamada de correo en la capa de servicios. Si la conexión SMTP se interrumpe o agota el timeout de 20 segundos, el error se captura en los logs del servidor y el envío se guarda exitosamente en la base de datos. La operativa en ventanilla nunca se detiene por fallas en el proveedor de correo externo."*

#### Pregunta 2: "¿Cómo evitan que el correo llegue a la carpeta de SPAM del cliente?"
> **Respuesta:**  
> *"Primero, se sanitizan los encabezados eliminando saltos de línea inyectados (`\r\n`). Segundo, se utiliza un remitente autenticado con dominio verificado y cifrado TLS 1.3. Tercero, el mensaje se despacha como `multipart/alternative`, incluyendo tanto el cuerpo HTML como la versión alternativa en texto plano, cumpliendo las buenas prácticas anti-spam de proveedores como Gmail y Microsoft Outlook."*
