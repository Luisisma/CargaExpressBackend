# 🔍 Guía Técnica de Exposición 06: Tracking Público, Línea de Tiempo e Integración RENIEC / SUNAT

Esta guía explica a fondo la arquitectura, seguridad y funcionamiento del módulo de **Tracking Público de Envíos y Consulta de Identidad Fiscal** en **CargaExpress Perú**.

---

## 1. Visión General del Módulo

El portal de Tracking es el servicio público de cara al cliente que permite:
1. **Rastreo Abierto en Tiempo Real:** Cualquier usuario con su código de guía o tracking (`CE-YYYY-NNNNN`) puede verificar el estado de su paquete sin necesidad de crear una cuenta o iniciar sesión.
2. **Protección de Datos Personales (PII / Ley 29733):** Enmascaramiento criptográfico de nombres, teléfonos y correos para evitar el raspado masivo de datos (*Data Scraping*).
3. **Validación Oficial de Identidad Fiscal:** Búsqueda híbrida que consulta primero la base local y, de no existir, interroga en tiempo real a los servicios de **RENIEC** (DNI) y **SUNAT** (RUC) para autocompletar nombres legítimos.

---

## 2. Diagrama de Conexión de Componentes

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Portal Público React)                           │
│                                                                                        │
│     [Vista Tracking: Tracking.jsx]             [Formulario: RegistrarPedido.jsx]        │
│                    │                                           │                       │
│                    ▼                                           ▼                       │
│             [publicService.getTracking]                [publicService.buscarCliente]   │
└────────────────────┬───────────────────────────────────────────┬───────────────────────┘
                     │ GET /api/v1/publico/tracking/{cod}        │ GET /buscar-cliente/{doc}
┌────────────────────▼───────────────────────────────────────────▼───────────────────────┐
│                              BACKEND (FastAPI Public Core)                             │
│                                                                                        │
│   [Router: publico.py] ────────► [Service: publico_service.py]                        │
│                                            │                                           │
│                 ┌──────────────────────────┴──────────────────────────┐                │
│                 ▼                                                     ▼                │
│        [Enmascaramiento PII]                              [consulta_documento_service] │
│      (C**** M****** / 98***34)                                        │                │
└─────────────────┬─────────────────────────────────────────────────────┼────────────────┘
                  │                                                     │
                  ▼                                                     ▼
     ┌─────────────────────────┐                           ┌─────────────────────────┐
     │  BASE DE DATOS LOCAL    │                           │ APIS EXTERNAS OFICIALES │
     │                         │                           │                         │
     │ - TABLA: envios         │                           │ 🏛️ RENIEC (DNI 8 dígitos)│
     │ - TABLA: historial_     │                           │ 🏢 SUNAT  (RUC 11 dígit)│
     │          envios         │                           │                         │
     └─────────────────────────┘                           └─────────────────────────┘
```

---

## 3. Flujo Paso a Paso de la Consulta de Tracking

1. **Ingreso del Código:** El cliente digita su código (ejemplo: `CE-2026-00001`) o hace clic en el enlace provisto por el sistema (`/tracking/CE-2026-00001`).
2. **Llamada API REST:** [Tracking.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/Tracking.jsx) ejecuta `GET /api/v1/publico/tracking/CE-2026-00001`.
3. **Búsqueda Indexada en DB:** El backend ejecuta una consulta optimizada sobre la columna indexada `envios.codigo_tracking`.
4. **Construcción de Línea de Tiempo Inmutable:**
   * Recupera la relación 1 a N de `historial_envios` ordenada cronológicamente por `creado_en`.
   * Extrae cada hito: `REGISTRADO`, `RECEPCIONADO`, `EN_RUTA`, `EN_AGENCIA_DESTINO` y `ENTREGADO`.
5. **Enmascaramiento Obligatorio de Privacidad (Compliance Legal):**
   * El servicio aplica funciones de anonimización sobre los nombres:
     * `"Carlos Alberto Mendoza"` $\rightarrow$ `"C***** A****** M******"`.
   * Si la consulta la realiza un tercero que encontró una boleta botada, **no puede extraer el nombre completo, teléfono ni dirección exacta del remitente o destinatario**.
6. **Respuesta y Renderizado Visual:**
   * El cliente visualiza un *Stepper* visual con íconos de estado, fecha/hora exacta de cada escala y estado del pago (`pendiente` o `pagado`).

---

## 4. Consulta Híbrida de Clientes (RENIEC / SUNAT)

Al registrar encomiendas o emitir comprobantes en mostrador, el sistema implementa una **búsqueda en dos niveles** para máxima velocidad y fiabilidad:

```text
               ¿Existe el documento en la tabla local 'clientes'?
                                  /            \
                             SÍ  /              \ NO
                                ▼                ▼
                  Retorna cliente local     Consulta API RENIEC / SUNAT
                  (Caché de alta velocidad)   (Verifica portador oficial)
                                                 │
                                                 ▼
                                            Guarda en memoria y 
                                            autocompleta formulario
```

### A. Consulta RENIEC (Documento Nacional de Identidad - DNI de 8 dígitos)
* **Validación:** Comprueba longitud exacta de 8 dígitos numéricos con expresión regular `^\d{8}$`.
* **Respuesta:** Extrae `nombres`, `apellido_paterno` y `apellido_materno`, unificándolos en `nombre_completo`.

### B. Consulta SUNAT (Registro Único de Contribuyentes - RUC de 11 dígitos)
* **Validación:** Comprueba longitud de 11 dígitos que inicien con prefijos oficiales `10`, `15` (personas naturales con negocio) o `20` (empresas / personas jurídicas).
* **Respuesta:** Extrae la `razon_social`, `direccion_fiscal`, `estado` (HABIDO / ACTIVO) y clasifica automáticamente como persona jurídica para emisión de **Factura**.

---

## 5. Persistencia en Base de Datos y Datos Esenciales

### A. Tabla `envios` (Lectura Pública)
* Se leen únicamente campos no confidenciales: `codigo_tracking`, `estado`, `tipo_envio`, `tipo_paquete`, `estado_pago`, `precio_envio`, `fecha_estimada`, `creado_en`.

### B. Tabla `historial_envios` (Fuente de la Línea de Tiempo)

| Campo | Ejemplo de Dato Retornado al Cliente |
|:---|:---|
| `estado` | `"EN_AGENCIA_DESTINO"` |
| `descripcion` | `"Arribó a la ciudad destino y está bajo custodia de la agencia destino."` |
| `ubicacion` | `"Agencia (Destino) ID: 10 - Cusco"` |
| `creado_en` | `"2026-10-13T20:50:00Z"` |

---

### C. Payloads de Red (API REST)

#### Response de Tracking Público con Enmascaramiento:
```json
{
  "success": true,
  "data": {
    "codigo_tracking": "CE-2026-00001",
    "estado": "EN_TRANSITO",
    "tipo_envio": "agencia_agencia",
    "tipo_paquete": "caja",
    "remitente": "C***** M******",
    "destinatario": "J**** Q******",
    "origen": "Lima (AGENCIA LIMA - LIMA CENTRAL)",
    "destino": "Arequipa (AGENCIA AREQUIPA - AREQUIPA)",
    "estado_pago": "pagado",
    "precio_total": 20.5,
    "creado_en": "2026-10-07T05:10:02Z",
    "historial": [
      {
        "estado": "REGISTRADO",
        "descripcion": "Pre-registro de envío completado vía portal web.",
        "ubicacion": "AGENCIA LIMA CENTRAL",
        "fecha": "2026-10-07T05:10:02Z"
      },
      {
        "estado": "RECEPCIONADO",
        "descripcion": "Recepcionado en agencia origen. Peso verificado en balanza.",
        "ubicacion": "Agencia Origen ID: 1",
        "fecha": "2026-10-07T05:15:00Z"
      },
      {
        "estado": "EN_RUTA",
        "descripcion": "Despachado y en tránsito hacia la agencia destino.",
        "ubicacion": "Ruta Nacional",
        "fecha": "2026-10-07T06:00:00Z"
      }
    ]
  }
}
```

---

## 6. Módulos de Código Exactos para Mostrar en la Exposición

### Backend:
1. [app/api/v1/endpoints/publico.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py):
   * Línea 48: Endpoint `/tracking/{codigo}` (Acceso abierto sin token JWT).
   * Línea 64: Endpoint `/buscar-cliente/{documento}` (Consulta híbrida DNI/RUC).
2. [app/services/publico_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py):
   * Líneas 97-135: Método `tracking()` con mapeo de `historial_envios` y enmascaramiento de nombres.
   * Líneas 137-200: Método `buscar_cliente()` (Nivel 1 local, Nivel 2 externo).
3. [app/services/consulta_documento_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/consulta_documento_service.py):
   * Integración HTTP con APIs de RENIEC y SUNAT.

### Frontend:
1. [src/pages/public/Tracking.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/Tracking.jsx):
   * Líneas 33-50: Función `consultarTracking()` y gestión de estados.
   * Líneas 51-65: Modal de cancelación voluntaria del pedido por parte del remitente validando DNI.
   * Líneas 120-220: Renderizado del Stepper dinámico y detalle de escalas.

---

## 7. Preguntas Frecuentes del Jurado y Cómo Defenderlas

| Pregunta Típica | Respuesta Técnica y Normativa |
|:---|:---|
| **¿Por qué la consulta de tracking no requiere iniciar sesión con usuario y contraseña?** | *"Porque es un servicio de cara al cliente final (B2C/C2C). Para conciliar la facilidad de acceso con la seguridad, el endpoint aplica un estricto filtrado que enmascara los nombres y nunca expone montos de cuentas bancarias, direcciones privadas ni datos sensibles (cumpliendo OWASP API3:2023 y Ley 29733)."* |
| **¿Qué pasa si el servicio de RENIEC o SUNAT se cae o no tiene internet?** | *"El sistema cuenta con tolerancia a fallos: el Nivel 1 busca primero en la tabla local `clientes`. Si la API externa falla o no responde, el servicio captura la excepción de forma segura y devuelve `encontrado: false`, permitiendo al operador ingresar los nombres manualmente en la interfaz sin interrumpir la atención de ventanilla."* |
| **¿Puede el cliente cancelar su pedido desde la web una vez creado?** | *"Sí, siempre y cuando el paquete permanezca en estado `registrado` y no haya sido pagado ni despachado. El remitente debe digitar su número de documento en la vista de tracking para comprobar su titularidad y ejecutar la cancelación voluntaria."* |
