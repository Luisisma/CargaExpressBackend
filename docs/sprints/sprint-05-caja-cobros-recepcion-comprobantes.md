# Sprint 05: Caja Chica, Recepción en Ventanilla, Agendamiento de Cobros y Notificaciones

> **Módulos:**
> 1. Control Financiero de Cajas (`/api/v1/caja/aperturar`, `/api/v1/caja/estado-actual`, `/api/v1/caja/cerrar`)
> 2. Recepción y Pesaje Oficial de Encomiendas (`/api/v1/envios/{id}/pesar-recepcionar`)
> 3. Cobro Presencial en Ventanilla (`/api/v1/caja/cobrar-presencial`)
> 4. Motor de Pago Digital Simulado y Webhooks (`/api/v1/pagos/webhook-simulado`)
> 5. Agendamiento de Cobros y Contraentrega (`/api/v1/publico/pedidos/agendar-cobro`)
> 6. Notificaciones Transaccionales por Correo Electrónico (`email_service.py` con Mailtrap/SMTP)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (`src/pages/admin/caja/CajaDashboard.jsx`, modal de cobro y QR simulado en `PedidoExitoso.jsx`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + SQLAlchemy 2.0 + Mailtrap SMTP)  
> **Persistencia:** Tablas `aperturas_caja`, `movimientos_caja`, `envios`, `historial_envios`  
> **Moneda Oficial:** Soles Peruanos (`PEN` / `S/`)  
> **Estado del Sprint:** 📋 **ESPECIFICADO Y LISTO PARA EJECUCIÓN (SDD)**

---

## 1. Justificación y Objetivos de Negocio

El Sprint 04 cerró con éxito el **Pre-registro de Encomiendas Web como Usuario Invitado** (generando el correlativo `CE-2026-NNNNN`).

El objetivo del **Sprint 05** es implementar el **ciclo completo de cobranza, agendamiento de cobros y comunicación automatizada con el cliente**:
1. **Recepción de Pagos:** Habilitar el cobro físico en agencia (Efectivo, Tarjeta POS, Yape/Plin verificado por cajero) y el cobro digital simulado con QR vía Webhook criptográfico.
2. **Agendamiento de Cobros (Contraentrega y Recojo):** Permitir diferir el cobro al destino (cobro contraentrega al destinatario) o agendar la fecha/franja horaria para recojo y pesaje en domicilio.
3. **Control Financiero de Caja:** Garantizar que todo ingreso en efectivo alimente la sesión activa de caja en Soles (`aperturas_caja` y `movimientos_caja`).
4. **Notificaciones por Correo Electrónico en Tiempo Real:** Enviar confirmaciones automáticas vía Mailtrap:
   * Constancia de Pre-registro y agendamiento de cobro con código de tracking.
   * Confirmación de pago recibido y comprobante fiscal (Boleta/Factura con IGV 18%).
   * Aviso de cobro pendiente al destinatario en encomiendas contraentrega.

```text
┌─────────────────────────────────┐
│     CLIENTE PRE-REGISTRADO      │ ──> CORREO 1: Constancia de orden y tracking
│     (Tracking CE-2026-NNNNN)    │
│     Estado: REGISTRADO          │
│     Estado Pago: PENDIENTE      │
└─────────────────────────────────┘
                 │
                 ├─── CANAL A: Acude a Ventanilla en Agencia
                 │    ┌──────────────────────────────────────────────┐
                 │    │ 1. Cajero busca tracking                     │
                 │    │ 2. Pesa en balanza oficial (recalcula precio)│
                 │    │ 3. Cobra (Efectivo / Yape / POS)             │
                 │    │ 4. POST /caja/cobrar-presencial              │
                 │    └──────────────────────────────────────────────┘
                 │
                 ├─── CANAL B: Pago Digital Simulado en App (QR Yape)
                 │    ┌──────────────────────────────────────────────┐
                 │    │ 1. Cliente pulsa "Pagar con Yape QR"         │
                 │    │ 2. Frontend despacha notificación firmada    │
                 │    │ 3. POST /pagos/webhook-simulado              │
                 │    └──────────────────────────────────────────────┘
                 │
                 └─── CANAL C: Agendamiento de Cobro Contraentrega
                      ┌──────────────────────────────────────────────┐
                      │ 1. lugar_pago = 'destino'                    │
                      │ 2. Carga viaja con cobro programado          │
                      │ 3. Cajero destino cobra antes de entregar    │
                      └──────────────────────────────────────────────┘
                                       │
                                       ▼
                      ┌──────────────────────────────────────────────┐
                      │           TRANSACCIÓN EN BASE DE DATOS       │
                      │ - envios.estado = 'recepcionado'             │
                      │ - envios.estado_pago = 'pagado'              │
                      │ - movimientos_caja (ingreso S/)              │
                      │ - historial_envios (hito emitido)            │
                      └──────────────────────────────────────────────┘
                                       │
                                       ▼
                     CORREO 2: Confirmación de Pago y Boleta SUNAT
```

---

## 2. Requerimientos Funcionales y Reglas de Negocio

### 2.1. Sesión de Caja Obligatoria (RBAC: Cajero / Administrador)
* Un usuario con rol `cajero` debe abrir su turno con un `saldo_inicial >= 0.00` antes de procesar cobros en ventanilla.
* Solo se permite una caja abierta activa por usuario simultáneamente.
* Cada cobro en efectivo genera un registro en `movimientos_caja` (`tipo = 'ingreso'`), actualizando el arqueo del cajero.

### 2.2. Agendamiento de Cobros (Contraentrega y Recojo a Domicilio)
* **Cobro Contraentrega (`lugar_pago = 'destino'`):**
  * El paquete viaja sin cobro previo en origen.
  * El estado de pago permanece como `pendiente`.
  * La encomienda se bloquea en la agencia de destino hasta que el destinatario liquide el total en ventanilla o al courier.
* **Agendamiento de Recojo en Domicilio:**
  * El cliente selecciona fecha (`fecha_recojo_programada`) y turno (`mañana: 09:00 - 13:00` o `tarde: 14:00 - 18:00`).
  * El courier acude con balanza portátil para verificar peso, calcular tarifa final y cobrar en puerta.
* **Ventana de Expiración:** Pre-registros no pagados ni agendados caducan automáticamente a las 48 horas hábiles (`estado = 'expirado'`).

### 2.3. Motor de Pago Digital Simulado vía Webhook (OWASP API Top 10)
* Emula pasarelas peruanas como Culqi o Niubiz:
  * El frontend simula el pago por QR Yape o Tarjeta de prueba.
  * Se emite una petición POST a `/api/v1/pagos/webhook-simulado`.
  * Validación obligatoria de la cabecera `X-Webhook-Signature` mediante HMAC-SHA256 con `WEBHOOK_SECRET_KEY`.
  * Validación de idempotencia con `transaction_id`.

### 2.4. Servicio de Notificaciones por Correo Electrónico (Mailtrap / SMTP)
Se implementan 3 plantillas HTML corporativas responsivas en `email_service.py`:
1. **Plantilla 1: Constancia de Pre-registro y Agendamiento de Cobro:**
   * Enviada al remitente inmediatamente tras el pre-registro.
   * Contenido: Código de tracking `CE-2026-NNNNN`, datos de ruta, tarifa estimada en Soles, instrucciones de entrega y fecha límite de vigencia.
2. **Plantilla 2: Confirmación de Pago y Comprobante Fiscal SUNAT:**
   * Enviada al remitente (y destinatario) cuando el pago pasa a `pagado`.
   * Contenido: Tipo de comprobante (Boleta/Factura), serie y número, desglose de Subtotal e IGV (18%), método de pago utilizado y enlace directo al seguimiento en vivo.
3. **Plantilla 3: Aviso de Cobro Contraentrega:**
   * Enviada al destinatario cuando el paquete llega a la agencia destino.
   * Contenido: Aviso de paquete listo para retiro, dirección de la agencia destino y monto exacto en Soles a abonar para recibir la carga.

---

## 3. Matriz de Endpoints a Implementar en el Backend

| Endpoint | Método | Acceso | Propósito | DTO / Esquema |
| :--- | :---: | :---: | :--- | :--- |
| `/api/v1/caja/aperturar` | `POST` | Cajero / Admin | Inicia el turno de caja con saldo base en Soles | `AperturaCajaRequest` &rarr; `AperturaCajaResponse` |
| `/api/v1/caja/estado-actual` | `GET` | Cajero / Admin | Consulta saldo actual, total ventas y movimientos | `EstadoCajaDTO` |
| `/api/v1/caja/cerrar` | `POST` | Cajero / Admin | Cierra el turno de caja con arqueo final | `CierreCajaRequest` &rarr; `CierreCajaResponse` |
| `/api/v1/caja/cobrar-presencial` | `POST` | Cajero / Admin | Procesa cobro físico (Efectivo/Yape/POS) y emite correo | `CobroPresencialRequest` &rarr; `CobroPresencialResponse` |
| `/api/v1/pagos/webhook-simulado` | `POST` | Público / HMAC | Webhook de pago digital QR con firma criptográfica | `WebhookPagoRequest` &rarr; `WebhookPagoResponse` |
| `/api/v1/envios/{id}/pesar-recepcionar` | `POST` | Cajero / Almacén | Valida pesaje oficial en balanza y recalcula precio | `PesajeOficialRequest` &rarr; `EnvioRecepcionadoDTO` |
| `/api/v1/publico/pedidos/{codigo}/agendar-cobro` | `POST` | Público | Programa fecha de recojo o fija pago contraentrega | `AgendarCobroRequest` &rarr; `AgendarCobroResponse` |
| `/api/v1/publico/pedidos/{codigo}/reenviar-correo` | `POST` | Público | Reenvía la constancia o comprobante por correo | `ReenviarCorreoRequest` &rarr; `SuccessResponse` |

---

## 4. Transformación del Frontend ([`CargaExpressFront`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront))

1. **Pantalla de Éxito ([`PedidoExitoso.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/PedidoExitoso.jsx)):**
   * Añadir modal interactivo **"Pagar con Yape QR Dinámico (Simulador)"** con temporizador y generación de número de operación.
   * Disparo automático del Webhook al confirmar el pago en pantalla y actualización inmediata del estado a `PAGADO`.
   * Botón para **"Agendar Fecha de Cobro / Recojo"** o cambiar a modalidad contraentrega.
2. **Panel de Caja Administrativa ([`CajaDashboard.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/caja/CajaDashboard.jsx)):**
   * Botón para aperturar caja ingresando saldo base en Soles.
   * Indicadores en vivo: Saldo Inicial, Cobros en Efectivo, Cobros Yape/Plin, Cobros Tarjeta POS y Saldo en Caja.
   * Registro y visualización de la tabla de movimientos del día.
3. **Módulo de Ventanilla y Recepción:**
   * Buscador rápido por tracking `CE-2026-NNNNN`.
   * Formulario de pesaje oficial y selector de cobro (Efectivo / Yape con N° operación / POS).

---

## 5. Criterios de Aceptación y Certificación E2E

1. **CA-01 (Control de Caja):** Un cajero sin sesión de caja abierta no puede registrar cobros en ventanilla (`400 BAD REQUEST: Caja no aperturada`).
2. **CA-02 (Notificación de Pre-registro):** Al registrar una encomienda con correo electrónico, el backend envía la constancia por Mailtrap en menos de 2 segundos.
3. **CA-03 (Firma Criptográfica Webhook):** Notificaciones al webhook con firma HMAC errónea se rechazan con `401 UNAUTHORIZED`.
4. **CA-04 (Notificación de Pago y Comprobante):** Al completarse el cobro (en ventanilla o por webhook), el sistema emite el correo con la Boleta/Factura electrónica y actualiza el hito en la línea de tiempo de tracking.
5. **CA-05 (Contraentrega):** Envíos con `lugar_pago = 'destino'` no permiten entrega física hasta registrar el cobro en la agencia receptora.
