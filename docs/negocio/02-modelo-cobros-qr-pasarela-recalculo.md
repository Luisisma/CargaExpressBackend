# Política Oficial de Cobros, QR, Pasarela y Arquitectura de Webhooks

> **Organización:** CargaExpress Perú S.A.C.  
> **Marco Regulatorio:** Estándar PCI-DSS (Seguridad de Datos de Tarjetas), Normativa de Comprobantes de Pago Electrónicos (SUNAT), Ley N° 29733 (Protección de Datos Personales en Perú), Código de Protección al Consumidor (INDECOPI).  
> **Moneda Oficial del Sistema:** Soles Peruanos (`PEN` / `S/`).  
> **Estado:** 🛡️ **POLÍTICA OFICIAL ADOPTADA Y VIGENTE**

---

## 1. Decisión de Negocio Adoptada: Modelo Híbrido Basado en Pesaje Real

Tras evaluar la operativa del transporte interprovincial de encomiendas y la normativa fiscal peruana, **CargaExpress adopta formalmente el Modelo 1**:

### Política Oficial: "Pre-registro Gratuito + Cobro por QR/Efectivo al Pesar"

1. **Pre-registro Web Cero Fricción:** El usuario registra la encomienda en el portal web o app móvil sin necesidad de ingresar tarjetas de crédito ni pagar por anticipado. El sistema emite el **Código de Tracking Oficial `CE-2026-NNNNN`** con una tarifa referencial estimada.
2. **Estado Inicial:** El envío se almacena en base de datos con:
   * `estado = 'registrado'`
   * `estado_pago = 'pendiente'`
   * `lugar_pago = 'origen'` (o `'destino'` si es modalidad contraentrega)
3. **Inspección Física Vinculante (INACAL / MTC):**
   * **En Agencia:** El cajero recibe el paquete y lo pesa en la balanza digital certificada.
   * **En Domicilio:** El courier arriba con dinamómetro/balanza portátil y valida dimensiones.
4. **Liquidación Inmediata del Precio Real:** En ese segundo exacto, el backend calcula el precio definitivo en Soles (`PEN`) y el cliente abona el importe exacto.
5. **Cero Problemas de Reembolsos:** Al no cobrarse nada por adelantado, la empresa elimina el 100% de las disputas por diferencias de peso, sobreprecios o devoluciones antes del despacho.

---

## 2. Mecanismo Dual de Aprobación de Pagos

El backend de FastAPI y la base de datos relacional soportan dos canales de liquidación para el cobro:

```text
                                  ┌────────────────────────┐
                                  │   LIQUIDACIÓN DE PAGO  │
                                  └────────────────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
             [CANAL A: FÍSICO / CAJERO]                      [CANAL B: DIGITAL WEBHOOK]
             - Efectivo en Ventanilla                        - Yape / Plin QR en Pantalla
             - POS Izipay / Niubiz                           - Pasarela Sandbox / Tarjetas
             - Yape presencial a QR de Agencia                             │
                       │                                                   │
                       ▼                                                   ▼
            POST /caja/cobrar-presencial                     POST /pagos/webhook-simulado
            - Cajero valida dinero físico                    - Payload firmado HMAC/Secret
            - Ingreso en aperturas_caja                      - Procesa evento payment.succeeded
                       │                                                   │
                       └───────────────────────┬───────────────────────────┘
                                               ▼
                                  ┌────────────────────────┐
                                  │   ACTUALIZACIÓN BDD    │
                                  │ - estado_pago: pagado  │
                                  │ - estado: recepcionado │
                                  │ - Boleta/Factura SUNAT │
                                  │ - Hito en historial    │
                                  └────────────────────────┘
```

---

### 2.1. Canal A: Aprobación Presencial por Cajero (Ventanilla / Agencia)

Aplica cuando el cliente entrega el paquete en la agencia o cuando el courier cobra en puerta:

* **Medios Habilitados:**
  1. **Efectivo (Cash):** El cajero recibe los billetes/monedas en Soles, comprueba autenticidad y registra el ingreso en la sesión activa de caja (`aperturas_caja`).
  2. **Billetera Móvil (Yape / Plin):** El cliente escanea el QR físico impreso en la ventanilla. El cajero verifica en su terminal el abono y digita obligatoriamente el **Número de Operación** de 6 dígitos del voucher.
  3. **POS Tarjeta (Izipay / Niubiz):** El cajero procesa la tarjeta en el POS físico y digita el **Número de Referencia / Lote** del voucher impreso.

* **Contrato de Endpoint (Backend):**
  * `POST /api/v1/caja/cobrar-presencial` (Protegido: Roles `cajero`, `administrador`).

```json
// Request Body
{
  "envio_id": 3,
  "metodo_pago": "yape", // "efectivo" | "yape" | "plin" | "tarjeta_pos"
  "numero_operacion": "489201",
  "monto_cobrado": 18.00,
  "tipo_comprobante": "boleta" // "boleta" | "factura"
}

// Acciones ACID en BDD:
// 1. Validar que la caja del usuario esté 'abierta'.
// 2. Insertar en 'movimientos_caja' (tipo: 'ingreso', monto: 18.00).
// 3. Actualizar 'envios': estado = 'recepcionado', estado_pago = 'pagado'.
// 4. Insertar hito en 'historial_envios': 'PAGO_CONFIRMADO_VENTANILLA'.
```

---

### 2.2. Canal B: Pago Digital Simulado mediante Arquitectura Webhook

Para permitir que el usuario experimente el pago digital en la web o app (vía QR dinámico o pasarela simulada) sin incurrir en costos de pasarelas reales ni almacenar tarjetas:

* **Simulación de Pasarela (Sandbox Estilo Culqi / Niubiz):**
  * En el frontend se despliega una pantalla interactiva de pago:
    * Opción A: **Yape QR Dinámico** con temporizador de 5 minutos y monto exacto en Soles.
    * Opción B: **Tarjeta de Prueba (Sandbox)** con datos de prueba (ej: `4242 4242...`).
  * Al confirmar el pago en el cliente, este no modifica directamente la base de datos de envíos (para evitar manipulación de estado en cliente).
  * En su lugar, el simulador despacha una llamada segura al **Webhook de Pagos** del backend.

* **Arquitectura de Webhook Seguro (OWASP API Top 10):**
  * **Ruta:** `POST /api/v1/pagos/webhook-simulado`
  * **Seguridad:** Cabecera `X-Webhook-Signature` generada con HMAC-SHA256 y secreto compartido (`WEBHOOK_SECRET_KEY`) para garantizar que la notificación proviene del motor de pagos autorizado y no de un atacante.
  * **Idempotencia:** Cabecera `X-Idempotency-Key` o `transaction_id` único para evitar cobros dobles si la notificación se reintenta.

```json
// Headers
// X-Webhook-Signature: a58f79... (HMAC-SHA256)
// Content-Type: application/json

// Webhook Payload
{
  "event": "payment.succeeded",
  "transaction_id": "TXN-2026-981249",
  "codigo_tracking": "CE-2026-00003",
  "monto": 18.00,
  "moneda": "PEN",
  "metodo_pago": "yape_qr",
  "numero_operacion": "892104",
  "timestamp": "2026-10-08T16:40:00Z"
}
```

* **Procesamiento Server-Side:**
  1. Verificar la firma criptográfica del Webhook.
  2. Buscar el envío por `codigo_tracking`.
  3. Validar que el monto coincida con `precio_envio` (en Soles).
  4. Actualizar atómicamente:
     * `envios.forma_pago = 'yape'`
     * `envios.estado_pago = 'pagado'`
     * `envios.estado = 'recepcionado'` (o `'pagado_web'`)
  5. Registrar hito en `historial_envios`: `"Pago digital confirmado vía Yape QR (Op: 892104)"`.
  6. Responder `200 OK` con `{"received": true}`.

---

## 3. Seguridad de Datos Financieros (PCI-DSS & Ley N° 29733)

1. **Prohibición Absoluta de Almacenamiento Bancario:**
   * La base de datos relacional de CargaExpress **no contiene ni contendrá campos para:**
     * `numero_tarjeta` (PAN)
     * `cvv` / `cvc`
     * `fecha_expiracion`
     * `pin` o contraseñas bancarias
2. **Campos Autorizados en la Base de Datos:**
   * Solo se almacenan datos transaccionales de auditoría:
     * `forma_pago` (`efectivo`, `yape`, `plin`, `tarjeta`, `transferencia`)
     * `numero_documento_comprobante` (serie y correlativo boleta/factura)
     * `numero_operacion` (código de voucher o referencia bancaria)
     * `monto` en Soles (`NUMERIC(10,2)`)

---

## 4. Parámetros Legales y Normativos (SUNAT)

* **Moneda Única y Exclusiva:** Todas las cotizaciones, comprobantes y arqueos se expresan en **Soles Peruanos (`PEN` / `S/`)**.
* **Comprobantes Electrónicos:**
  * Remitente con **DNI (8 dígitos)**: Emisión obligatoria de **Boleta de Venta Electrónica**.
  * Remitente con **RUC (11 dígitos)**: Emisión obligatoria de **Factura Electrónica** con desglose de Base Imponible e IGV (18%).
  * El comprobante legal se emite únicamente tras la confirmación efectiva del pago.

---

## 5. Resumen de Estados de la Encomienda y del Pago

| Momento Operativo | `estado` (Envío) | `estado_pago` | Acción en Caja / Webhook |
| :--- | :--- | :--- | :--- |
| **Cliente pre-registra en casa** | `registrado` | `pendiente` | Ninguna. Cupo reservado. |
| **Pesaje y Cobro en Ventanilla** | `recepcionado` | `pagado` | Cajero registra ingreso en `movimientos_caja`. |
| **Pago Digital Simulado QR** | `recepcionado` | `pagado` | Webhook actualiza estado tras verificar firma. |
| **Cobro Contraentrega (Destino)** | `en_agencia_destino` ➔ `entregado` | `pendiente` ➔ `pagado` | Cajero destino cobra antes de entregar paquete. |
| **Cancelación sin Pago** | `anulado` | `anulado` | Pre-registro web cancelado sin costo. |

---

## 6. Regla `BR-COB-04`: Protocolo Oficial de Sobrepagos Digitales (Yape / Plin) y Prevención de Lavado de Activos (PLAFT / UIF)

### 6.1. Marco Regulatorio Peruano
Esta política se fundamenta estrictamente en la legislación financiera y tributaria de la República del Perú:
1. **Ley N° 27693 y Resolución SBS N° 789-2018 (Norma de Prevención del Lavado de Activos y Financiamiento del Terrorismo - PLAFT):**
   * Tipifica la **"Bancarización Inversa o Extracción Ilícita de Efectivo"**: modalidad de fraude donde un delincuente transfiere dinero de origen dudoso (phishing, cuentas vulneradas o tarjetas clonadas) a un comercio físico simulando una compra o servicio, para luego solicitar inmediatamente la devolución en **efectivo limpio de la caja registradora**, convirtiendo al negocio en víctima de fraude o sujeto obligado bajo investigación penal.
2. **Ley N° 28194 (Ley para la Lucha contra la Evasión y para la Formalización de la Economía - Ley de Bancarización):**
   * Establece el **Principio de Simetría en los Medios de Pago**: Toda restitución de fondos originada en una transferencia digital debe devolverse a través del mismo canal y hacia la misma cuenta de origen para no quebrar la trazabilidad bancaria del dinero.
3. **Reglamento de Comprobantes de Pago (Resolución de Superintendencia N° 007-99/SUNAT):**
   * Los comprobantes de pago (Boleta o Factura) deben emitirse **únicamente por el valor real del servicio prestado (flete de la encomienda)**. Un importe transferido en exceso por error del cliente **no constituye base imponible ni ingreso gravado con IGV**, sino un pasivo exigible temporal (abono en exceso a favor de terceros).
4. **Ley N° 29571 (Código de Protección y Defensa del Consumidor - INDECOPI):**
   * Ampara el derecho del usuario a la restitución expedita de cobros indebidos o en exceso, condicionada a la verificación de la identidad del titular pagador para salvaguardar su patrimonio frente a suplantaciones.

---

### 6.2. Matriz de Casuísticas Operativas y Protocolos de Resolución

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│             MATRIZ DE RESOLUCIÓN DE SOBREPAGOS DIGITALES (YAPE / PLIN)                 │
├────────────────────┬──────────────────┬────────────────────────────────────────────────┤
│ Rango del Exceso   │ Nivel de Riesgo  │ Protocolo Operativo y Fiscal Obligatorio       │
├────────────────────┼──────────────────┼────────────────────────────────────────────────┤
│ Hasta S/ 20.00     │ 🟢 Bajo (Sencillo│ Reembolso en efectivo inmediato como "Vuelto   │
│                    │   operativo)     │ menor de caja chica" con registro de voucher.  │
├────────────────────┼──────────────────┼────────────────────────────────────────────────┤
│ De S/ 20.01        │ 🟡 Medio (Riesgo │ PROHIBIDO DEVOLVER EFECTIVO EN VENTANILLA.     │
│ hasta S/ 500.00    │   descapitalizado│ Opciones: 1) Re-yapeo / Extorno digital hacia  │
│                    │   y liquidez)    │ el mismo titular. 2) Saldo a favor del cliente.│
├────────────────────┼──────────────────┼────────────────────────────────────────────────┤
│ Más de S/ 500.00   │ 🔴 Alto (Alerta  │ BLOQUEO INMEDIATO EN VENTANILLA (Alerta PLAFT).│
│ (Monto atípico)    │   PLAFT / Fraude)│ Expediente formal en Tesorería. Retención de   │
│                    │                  │ fondos y restitución bancaria (CCI) en 24-48h. │
└────────────────────┴──────────────────┴────────────────────────────────────────────────┘
```

#### 📌 Casuística 1: Diferencia Menor o Error de Sencillo ($\le S/\ 20.00$)
* **Escenario Típico:** El flete liquidado en balanza es $S/\ 15.00$ y el remitente transfiere $S/\ 20.00$ por redondeo rápido en su app móvil.
* **Resolución en Software:**
  * El cajero puede otorgar el vuelto de $S/\ 5.00$ en efectivo directamente desde la gaveta física.
  * El backend registra un egreso en `movimientos_caja` (`tipo = 'devolucion_sobrepago'`) vinculado al número de operación de Yape/Plin, garantizando que el arqueo de caja cuadre al milímetro.
* **Justificación de Riesgo:** Importes menores a $S/\ 20.00$ no descapitalizan la caja chica de la agencia ni configuran riesgo significativo de lavado de dinero.

#### 📌 Casuística 2: Sobrepago Mayor o Significativo ($> S/\ 20.00$ hasta $S/\ 500.00$)
* **Escenario Típico:** El flete es de $S/\ 30.00$ y el cliente transfiere $S/\ 150.00$ o $S/\ 300.00$ por error al digitar el número telefónico o monto.
* **Regla Inflexible:** **El cajero tiene terminantemente prohibido abrir el cajón y entregar efectivo físico.**
* **Motivación Operativa y Financiera:**
  1. **Descapitalización de Agencia:** Las agencias inician turno con un fondo fijo de sencillo (ej. $S/\ 150.00$). Entregar $S/\ 200.00$ en billetes dejaría al mostrador sin cambio para atender a los siguientes clientes.
  2. **Riesgo de Estafa:** Si el pago proviene de una cuenta suplantada, el titular real solicitará el descongelamiento al banco (chargeback o contracargo), y CargaExpress perdería el efectivo entregado.
* **Vías de Solución Habilitadas:**
  1. **Vía A - Re-Yapeo / Re-abono Digital Inverso:** El supervisor de la agencia o tesorería ejecuta una transferencia reversa por el saldo excedente **hacia el mismo número de teléfono y titular** de donde provino el pago, conservando ambos vouchers en auditoría.
  2. **Vía B - Saldo a Favor en Cuenta de Cliente (`saldo_credito`):** Si el cliente es remitente recurrente o corporativo, el saldo sobrante se abona como crédito a su favor en el padrón (`clientes.saldo_credito`) para descontarse automáticamente en sus próximos despachos.

#### 📌 Casuística 3: Sobrepago Anómalo o Sospechoso ($> S/\ 500.00$)
* **Escenario Típico:** El flete es $S/\ 25.00$ y el cliente transfiere $S/\ 1,500.00$ o $S/\ 3,000.00$, solicitando que la agencia "le devuelva el saldo en efectivo para hacer otras compras".
* **Protocolo de Seguridad (Alerta PLAFT / Oficial de Cumplimiento):**
  1. **Bloqueo Inmediato:** El sistema no autoriza ningún extorno directo en mostrador.
  2. **Identificación Fehaciente del Pagador:** Se solicita el DNI físico original del remitente y el estado de cuenta / voucher oficial emitido por la entidad bancaria remitente.
  3. **Apertura de Expediente de Devolución:** El caso se deriva a la Gerencia de Finanzas / Oficial de Cumplimiento.
  4. **Restitución Vía CCI:** La devolución se procesa dentro de las **24 a 48 horas hábiles** exclusivamente mediante transferencia interbancaria (CCI) a una cuenta bancaria a nombre del mismo titular del DNI verificado, emitiendo el acta de extorno bancario auditable ante la SBS/UIF.

#### 📌 Casuística 4: Comprobante Falso o Voucher Adulterado
* **Escenario Típico:** El usuario muestra una captura de pantalla en su teléfono celular simulando un Yape exitoso con tipografía o colores modificados.
* **Control Técnico de Sistema:**
  * **Regla de Oro en Ventanilla:** *"Ningún paquete se recepciona basándose en la pantalla del celular del cliente."*
  * El cajero verifica la acreditación en el **terminal corporativo receptor de la agencia** (SMS / Notificación Push / Estado de Cuenta de la empresa).
  * El cajero digita en el sistema el **Número de Operación oficial de 6 dígitos**.
  * Si la operación no figura acreditada en la cuenta de la empresa, el paquete se mantiene en estado `registrado` con `estado_pago = 'pendiente'`, impidiendo su ingreso al almacén.

