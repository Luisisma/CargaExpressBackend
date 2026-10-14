# 2.8.2. Pruebas Pendientes y Limitaciones de la Fase Actual de Desarrollo

Este documento detalla con transparencia técnica y rigor metodológico las pruebas de software que **aún no han sido ejecutadas o superadas** en la fase actual del proyecto, justificando las limitaciones de alcance y estableciendo la hoja de ruta para fases futuras de control de calidad (QA).

---

## 1. Resumen de Pruebas Pendientes por Categoría

| Categoría | Tipo de Prueba | Herramienta Prevista | Causa / Limitación Actual | Fase Planificada |
| :--- | :--- | :---: | :--- | :---: |
| **Rendimiento** | Estrés y Concurrencia Masiva | Locust / k6 / JMeter | El entorno actual es de desarrollo local mono-hilo; no se ha probado bajo cargas de > 500 req/seg. | Fase de Despliegue Cloud |
| **Facturación Fiscal**| Integración SUNAT (PSE/OSE) | Certificado Digital X.509 | Las boletas y facturas se registran en BD interna, pero no envían XML firmado ni reciben CDR oficial. | Sprint de Facturación Electrónica |
| **Finanzas Reales** | Pasarela de Pagos en Producción | SDK Niubiz / MercadoPago | Los cobros operan con simulación de Webhook criptográfico, pendiente integración con credenciales bancarias. | Fase de Homologación Bancaria |
| **Resiliencia** | Tolerancia a Fallos (Circuit Breaker) | Tenacity / Redis Cache | Caídas prolongadas de RENIEC o SUNAT no activan apertura de circuito con caché distribuida. | Fase de Microservicios |
| **Automatización**| Cobertura Unitaria (`pytest-cov`)| Pytest / GitHub Actions | Las pruebas fueron manuales y de integración E2E; pendiente suite unitaria con cobertura > 80%. | Integración CI/CD |
| **Usabilidad Móvil**| Responsive en Panel Admin (`/admin/*`)| BrowserStack / Chrome DevTools | El panel de operaciones fue diseñado para PC de escritorio; no supera pruebas de diseño móvil en < 768px. | Sprint de Accesibilidad Móvil |
| **Infraestructura** | Recuperación ante Desastres (DRP) | PostgreSQL Barman / AWS RDS | Pendiente validar restauración automática de backups y conmutación por error (Failover). | Fase de Producción VPS |

---

## 2. Detalle Exhaustivo de las Pruebas Pendientes

### 1. Pruebas de Carga, Rendimiento y Concurrencia Masiva (Stress Testing)
* **Objetivo de la prueba:** Determinar el punto de degradación (*breaking point*) del backend FastAPI ante picos masivos de usuarios concurrentes (ej. campañas navideñas o Cyber Days).
* **Escenario no probado:** Ejecución de 1,000 usuarios virtuales simultáneos solicitando cotizaciones de flete (`POST /api/v1/publico/cotizar`) y rastreo de encomiendas en tiempo real.
* **Limitación actual:** Las pruebas actuales validan el comportamiento funcional para peticiones individuales o secuenciales. No se ha medido el agotamiento del pool de conexiones a la base de datos (`pool_size`, `max_overflow`), ni la saturación de workers de Uvicorn en entornos multi-core.
* **Riesgo asociado:** Posible incremento en la latencia (tiempos de respuesta superiores a 2 segundos) ante concurrencia extrema sin un balanceador Nginx previo.

---

### 2. Pruebas de Integración con Facturación Electrónica SUNAT (PSE / OSE)
* **Objetivo de la prueba:** Emisión y validación tributaria de Comprobantes de Pago Electrónicos (CPE) bajo el estándar UBL 2.1 de SUNAT.
* **Escenario no probado:** Generación de archivos XML para Boletas, Facturas y Guías de Remisión Electrónicas (GRE), firmado con certificado digital criptográfico X.509, envío mediante servicios web SOAP a SUNAT y recepción de la Constancia de Recepción (CDR) aceptada.
* **Limitación actual:** El sistema genera comprobantes y números de serie válidos en la base de datos relacional conforme a la regla `BR-CLI-01`, pero se detiene antes de la firma digital por requerir un RUC emisor con certificado tributario comercial.
* **Riesgo asociado:** No se puede certificar la interoperabilidad tributaria en tiempo real hasta contratar un proveedor OSE o utilizar el ambiente de pruebas (BETA) de SUNAT.

---

### 3. Pruebas con Pasarelas de Pago en Producción (Niubiz / Izipay / MercadoPago)
* **Objetivo de la prueba:** Liquidación financiera real mediante tarjetas de crédito, débito y transferencias bancarias interbancarias.
* **Escenario no probado:** Reconciliación bancaria real, manejo de contracargos, 3D Secure 2.0 (OTP bancario) y expiración de tokens de pago en pasarelas reales.
* **Limitación actual:** El sistema cuenta con un endpoint de Webhook criptográfico simulado (`/api/v1/pagos/webhook-simulado`) que valida la firma de cabecera y actualiza el estado de la encomienda, pero las credenciales no corresponden a un contrato de adquirencia comercial.
* **Riesgo asociado:** Necesidad de homologar flujos ante eventuales rechazos de fondos insuficientes o caídas de pasarela.

---

### 4. Pruebas de Resiliencia ante Caídas de Entidades Externas (Circuit Breaker)
* **Objetivo de la prueba:** Garantizar que la plataforma continúe operando si los servicios públicos de RENIEC o SUNAT sufren caídas de red o aplican bloqueos por saturación (WAF/CAPTCHA).
* **Escenario no probado:** Simular una desconexión total o latencia de 10 segundos en los servidores de consulta de DNI/RUC durante la admisión de una encomienda en ventanilla.
* **Limitación actual:** Si la entidad pública no responde, el sistema captura la excepción y retorna `encontrado: false`, permitiendo el ingreso manual de nombres por parte del operador; sin embargo, no existe un mecanismo de reintento exponencial (*Exponential Backoff*) ni un Circuit Breaker con caché en memoria (Redis) que sirva datos de clientes recurrentes sin salir a internet.
* **Riesgo asociado:** Retraso en la atención de ventanilla si el operador depende exclusivamente del autocompletado automatizado.

---

### 5. Pruebas Unitarias Automatizadas con Cobertura Continua (`pytest-cov`)
* **Objetivo de la prueba:** Ejecución automatizada de cientos de pruebas unitarias aisladas en menos de 10 segundos antes de cada commit en Git.
* **Escenario no probado:** Ejecución de pruebas unitarias sobre cada función de servicio (`AuthService`, `EnvioService`, `MotorTarifario`) utilizando *mocks* para aislar la base de datos y certificar una cobertura de código (*code coverage*) superior al 80%.
* **Limitación actual:** La validación del sistema se ha ejecutado mediante pruebas de integración E2E (Front ➔ Back ➔ Base de datos), certificando el funcionamiento integral pero sin una suite formal de `pytest` integrada en GitHub Actions.
* **Riesgo asociado:** Riesgo de regresión en funciones auxiliares al refactorizar código sin una suite unitaria automatizada.

---

### 6. Pruebas de Usabilidad y Compatibilidad Móvil en el Panel Administrativo (`/admin/*`)
* **Objetivo de la prueba:** Adaptabilidad ergonómica de las interfaces de gestión en teléfonos inteligentes y tabletas táctiles.
* **Escenario no probado:** Operación de la admisión en balanza, auditoría de usuarios y tablas de despacho en pantallas con resolución menor a 768 píxeles (dispositivos móviles).
* **Limitación actual:** Por requerimiento de alcance del proyecto, el panel administrativo fue diseñado y optimizado prioritariamente para **estaciones de trabajo de PC de escritorio** (agencias y bodegas). Las tablas con múltiples columnas y botones de acción no cuentan con diseño colapsable (*accordion view*) en smartphones.
* **Riesgo asociado:** La experiencia de usuario del personal administrativo en celulares es incómoda por requerir scroll horizontal.

---

## 3. Plan de Mitigación y Hoja de Ruta para Próximas Fases

Para abordar las pruebas pendientes antes de un pase formal a producción:

1. **Sprint 07 (Calidad y Automatización):**
   - Construcción de la suite de pruebas unitarias con `pytest` y `httpx.AsyncClient`.
   - Meta de cobertura: > 75% en la capa de servicios.
2. **Sprint 08 (Homologación y Pasarelas):**
   - Integración con el sandbox de pruebas de Niubiz / MercadoPago.
   - Conexión con el servicio BETA de Facturación Electrónica de SUNAT.
3. **Sprint 09 (Pruebas de Carga y Despliegue):**
   - Ejecución de pruebas de estrés con `Locust` simulando 200 usuarios concurrentes en servidor VPS de staging con PostgreSQL 17.
