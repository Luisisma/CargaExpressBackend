# Sprint 13: Aplicación Web Móvil (PWA) para Transportistas, Escaneo In Situ y Validación de Pre-Registros en Campo

> **Módulos:**
> 1. Aplicación Web Progresiva (PWA Móvil) para Transportistas y Choferes de Troncal (`/app/transportista`)
> 2. Escáner Óptico de Códigos de Barras / QR con la Cámara del Celular (HTML5 Camera API / QuaggaJS)
> 3. Recepción Instantánea de Paquetes en Camión y Transición a `EN_TRANSITO`
> 4. Módulo de Recojo en Puerta: Validación y Activación de Pre-Registros en Campo
> 5. Captura Automática de Coordenadas GPS del Conductor  
> **Frontend:** [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) (`src/pages/transportista/AppTransportista.jsx`, `src/components/scanner/CameraQrScanner.jsx`)  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (`app/api/v1/endpoints/transportistas.py`, `app/services/transportista_service.py`)  
> **Persistencia:** Tablas `manifiestos_embarque`, `eventos_tracking_gps`, `usuarios`, `envios`  
> **Estado:** 📋 **PLANIFICADO / EN DISEÑO DE ARQUITECTURA**

---

## 1. Justificación y Objetivos de Negocio

En el modelo actual, la confirmación de embarque de paquetes a los camiones se realiza desde la computadora de escritorio del jefe de almacén antes de la partida. Esto provoca vacíos de visibilidad operativa:
1. **Falta de confirmación instantánea:** El conductor no cuenta con una herramienta en su smartphone para confirmar que un paquete específico efectivamente subió a su unidad. Si un paquete se extravía entre el muelle y el camión, no hay responsable trazable.
2. **Incapacidad de validar Pre-Registros en Campo:** Cuando un cliente solicita un recojo en su fábrica o domicilio mediante pre-registro web, el chofer o courier no puede convertir ese pre-registro en una orden formal en el momento de la recepción física.
3. **Ausencia de Trazabilidad Geográfica:** El cliente no sabe en qué tramo de la carretera nacional o avenida se encuentra su encomienda.

### Metas del Sprint 13:
* **PWA Móvil Ultraligera:** Interfaz web táctil responsive que no requiere instalación desde Google Play / App Store; funciona desde el navegador Chrome/Safari del celular del transportista con modo pantalla completa y compatibilidad offline básica.
* **Escaneo con la Cámara:** El chofer activa la cámara de su celular y apunta al código de barras o QR de la guía; el sistema emite un pitido sonoro de éxito y marca el paquete como `CARGADO_EN_UNIDAD`.
* **Activación de Pre-Registros en Puerta:** El chofer escanea el código del pre-registro del cliente, verifica o ajusta las medidas/peso aproximado, confirma la recepción y el sistema emite el código de tracking definitivo en tiempo real notificando al cliente por email.
* **Eventos con Geoposicionamiento:** Cada escaneo registra latitud y longitud GPS del dispositivo móvil, alimentando la línea de tiempo del tracking público.

---

## 2. Diagrama de Flujo: Escaneo Móvil y Activación de Pre-Registros

```mermaid
flowchart TD
    Start([Chofer inicia ruta en su celular]) --> Login[Autenticación con PIN o Biometría]
    Login --> SelVehiculo[Selecciona Placa de Camión / Ruta]
    
    subgraph Escenario A: Carga en Almacén
        SelVehiculo --> ModoCarga[Modo: Embarque a Camión]
        ModoCarga --> ScanCamara[Apunta cámara al QR del Paquete]
        ScanCamara --> ValidaGuia{¿Paquete asignado a esta ruta?}
        ValidaGuia -- Sí --> BeepOK[Pitido Verde: Paquete Cargado]
        BeepOK --> UpdateTransito[Estado: EN_TRANSITO con GPS]
        ValidaGuia -- No --> BeepError[Alerta Roja: Paquete Erróneo / Otra Ruta]
    end

    subgraph Escenario B: Recojo a Domicilio (Pre-Registro)
        SelVehiculo --> ModoRecojo[Modo: Recojo de Pre-Registro]
        ModoRecojo --> ScanPreReg[Escanea QR del Pre-Registro del Cliente]
        ScanPreReg --> ConfirmaFisico[Confirma bultos y condición física]
        ConfirmaFisico --> FotoEvidencia[Captura foto del paquete en puerta]
        FotoEvidencia --> ActivaEnvio[POST /api/v1/transportista/activar-preregistro]
        ActivaEnvio --> PrintTicket[Envía Guía oficial PDF por Email al Cliente]
    end
```

---

## 3. Especificación Técnica de Endpoints

### 3.1. `POST /api/v1/transportista/embarcar-paquete`
* **Rol requerido:** `TRANSPORTISTA`, `CHOFER`, `COURIER`.
* **Payload:**
```json
{
  "tracking_o_qr": "TRK-2026-987654",
  "vehiculo_placa": "ABC-123",
  "latitud": -12.046374,
  "longitud": -77.042793,
  "precision_gps_metros": 8.5
}
```
* **Acción:**
  * Valida que el paquete pertenezca a la agencia de origen y no haya sido embarcado en otra unidad.
  * Cambia el estado del envío a `en_transito`.
  * Inserta un hito en `eventos_tracking_gps` con fecha, hora, placa y coordenadas geográficas.

### 3.2. `POST /api/v1/transportista/activar-preregistro`
* **Rol requerido:** `TRANSPORTISTA`, `CHOFER`, `COURIER`.
* **Payload:**
```json
{
  "codigo_preregistro": "PR-2026-00451",
  "peso_verificado_kg": 14.50,
  "bultos_recibidos": 2,
  "foto_evidencia_base64": "data:image/jpeg;base64,...",
  "observaciones_estado": "Cajas selladas correctamente con precinto de seguridad",
  "latitud": -12.085123,
  "longitud": -77.034561
}
```
* **Acción:**
  * Transforma el `pre_registro` en un `Envio` formal en la base de datos con número de tracking único `TRK-...`.
  * Registra el cobro si el cliente pagó online o asigna `modalidad_pago = 'contraentrega'` si pagará en destino.
  * Dispara correo transaccional automático al cliente confirmando: *"Su encomienda fue recolectada exitosamente por el chofer asignado"*.

---

## 4. Reglas de Negocio (Business Rules)

* **`BR-TRN-01` (Control de Capacidad en Cabina):** El sistema móvil muestra una barra de progreso del volumen del camión ($m^3$ y Toneladas). Si el chofer intenta escanear un paquete que supera la carga útil máxima de su placa, la aplicación emite una advertencia de sobrepeso legal (MTC).
* **`BR-TRN-02` (Geolocalización Obligatoria):** La PWA exige permiso de ubicación al iniciar sesión. Cada confirmación de carga o recojo debe incluir coordenadas GPS con un error de precisión menor a 50 metros.
* **`BR-TRN-03` (Modo Sin Cobertura / Offline Queue):** En carreteras interprovinciales sin señal celular 4G/5G (ej: zonas de puna o selva), la PWA almacena los escaneos en `IndexedDB` local del teléfono y los sincroniza automáticamente con el backend tan pronto recupera conectividad.

