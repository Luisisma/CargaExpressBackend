# Política Corporativa y Lógica de Negocio: Cancelaciones, Devoluciones y Reembolsos

> **Organización:** CargaExpress Perú S.A.C.  
> **Área:** Operaciones Logísticas, Finanzas y Seguridad de Software  
> **Marco Regulatorio:** Ley N° 29571 (Código de Protección y Defensa del Consumidor - INDECOPI), Reglamento Nacional de Transporte Terrestre (MTC), Normativa de Comprobantes de Pago Electrónicos (SUNAT).  
> **Estado:** 🛡️ **VIGENTE Y DE CUMPLIMIENTO OBLIGATORIO**  

---

## 1. Justificación y Objetivos de Negocio

La presente política establece las directrices operativas, financieras y de software para gestionar solicitudes de **cancelación de envíos**, **devolución de mercancías** y **reembolso de fletes**. 

### Objetivos Principales:
1. **Prevenir Malas Gestiones y Fraude Interno:** Impedir que cajeros o usuarios anulen encomiendas cobradas para sustraer efectivo de caja (*jineteo* o apropiación ilícita).
2. **Garantizar la Integridad Contable (SUNAT):** Asegurar que toda anulación de un envío facturado cuente con su correspondiente **Nota de Crédito Electrónica** vinculada y trazada en el arqueo de caja.
3. **Respetar el Ciclo Logístico Operativo:** Definir qué acciones proceden según el estado real de la encomienda en el transporte físico (origen, ruta o destino).
4. **Cumplir con la Trazabilidad Inmutable:** Cada solicitud de cancelación debe quedar registrada en `historial_envios` y `auditoria_sistema` con el usuario responsable, motivo tipificado, estampa de tiempo e IP.

---

## 2. Matriz de Estados y Viabilidad de Cancelación

El sistema de software y las agencias físicas deben respetar de forma estricta la siguiente matriz de viabilidad:

| Estado de la Encomienda (`estado`) | Estado de Pago (`estado_pago`) | ¿Procede Cancelación? | ¿Procede Reembolso? | Acción Operativa y Fiscal | Nivel de Autorización Requerido |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`registrado` (Pre-registro Web)** | `pendiente` | **SÍ (Inmediata)** | **NO APLICA** (No se cobró) | El registro pasa a `anulado`. Se libera el cupo. Si no se entrega en 48 hrs hábiles, el sistema lo expira automáticamente. | Cliente (Portal Web) / Cajero |
| **`en_almacen_origen` / `recepcionado`** | `pagado` | **SÍ (Condicionada)** | **SÍ (100% o 90%)** | Devolución física del paquete al remitente en la agencia de origen. Emisión obligatoria de **Nota de Crédito** y egreso de caja formal. | Cajero (hasta S/ 50) / Administrador de Agencia (> S/ 50) |
| **`en_transito` (En camión / ruta)** | `pagado` | **NO** | **NO** | El camión está precintado e intercomunicado en carretera nacional (MTC). Solo se permite **Solicitud de Retención en Destino** o **Retorno a Origen**. | Solo Administrador Nacional de Operaciones |
| **`en_agencia_destino` / `listo_para_recojo`** | `pagado` | **NO (Flete consumido)** | **NO** | El servicio de transporte se cumplió íntegramente. Si el destinatario no retira o rechaza, procede el protocolo de **Retorno a Origen**. | Administrador de Agencia Destino |
| **`entregado`** | `pagado` | **NO** | **NO** | Servicio concluido a satisfacción. | No procede |
| **`siniestrado` / `extraviado`** (Falla de la empresa) | `pagado` | **SÍ (Proceso Extraordinario)** | **SÍ (100% flete + indemnización)** | Apertura de expediente de siniestro. Reembolso total del flete pagado más indemnización según declaración jurada o póliza de seguro. | Gerencia de Operaciones y Auditoría |

---

## 3. Reglas Específicas por Escenario

```text
                                  ┌────────────────────────┐
                                  │   SOLICITUD CLIENTE    │
                                  └────────────────────────┘
                                               │
                                  ¿Ya entregó paquete en   │
                                  ventanilla y pagó?       │
                                  ┌────────────┴───────────┐
                               NO │                        │ SÍ
                                  ▼                        ▼
                       ┌──────────────────────┐   ┌──────────────────────┐
                       │ Cancelación Web /    │   │ ¿El paquete salió    │
                       │ Sin movimiento caja  │   │ de la agencia?       │
                       │ (estado: 'anulado')  │   └──────────┬───────────┘
                       └──────────────────────┘           NO │           │ SÍ
                                                             ▼           ▼
                                                  ┌─────────────────┐  ┌──────────────────┐
                                                  │ Reembolso Caja  │  │ NO PROCEDE       │
                                                  │ + Nota Crédito  │  │ Solo retención o │
                                                  │ SUNAT + Entrega │  │ retorno pagado   │
                                                  └─────────────────┘  └──────────────────┘
```

### 3.1. Escenario A: Cancelación de Pre-registro Web (Usuario Invitado / Portal)
* **Condición:** El envío fue creado vía web (`registrado_web = true`) con estado `registrado` y `estado_pago = 'pendiente'`.
* **Plazo de vigencia:** El cliente tiene **48 horas hábiles** para presentarse a la ventanilla de la agencia origen.
* **Acción:**
  * Si el cliente decide no enviar, puede cancelarlo desde el enlace de su correo o el cajero puede desestimarlo.
  * Si transcurren las 48 horas sin entrega física, un job cron en backend actualiza automáticamente el estado a `expirado`.
  * **Cero impacto financiero:** No hay devolución de dinero ni comprobante SUNAT que anular.

### 3.2. Escenario B: Cancelación en Agencia Origen antes del Despacho
* **Condición:** La encomienda fue pesada, etiquetada y cobrada, pero el camión aún no ha sido cargado con el manifiesto (`estado == 'en_almacen_origen'` o `'recepcionado'`).
* **Requisitos para el Cliente:**
  1. Presentar documento de identidad original del **Remitente** (DNI, CE o RUC de la empresa).
  2. Presentar el comprobante original de pago (Boleta o Factura física o electrónica).
* **Monto a Reembolsar:**
  * **Cancelación dentro de los primeros 60 minutos:** Reembolso del **100%** del monto total.
  * **Cancelación posterior a 60 minutos (paquete ya embalado/ubicado en palet):** Reembolso del **90%** (se deduce un 10% por gastos operativos y administrativos de etiquetado y manipulación, con tope máximo de S/ 20.00).
* **Protocolo de Caja y SUNAT:**
  * El cajero no puede simplemente entregar billetes. Debe emitir la **Nota de Crédito Electrónica** vinculada a la boleta/factura original con el código de motivo SUNAT **01 (Anulación de la operación)**.
  * Se registra un movimiento de egreso en la sesión de caja activa (`apertura_caja_id`) con el tipo `devolucion_envio`.

### 3.3. Escenario C: Encomienda en Tránsito (Carga Despachada)
* **Regla Inflexible:** Una vez asignado el envío a un manifiesto de carga (`manifiestos`) y encontrándose el camión en ruta, **bajo ninguna circunstancia se detiene el convoy para buscar una encomienda individual**.
* **Opciones del Remitente:**
  1. **Orden de Retención en Destino:** El remitente solicita formalmente que al arribar la carga a la agencia destino, no sea entregada al destinatario ni derivada a reparto a domicilio, sino puesta bajo custodia para retorno.
  2. **Retorno a Origen (Flete Inverso):** El cliente debe abonar la tarifa correspondiente al flete de regreso hacia la agencia de origen. No existe reembolso del flete de ida ya ejecutado.

### 3.4. Escenario D: Mercancía No Retirada o Rechazada en Destino
* **Plazo de Custodia Gratuita:** El destinatario dispone de **15 días calendario** para retirar la encomienda sin costo adicional.
* **Costo por Almacenaje:** Del día 16 al día 30 se aplica una tasa de almacenaje de $S/\ 2.00$ diarios para paquetes estándar y $S/\ 5.00$ para carga voluminosa.
* **Declaración de Abandono Legal:** Cumplidos los **30 días calendario** sin reclamo y tras dos notificaciones por correo/teléfono al remitente y destinatario, la mercancía se declara en abandono legal conforme a la normativa del MTC e INDECOPI.

---

## 4. Mitigación de Riesgos de Fraude y Malas Gestiones

Para blindar el negocio ante conductas deshonestas o errores humanos, la plataforma impone los siguientes controles técnicos:

### 4.1. Catálogo Cerrado de Motivos de Cancelación
Queda prohibido ingresar descripciones libres sin tipificación. Toda anulación debe clasificarse en:
1. `SOLICITUD_REMITENTE_VOLUNTARIA`: Remitente desiste antes del embarque.
2. `ERROR_DIGITACION_CAJERO`: Error en dimensiones, peso o destino detectado en los primeros 10 minutos (requiere emisión inmediata de nuevo ticket corregido).
3. `CONTENIDO_PROHIBIDO_DETECTADO`: Detección en inspección de sustancias o artículos no autorizados por ley (sustancias químicas, explosivos, perecibles no autorizados).
4. `DESTINATARIO_INUBICABLE_RECHAZO`: Destinatario rechaza recepción a domicilio.
5. `EXTRAVIO_O_DANO_OPERATIVO`: Siniestro declarado por la empresa.

### 4.2. Doble Aprobación (Dual Control)
* **Montos hasta S/ 50.00:** El cajero puede procesar la cancelación en su turno de caja activo, adjuntando obligatoriamente el motivo.
* **Montos superiores a S/ 50.00 o con más de 2 horas de antigüedad:** El sistema bloquea la acción hasta que un usuario con rol `ADMINISTRADOR` o `SUPERVISOR_AGENCIA` autorice la transacción en el módulo administrativo.
* **Cajas cerradas:** Si la caja del día ya fue arqueada y cerrada, ninguna anulación puede realizarse en esa fecha. El trámite pasa a **Tesorería Central** para reembolso por transferencia bancaria en un plazo de 24 a 48 horas.

### 4.3. Pistas de Auditoría Inmutables
Toda operación de cancelación o reembolso dispara automáticamente:
1. Actualización en tabla `envios`:
   * `estado = 'cancelado'` o `'anulado'`
   * `estado_pago = 'reembolsado'` o `'anulado'`
2. Inserción en `historial_envios`:
   * `estado = 'CANCELADO'`
   * `descripcion = 'Cancelación: [MOTIVO]. Autorizado por usuario [ID]. Monto reembolsado S/ [X]'`
   * `usuario_id = ID_DEL_AUTORIZADOR`
3. Inserción en `auditoria_sistema`:
   * Registro con `tabla = 'envios'`, `accion = 'CANCELACION_REEMBOLSO'`, IP del cliente, `datos_previos` y `datos_nuevos`.

---

## 5. Especificación Técnica de Endpoints REST (SDD)

Para dar soporte formal en el backend de FastAPI a estas políticas, se define la siguiente especificación:

### 5.1. Solicitud de Cancelación de Pre-registro (Público)
* **Ruta:** `POST /api/v1/publico/pedidos/{codigo}/cancelar`
* **Acceso:** Público (requiere validación con documento del remitente para anti-BOLA/IDOR).
* **Restricción:** Solo si `estado == 'registrado'` y `estado_pago == 'pendiente'`.

```json
// Request Body
{
  "numero_documento_remitente": "45678912",
  "motivo": "Cancelación solicitada por el cliente antes del pago"
}

// Response 200 OK
{
  "success": true,
  "data": {
    "codigo_tracking": "CE-2026-00003",
    "estado": "ANULADO",
    "mensaje": "El pre-registro de envío ha sido cancelado con éxito sin costo alguno."
  }
}
```

### 5.2. Cancelación y Reembolso Administrativo en Agencia
* **Ruta:** `POST /api/v1/envios/{id}/cancelar-reembolso`
* **Acceso:** Autenticado (Roles: `cajero`, `administrador`, `superadmin`).
* **Validación RBAC:** Si el flete supera S/ 50.00, rechaza con `403 FORBIDDEN` a menos que el token posea rol `administrador`.

```json
// Request Body
{
  "motivo_codigo": "SOLICITUD_REMITENTE_VOLUNTARIA",
  "observaciones": "Cliente decide transportar paquete por cuenta propia",
  "porcentaje_reembolso": 100.0,
  "metodo_reembolso": "efectivo_caja",
  "codigo_autorizacion": null
}

// Response 200 OK
{
  "success": true,
  "data": {
    "envio_id": 3,
    "codigo_tracking": "CE-2026-00003",
    "estado": "CANCELADO",
    "monto_reembolsado": 18.00,
    "nota_credito_requerida": true,
    "mensaje": "Envío cancelado. Proceda a devolver la carga física y emitir la Nota de Crédito en caja."
  }
}
```

---

## 6. Resumen de Cumplimiento para el Equipo de Desarrollo

1. **Nunca ejecutar `DELETE`:** Las encomiendas canceladas se preservan en la base de datos con fines tributarios y de auditoría.
2. **Cálculo de Descuentos o Penalidades en Servidor:** Cualquier retención por gastos operativos (ej: 10%) debe calcularse exclusivamente en `CargaExpressBackend`, nunca enviarse precalculada desde el cliente React.
3. **Bloqueo Concurrente:** La transacción de cancelación debe adquirir un bloqueo de fila (`SELECT ... FOR UPDATE`) sobre el registro del envío y la sesión de caja activa para evitar dobles reembolsos simultáneos.
