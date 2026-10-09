# Reglas de Negocio: Clientes, Identidad y Normativa Fiscal

> **Módulo:** Gestión de Clientes y Cumplimiento Tributario  
> **Prefijo de Reglas:** `BR-CLI` (Business Rules - Clientes)  
> **Servicio Responsable:** [`app/services/consulta_documento_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/consulta_documento_service.py) & [`app/services/publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py)  
> **Marco Legal:** Ley N° 29733 (Protección de Datos Personales), Reglamento de Comprobantes de Pago de SUNAT (Resolución de Superintendencia N° 007-99/SUNAT)  
> **Estado:** 👤 **REGLA DE NEGOCIO VIGENTE Y DE OBLIGATORIO CUMPLIMIENTO**

---

## 1. Justificación y Objetivos

El transporte de mercancías interprovincial está estrictamente regulado en el Perú por la **SUNAT** (Superintendencia Nacional de Aduanas y de Administración Tributaria), la **SUTRAN** y el **MTC**. 

Para evitar multas tributarias, incautación de carga en garitas de control o lavado de activos:
1. Ninguna encomienda puede ser admitida sin identificar fehacientemente al remitente y al destinatario.
2. Los comprobantes de pago deben corresponder con exactitud al tipo de persona (Natural o Jurídica).
3. Toda empresa que solicite Factura debe estar formalmente inscrita y habida ante el fisco.

---

## 2. Tipos de Documentos de Identidad Aceptados

| Tipo | Denominación Oficial | Formato / Longitud | Validación Oficial | Tipo de Comprobante Permitido |
| :--- | :--- | :--- | :--- | :--- |
| **`dni`** | Documento Nacional de Identidad | 8 dígitos numéricos | RENIEC API (Validación de nombres reales) | Boleta de Venta |
| **`ruc`** | Registro Único de Contribuyentes | 11 dígitos numéricos | SUNAT API (Estado ACTIVO y Condición HABIDO) | Factura Electrónica o Boleta |
| **`ce`** | Carnet de Extranjería | 9 a 12 caracteres | Migraciones Perú | Boleta de Venta |
| **`pas`** | Pasaporte | 6 a 12 caracteres | Pasaporte internacional | Boleta de Venta |

---

## 3. Catálogo Detallado de Reglas de Negocio (BR-CLI)

### `BR-CLI-01`: Requisitos para Emisión de Facturas (RUC Activo y Habido)
* **Descripción:** Para emitir una Factura Electrónica (`tipo_documento = 'factura'`), el cliente remitente debe contar obligatoriamente con un RUC de 11 dígitos.
* **Condición SUNAT:** El servicio valida en línea:
  1. `estado = 'ACTIVO'`
  2. `condicion = 'HABIDO'`
* **Excepción:** Si la empresa se encuentra en condición "NO HABIDO", "NO HALLADO" o con RUC dado de baja, el sistema rechaza la emisión de la factura y obliga a emitir Boleta a nombre de la persona natural que gestiona el envío.

### `BR-CLI-02`: Límite Legal para Boletas Anónimas (Umbral S/ 700.00 SUNAT)
* **Descripción:** Según la normativa tributaria peruana:
  * Si el importe total del envío es **menor a S/ 700.00**, se permite emitir boleta con DNI o datos simplificados.
  * Si el importe total del envío es **igual o superior a S/ 700.00**, es **obligatorio por ley** ingresar el DNI/CE, nombre y apellidos completos y dirección del cliente. El sistema no permite procesar el envío sin estos datos completos.

### `BR-CLI-03`: Creación y Sincronización Automática de Clientes (Upsert)
* **Descripción:** Cuando un cliente registra una orden en la web o en ventanilla:
  1. El sistema busca primero en la tabla `clientes` si existe un registro con el mismo `tipo_documento` y `numero_documento`.
  2. Si existe, actualiza los datos de contacto recientes (`telefono`, `email`).
  3. Si no existe, crea el registro automáticamente enlazándolo a la orden.
* **Unicidad:** La combinación `(tipo_documento, numero_documento)` es única en el sistema.

### `BR-CLI-04`: Independencia entre Remitente y Destinatario
* **Descripción:** Una misma persona puede ser remitente en un envío y destinataria en otro.
* **Restricción:** El `remitente_id` y el `destinatario_id` no pueden ser idénticos si la modalidad es `agencia_agencia` con el mismo local de origen y destino (evita encomiendas ficticias o circulares para lavado de activos).

### `BR-CLI-05`: Protección de Datos Personales y No Eliminación Física
* **Descripción:** Para garantizar la integridad de las guías de remisión y comprobantes contables (que deben auditarse por 5 años fiscales según SUNAT):
  * **Los clientes nunca se borran físicamente (`DELETE`)**.
  * Si un cliente solicita baja de cuenta o ejercicio de derechos ARCO (Ley 29733), se marca `activo = False`, manteniendo la integridad referencial de los envíos históricos que generó en el pasado.
