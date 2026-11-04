# ⚖️ Guía Técnica de Exposición 12: Políticas de Cancelación, Reintegros de Balanza y Capacidad de Bodega

Esta guía documenta los protocolos operativos, comerciales y financieros de **CargaExpress Perú S.A.C.** ante solicitudes de cancelación, discrepancias en balanza, control de capacidad en almacenes y retenciones administrativas.

---

## 1. Cancelación de Encomiendas: ¿Quién puede cancelar y cómo?

### A. Cancelación por Autoservicio Web (Cliente Remitente)
* **Condición Estricta:** Solo disponible si el envío está en estado **`REGISTRADO`** y su pago está **`PENDIENTE`**.
* **Mecanismo:** Desde el portal público de [Tracking](http://localhost:5173/tracking), el remitente ingresa su número de DNI/RUC para autenticar titularidad y confirma la anulación voluntaria.
* **Por qué figura `Estado: CANCELADO` con `Pago: PENDIENTE`:**
  Cuando un cliente genera una pre-orden en el portal web (`/registrar-pedido`), el sistema reserva la cotización con pago `PENDIENTE`. Si el usuario decide no llevar el paquete a la agencia o cancela antes de pagar, el registro pasa a `CANCELADO` mientras la columna contable de pago permanece en `PENDIENTE` (lo cual es contablemente exacto, pues nunca ingresó dinero al arqueo de caja).
* **Costo:** **$S/\ 0.00$ (0% penalidad)**. No se devengan gastos administrativos ni fletes.
* **Caducidad Automática:** Los pre-registros no pagados expiran y se anulan automáticamente tras **48 horas hábiles**.

### B. Cancelación Administrativa vs Anulación Operativa
* **Diferenciación Semántica:**
  - **`CANCELADO`:** Desistimiento voluntario iniciado por el cliente desde el portal público o solicitud previa al pago.
  - **`ANULADO`:** Intervención administrativa de ventanilla (cajero o supervisor) cuando una orden ya formalizada o con comprobante emitido requiere baja tributaria mediante Nota de Crédito SUNAT o rescisión operativa por caducidad en bodega.
* **Unificación en Capa Backend y Filtros de Interfaz:**
  Ambos conceptos representan carga que **no se transportará ni devengará flete**. Por ello, el backend de CargaExpress unifica ambos términos de forma transparente en todas las consultas:
  ```python
  # app/api/v1/endpoints/envios.py
  if estado_norm in ["cancelado", "anulado"]:
      query = query.filter(func.lower(Envio.estado).in_(["cancelado", "anulado"]))
  ```
  Esto garantiza que el módulo administrativo (`/admin/envios?estado=cancelado`) y el Dashboard consoliden todas las desestimaciones sin generar discrepancias operativas.

---

## 2. Retenciones Operativas, Falso Flete y Devoluciones

| Escenario Operativo | Estado | Retención Aplicable | Justificación Técnica / Legal |
| :--- | :--- | :--- | :--- |
| **Pre-registro Web Impago** | `registrado` | **$S/\ 0.00$** | No hubo movilización física ni emisión de comprobante tributario. |
| **Envío Pagado en Línea (Cancelado en Agencia)** | `registrado` / `recepcionado` | **Hasta 10%** | Cubre gastos administrativos, comisiones de pasarela de pago y emisión/anulación SUNAT. |
| **Recojo a Domicilio Frustrado (Courier acudió)** | `registrado` | **$S/\ 15.00$ (Recargo de Recojo)** | Concepto de **Falso Flete**: compensa combustible, tiempo y desplazamiento del motorizado. |
| **Carga en Carretera / En Tránsito** | `en_ruta` | **No cancelable** | La carga está físicamente en bodega de camión interprovincial sellado. |

---

## 3. Principio de "No Custodia sin Flete Liquidado" y Protección de Capacidad

Para evitar la saturación (*capacity limit*) de las sedes operativas:

1. **Cero Guardería de Carga Impaga en Mostrador:**
   Si al medir en balanza surge una diferencia (sobrepeso/volumen) y el cliente no cuenta con el dinero para el reintegro, **el cajero no formaliza la Guía de Remisión y el cliente se lleva su bulto**. La empresa no actúa como almacén de bultos irregulares.
2. **Cero Carga en Recojo a Domicilio:**
   El courier verifica con wincha/balanza en la puerta del domicilio; si el flete no se abona o cancela en el acto, **el paquete se queda en el domicilio del cliente**, impidiendo el ingreso de bultos impagos a la agencia.

---

## 4. Custodia en Destino y Tasa Diaria de Almacenaje (Bodegaje)

Para las encomiendas que arribaron a la agencia destino (`EN_AGENCIA_DESTINO`):

* **Días 1 al 7 calendario:** Almacenaje y custodia **100% gratuitos** en estanterías.
* **Días 8 al 30 calendario:** Se devenga una penalidad de **$S/\ 3.00$ a $S/\ 5.00$ por día** para desincentivar el uso de la agencia como bodega comercial.
* **Mayor a 30 días:** Se inicia el proceso de **Rezago / Abandono Legal** conforme a la normativa del MTC y el Código de Comercio.

---

## 5. Prevención de Lavado de Activos (PLAFT / SBS N° 789-2018)

* **Tope de Efectivo:** Prohibido entregar más de $S/\ 20.00$ en efectivo físico por sobrepagos realizados en Yape, Plin o transferencias bancarias.
* **Canal Único:** Toda devolución mayor se extorna exclusivamente por la **misma vía digital y hacia la misma cuenta titular** de origen.

