# Sprint 08: Courier Última Milla, Arqueo Ciego de Caja y Gestión de Sobrepagos

> **Módulos:**
> 1. Hoja de Reparto y Última Milla para Courier (`/api/v1/admin/courier/rutas`, `/api/v1/admin/courier/{id}/entregar`)
> 2. Turnos de Caja Chica y Arqueo Ciego (`/api/v1/caja/aperturar`, `/api/v1/caja/arqueo-ciego`, `/api/v1/caja/cerrar`)
> 3. Protocolo y Endpoint de Gestión de Sobrepagos Yape / Efectivo (`/api/v1/caja/gestionar-sobrepago`)  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (`src/pages/admin/courier/CourierRutas.jsx`, `src/pages/admin/caja/CajaArqueo.jsx`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + SQLAlchemy 2.0 ORM + Pydantic v2)  
> **Persistencia:** Tablas `aperturas_caja`, `movimientos_caja`, `envios`, `historial_envios`  
> **Estado del Sprint:** 🚀 **FASE 1 (COURIER Y ÚLTIMA MILLA) 100% CULMINADA Y CERTIFICADA E2E**

---

## 1. Justificación y Objetivos de Negocio

El **Sprint 08** tiene como meta cerrar la totalidad de los flujos operativos que involucran contacto directo con el cliente final y manejo de dinero físico/digital:

1. **Reparto Urbano de Última Milla (Rol COURIER) [✅ CULMINADO]:**
   * Vista interactiva de entregas asignadas en `CourierRepartos.jsx` con filtros por estado y llamadas directas por teléfono.
   * Transición controlada a `en_reparto` con asignación de `courier_id` mediante `POST /api/v1/envios/{id}/iniciar-reparto`.
   * Entrega domiciliaria mediante `POST /api/v1/envios/{id}/entregar-domicilio` con validación de DNI, cobro contraentrega si aplica, captura de firma táctil sobre Canvas HTML5 y fotografía de evidencia en puerta (Base64).
   * Servicio desacoplado y mantenible `CourierService` en `app/services/courier_service.py`.
2. **Control Financiero de Caja y Arqueo Ciego:**
   * Obligatoriedad de abrir turno con saldo inicial en sencillo (ej: $S/\ 100.00$) antes de realizar cobros en mostrador (`BR-CAJ-01`).
   * Al cerrar el turno, el cajero realiza un **arqueo ciego**: cuenta su dinero en mano e ingresa el monto sin saber el total calculado por el sistema; el backend calcula automáticamente sobrantes o faltantes (`BR-CAJ-03`).
3. **Manejo Estricto de Sobrepagos (Billeteras Digitales):**
   * Automatizar el registro de vueltos menores ($\le S/\ 20.00$) y el bloqueo de devoluciones en efectivo para importes mayores, forzando la restitución por el mismo canal digital para prevenir lavado de dinero.

---

## 2. Especificación Técnica de Endpoints

### 2.1. Courier y Reparto a Domicilio

#### `GET /api/v1/admin/courier/mis-entregas`
* **Roles:** `COURIER`, `ADMINISTRADOR`.
* **Descripción:** Lista los paquetes asignados a la agencia o ruta del mensajero que se encuentren en estado `en_agencia_destino` con modalidad a domicilio.
* **Respuesta:** Array con tracking, dirección de entrega, distrito, destinatario, teléfono y estado de pago (`pendiente` o `pagado`).

#### `POST /api/v1/envios/{identificador}/entregar-domicilio`
* **Roles:** `COURIER`, `TRANSPORTISTA`, `ADMINISTRADOR`, `SUPERVISOR`.
* **Payload:**
```json
{
  "dni_receptor": "45678912",
  "nombre_receptor": "María Elena Gómez",
  "firma_base64": "data:image/png;base64,iVBORw0KGgoAAAANSU...",
  "observaciones": "Entregado en puerta principal del domicilio.",
  "cobro_contraentrega_confirmado": true
}
```
* **Acciones ACID y Desacople de Almacenamiento:**
  1. Si `estado_pago == 'pendiente'`, valida que el courier confirme la recepción del flete (Efectivo o Yape en puerta) y actualiza `estado_pago = 'pagado'`.
  2. Valida identidad del receptor (DNI exactamente 8 dígitos numéricos, C.E. o Pasaporte).
  3. Desacopla la persistencia: `_guardar_evidencia_fisica()` decodifica las evidencias Base64 a archivos físicos en `uploads/evidencias/` y almacena únicamente la ruta URL (`VARCHAR 300`) en base de datos.
  4. Actualiza `estado = 'entregado'`, sella `fecha_entrega_real = NOW()` y registra auditoría.
  5. Inserta hito en `historial_envios`: *"Entrega domiciliaria completada a María Elena Gómez (DNI 45678912)"*.

---

### 2.2. Turnos de Caja y Arqueo Ciego

#### `POST /api/v1/caja/aperturar`
* **Payload:** `{"saldo_inicial": 100.00, "agencia_id": 1}`.
* **Regla:** Solo una apertura activa por usuario. Si ya tiene un turno abierto, retorna `HTTP 400 Bad Request`.

#### `POST /api/v1/caja/cerrar-arqueo-ciego`
* **Payload:**
```json
{
  "efectivo_declarado": 350.00,
  "yape_declarado": 180.50,
  "tarjeta_declarado": 50.00,
  "observaciones": "Turno tarde sin novedades."
}
```
* **Lógica del Backend:**
  * El sistema calcula el saldo teórico:
    $$\text{Total Teórico} = \text{Saldo Inicial} + \sum \text{Ingresos} - \sum \text{Egresos}$$
  * Calcula el descuadre:
    $$\text{Diferencia} = \text{Efectivo Declarado} - \text{Total Teórico}$$
  * Guarda el registro en `aperturas_caja` con `estado = 'cerrada'`, `diferencia_saldo = Diferencia`.
  * Si la diferencia es negativa, alerta por faltante de caja; si es positiva, sobrante.

---

### 2.3. Endpoint de Gestión de Sobrepagos

#### `POST /api/v1/caja/gestionar-sobrepago`
* **Payload:**
```json
{
  "codigo_tracking": "CE-2026-K9M4P2X",
  "numero_operacion_billetera": "489201",
  "monto_real_flete": 18.00,
  "monto_transferido_cliente": 50.00,
  "tipo_resolucion": "re_yapeo_digital" // "vuelto_efectivo" | "re_yapeo_digital" | "saldo_a_favor"
}
```
* **Reglas:**
  * Si `monto_transferido - monto_real > 20.00` y `tipo_resolucion == "vuelto_efectivo"`, el backend **rechaza con error 422** por política anti-lavado.
  * Si `tipo_resolucion == "vuelto_efectivo"` ($\le 20.00$), inserta egreso en `movimientos_caja` (`tipo = 'devolucion_sobrepago'`).
  * Si `tipo_resolucion == "saldo_a_favor"`, acredita la diferencia en `clientes.saldo_credito`.

---

## 3. Criterios de Aceptación
- [ ] El courier puede marcar entregas desde el móvil en $< 3\text{ segundos}$.
- [ ] Arqueo ciego impide fraudes de manipulación de caja.
- [ ] El protocolo de sobrepagos bloquea retiros en efectivo mayores a S/ 20.00.
