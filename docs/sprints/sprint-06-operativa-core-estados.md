# Sprint 06: Operativa Core - Flujo de Estados del Envío

## 1. Situación Actual y Logro
Hemos completado exitosamente la cadena operativa completa de la Intranet para mover encomiendas a lo largo de todo su ciclo de vida:
1. **Parte A (Recepción en Origen):** `POST /api/v1/envios/{codigo}/recepcionar` y vista `/admin/caja/recepcion` (Pesaje en balanza, recálculo tarifario y cobro). ✅
2. **Parte B (Tránsito y Bodega):** `POST /api/v1/envios/{codigo}/despachar` a `en_ruta` en `/admin/almacen/despacho` y `POST /api/v1/envios/{codigo}/arribar` a `en_agencia_destino` en `/admin/almacen/arribos`. ✅
3. **Parte C (Entrega Final al Destinatario):** `POST /api/v1/envios/{codigo}/entregar` y botón modal en `/admin/envios/{id}` exigiendo DNI y nombres de quien recoge físicamente (`BR-ENV-04`), concluyendo la orden en estado `entregado`. ✅

## 2. Roles que Intervinieron en el Ciclo de Vida:
1. **CAJERO (Agencia de Origen):**
   - Recibe físicamente el paquete de manos del remitente, verifica el pago (o cobra en mostrador) e imprime comprobante.
   - Pasa de `registrado` a `recepcionado`.
2. **ALMACENERO / CONDUCTOR (Tránsito):**
   - El almacenero agrupa los paquetes y los sube al camión (`en_ruta`).
   - Al llegar a la agencia destino se descarga y se marca `en_agencia_destino`.
3. **CAJERO (Agencia Destino) o REPARTIDOR (Última milla):**
   - El destinatario muestra su DNI en ventanilla, se valida que el flete esté pagado y se registra la entrega física (`entregado`).

---

## 3. Estado del Sprint 06: ✅ 100% IMPLEMENTADO Y CERTIFICADO E2E
