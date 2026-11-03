# ✉️ Guía Técnica de Exposición 05: Notificaciones Transaccionales por Correo Electrónico

Esta guía documenta la arquitectura, el protocolo de entrega y el diagnóstico del subsistema de **Notificaciones por Correo Electrónico en Tiempo Real** de **CargaExpress Perú**.

---

## 1. Arquitectura del Motor Híbrido de Envíos (Patrón Estrategia)

El sistema implementa un motor resiliente de 3 capas para garantizar que ninguna notificación crítica se pierda y que la experiencia de usuario sea fluida:

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

## 2. Eventos Transaccionales Disponibles

| Evento | Función Backend | Destinatarios | Propósito Operativo |
| :--- | :--- | :--- | :--- |
| **Pre-registro Web Remitente** | `enviar_correo_preregistro` | Remitente (`rem_email`) | Confirmación con código de tracking para presentar en balanza de agencia. |
| **Pre-registro Web Destinatario** | `enviar_correo_preregistro_destinatario` | Destinatario (`dest_email`) | Alerta de que tiene una encomienda programada a su nombre con enlace de seguimiento. |
| **Recepción en Balanza / Admisión** | `enviar_correo_cambio_estado` | Remitente y Destinatario | Notifica que el paquete fue pesado y admitido formalmente en agencia origen. |
| **Despacho Interprovincial (En Ruta)** | `enviar_correo_cambio_estado` | Remitente y Destinatario | Alerta de salida de camión y tránsito por carretera nacional. |
| **Llegada a Agencia Destino** | `enviar_correo_cambio_estado` | Destinatario | Notifica que el paquete está disponible en mostrador para retiro con DNI. |
| **Entrega Conforme** | `enviar_correo_cambio_estado` | Remitente y Destinatario | Confirmación de entrega con nombre y parentesco del receptor. |
| **Incidencia Grave / Siniestro** | `enviar_correo_cambio_estado` | Remitente y Destinatario | Alerta de congelamiento por siniestro, accidente o asalto con tipificación y denuncia policial PNP. Estilo de cabecera en rojo `#dc2626`. |
| **Restablecimiento de Clave** | `enviar_correo_recuperacion` | Usuario interno/externo | Token seguro JWT de 15 minutos de caducidad (OWASP A07). |

---

## 3. Consideraciones Técnicas Críticas y Diagnóstico

### 3.1 Codificación de Cabeceras RFC 2047 (Caracteres UTF-8)
En servidores SMTP con TLS estricto como Gmail:
* Los nombres que contengan tildes o caracteres especiales (ej. `"CargaExpress Perú"`, `"José"`, o `"Actualización de Envío"`) **deben** estar encapsulados con `email.header.Header(..., "utf-8")`.
* Si se transmiten como texto plano en el protocolo SMTP, el servidor puede emitir `UnicodeEncodeError: 'ascii' codec can't encode character` y conmutar automáticamente al Sandbox de Mailtrap.
* Se implementó `_sanitizar_header` con eliminación de comillas anidadas (`strip('"').strip("'")`) y el método `servidor.send_message(mensaje)` nativo de Python para compatibilidad completa con UTF-8.

### 3.2 ¿Dónde verificar la llegada de correos?
1. **Cuenta remitente autorizada:** En `.env`, `SMTP_USER` está vinculado a la cuenta emisora (`luismoralesmendezhumberto@gmail.com`). 
2. **Carpeta "Enviados" de Gmail:** Cualquier correo emitido exitosamente mediante la App Password de Google se refleja automáticamente en la carpeta de *Enviados* de `luismoralesmendezhumberto@gmail.com`.
3. **Bandeja de Entrada vs Spam:** Dado que es un servidor en desarrollo sin registros SPF/DKIM vinculados a un dominio corporativo propio (`@cargaexpress.pe`), los proveedores como Gmail pueden clasificar la primera recepción en la pestaña **Spam** o **Promociones**.
4. **Cuentas distintas:** El remitente y el destinatario ingresados en el formulario (`luish.morales.dev@gmail.com` y `cesarvallejocesar@gmail.com`) recibirán sus correos en sus respectivas cuentas personales, no en la cuenta del servidor salvo que coincidan.

### 3.3 Desacoplamiento Asíncrono con FastAPI BackgroundTasks (Regla del Boy Scout)
Para no bloquear el tiempo de respuesta del servidor ni la fluidez de la interfaz de usuario (cajeros en ventanilla, operadores de almacén o couriers):
* El despacho de correos se desacopló del ciclo síncrono HTTP mediante `fastapi.BackgroundTasks`.
* El endpoint HTTP valida la transacción en base de datos (`commit`), retorna inmediatamente un `HTTP 200 OK` al frontend en milisegundos (< 30ms) y delega la conexión SMTP y el envío del correo en segundo plano (*fire-and-forget* seguro).

