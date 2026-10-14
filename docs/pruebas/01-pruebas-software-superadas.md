# 2.8. Pruebas de Software Realizadas con Éxito

Este documento formaliza la batería completa de pruebas superadas exitosamente por el sistema **CargaExpress** durante su fase de desarrollo actual, categorizadas por tipos de pruebas (Funcionales, Integración, Seguridad DAST, Reglas de Negocio e Integridad de Persistencia).

---

## 2.8.1. Matriz General de Casos de Prueba Superados

| Código | Tipo de Prueba | Módulo / Componente | Resultado Esperado | Resultado Obtenido | Estado |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **`TC-AUTH-01`** | Seguridad / Funcional | Login y 2FA TOTP | Login seguro con Bcrypt y segundo factor de 6 dígitos. | Acceso concedido con JWT Bearer y generación de QR en pantalla. | ✅ **EXITOSO** |
| **`TC-AUTH-02`** | Integración / Funcional | Recuperación de Contraseña | Token temporal firmado (15 min) y despacho SMTP. | Envío de correo verificado en bandeja de entrada Mailtrap. | ✅ **EXITOSO** |
| **`TC-CLI-01`** | Integración Externa | Identidad RENIEC (DNI) | Obtener nombres reales de persona natural peruana. | DNI 8 dígitos retorna nombre oficial (ej. "Rouss Cuellar"). | ✅ **EXITOSO** |
| **`TC-CLI-02`** | Integración Externa | Identidad Fiscal SUNAT (RUC) | Validar RUC, Razón Social, estado y condición tributaria. | Parser HTML extrae razón social, estado ACTIVO y HABIDO. | ✅ **EXITOSO** |
| **`TC-TAR-01`** | Regla de Negocio | Motor Tarifario y Cubicaje | Aplicar $(L \times A \times H)/6000$ y peso liquidable (`BR-TAR-01`). | Flete base S/ 8.00 + S/ 2.50/kg adicional calculado con exactitud. | ✅ **EXITOSO** |
| **`TC-PED-01`** | Funcional E2E | Pre-registro Web de Envío | Generar orden preliminar con código de tracking y QR. | Orden creada en estado `registrado` con tracking `CE-2026-XXXXX`. | ✅ **EXITOSO** |
| **`TC-PAG-01`** | Integración / Finanzas | Simulación de Pago (Webhook) | Confirmar pago asíncrono y cambiar estado contable. | Webhook actualiza orden a `pagado` y registra comprobante. | ✅ **EXITOSO** |
| **`TC-CAJ-01`** | Operativa / Ventanilla | Recepción en Balanza Digital | Pesar paquete, recalcular flete y cobrar reintegro. | Paquete admitido, recalcula por sobrepeso (`BR-TAR-02`) y ticket. | ✅ **EXITOSO** |
| **`TC-ALM-01`** | Operativa / Bodega | Despacho a Ruta (Camión) | Bloquear si no está pagado (`BR-ENV-02`) y enviar a ruta. | Valida pago obligatorio y transiciona estado a `en_ruta`. | ✅ **EXITOSO** |
| **`TC-ALM-02`** | Operativa / Bodega | Arribo y Descarga en Destino | Descargar de camión y admitir en bodega de destino. | Valida procedencia (`BR-ENV-03`) y pasa a `en_agencia_destino`. | ✅ **EXITOSO** |
| **`TC-ENT-01`** | Operativa / Cierre | Entrega Física al Destinatario | Exigir DNI de quien recoge físicamente (`BR-ENV-04`). | Registra receptor, hito cronológico y finaliza en `entregado`. | ✅ **EXITOSO** |
| **`TC-RBAC-01`**| Seguridad / Autorización| Control RBAC Mínimo Privilegio| Bloquear endpoints no autorizados según rol del JWT. | Rechazo con `HTTP 403 Forbidden` a roles no autorizados. | ✅ **EXITOSO** |
| **`TC-SEC-01`** | Seguridad Dinámica | Auditoría DAST (OWASP ZAP) | Escaneo pasivo y activo sin fallos críticos. | 0 Alertas Altas, CSP Level 3 y SRI en Swagger UI. | ✅ **EXITOSO** |
| **`TC-PII-01`** | Seguridad / Privacidad | Enmascaramiento de Datos | Proteger DNI, nombres y teléfonos en rastreo público. | Datos sensibles ocultos bajo formato `***123` / `J*** P***`. | ✅ **EXITOSO** |
| **`TC-SES-01`** | Seguridad de Sesión | Invalidación Reactiva JWT | Cerrar sesión invalidando tokens anteriores en backend. | Incremento de `sesion_version` revoca de inmediato el JWT. | ✅ **EXITOSO** |

---

## 2.8.2. Detalle Exhaustivo de Pruebas Superadas por Dominio

### 1. Pruebas de Autenticación, MFA y Recuperación
* **`TC-AUTH-01`: Logueo del Administrador con MFA (TOTP):**
  - **Precondición:** Administrador registrado en base de datos con contraseña Bcrypt.
  - **Procedimiento:** El usuario ingresa credenciales en `/auth/login`. Si tiene MFA habilitado, el backend devuelve un token temporal de 5 minutos y no emite sesión completa. En `/auth/2fa`, el usuario ingresa el código de 6 dígitos de Google Authenticator.
  - **Resultado:** Token validado criptográficamente en backend con ventana de deriva de ±1 paso; se emite Access Token (30 min) y Refresh Token (7 días).
* **`TC-AUTH-02`: Recuperación de Contraseña con Despacho de Correo (Mailtrap):**
  - **Procedimiento:** Solicitud con DNI/Correo en `/auth/recuperar-password`. Backend genera token firmado HMAC-SHA256 de 15 minutos y despacha plantilla HTML por SMTP.
  - **Resultado:** El usuario hace clic en el enlace, define una nueva contraseña con política NIST (mínimo 8 caracteres, números y mayúsculas) y se incrementa `sesion_version`, cerrando sesiones abiertas en otros dispositivos.

### 2. Pruebas de Integración con Entidades Públicas (RENIEC y SUNAT)
* **`TC-CLI-01`: Validación de DNI ante RENIEC:**
  - **Procedimiento:** Ingreso de DNI de 8 dígitos en cotizador/registro de encomienda.
  - **Resultado:** El servicio consume la API de RENIEC y autocompleta con exactitud los nombres del ciudadano (ej. *"Rouss Cuellar"*), evitando digitación errónea del operador.
* **`TC-CLI-02`: Validación de Identidad Fiscal ante SUNAT (RUC 11 dígitos):**
  - **Procedimiento:** Ingreso de RUC `20100070970` para emisión de factura comercial.
  - **Resultado:** El servicio ejecuta el scraping estructurado ante el portal tributario, resolviendo cabeceras y extrayendo razón social oficial, estado `ACTIVO` y condición de domicilio `HABIDO`.

### 3. Pruebas de Motor Tarifario y Reglas de Negocio (`BR-TAR`)
* **`TC-TAR-01`: Cubicaje y Cálculo de Flete en Servidor:**
  - **Escenario:** Paquete de dimensiones $40 \times 30 \times 20\text{ cm}$ con peso físico de $2\text{ kg}$.
  - **Cálculo Backend:** Peso volumétrico $(40 \times 30 \times 20) / 6000 = 4.0\text{ kg}$. Peso liquidable $\max(2.0, 4.0) = 4.0\text{ kg}$.
  - **Tarifa Base:** S/ 8.00 (cubre primeros 2 kg) + S/ 2.50 $\times$ 2 kg adicionales = S/ 13.00.
  - **Resultado:** El frontend nunca calcula el precio final; el backend responde con desglose inmutable y cálculo de IGV (18%).

### 4. Pruebas de la Cadena Operativa E2E del Ciclo de Vida del Envío
* **`TC-PED-01`: Pre-registro y Tracking:** Generación de pre-orden en estado `registrado`, generación de tracking `CE-2026-XXXXX` y voucher imprimible.
* **`TC-PAG-01`: Pago Simulado con Webhook Criptográfico:** Recepción de firma `X-Webhook-Signature` y actualización atómica del estado contable a `pagado`.
* **`TC-CAJ-01`: Admisión en Ventanilla (Pesaje en Balanza Oficial `BR-TAR-02`):** El cajero coloca el paquete en balanza; si el peso real supera lo declarado en la web, el sistema calcula automáticamente el reintegro y cobra la diferencia en caja antes de cambiar a `en_almacen_origen`.
* **`TC-ALM-01`: Despacho a Ruta (`BR-ENV-02`):** El almacenero carga el camión. El sistema valida que el paquete esté pagado; de lo contrario, impide el despacho. Al confirmar, transiciona a `en_ruta`.
* **`TC-ALM-02`: Arribo y Descarga (`BR-ENV-03`):** El almacenero de la agencia destino descarga el camión interprovincial y transiciona el paquete a `en_agencia_destino`.
* **`TC-ENT-01`: Entrega Final con Validación de DNI (`BR-ENV-04`):** El cliente se acerca a ventanilla. El sistema exige obligatoriamente registrar el DNI del receptor físico, sus nombres completos y parentesco. Tras validar, sella la orden en `entregado` y registra la fecha real de recepción.

### 5. Pruebas de Seguridad Dinámica (DAST) y Control de Acceso
* **`TC-SEC-01`: Auditoría OWASP ZAP v2.17.0:**
  - **Resultado:** 0 Vulnerabilidades Críticas/Altas (sin inyección SQL ni fugas de credenciales).
  - **Mitigación:** Inyección de `Content-Security-Policy` Level 3 con `form-action` y `base-uri`, y validación criptográfica Subresource Integrity (`integrity="sha384-..."`) en Swagger UI.
* **`TC-RBAC-01`: Control de Acceso Basado en Roles:**
  - Intento de un usuario con rol `ALMACEN` de invocar `POST /api/v1/usuarios` o ver la recaudación monetaria.
  - **Resultado:** Backend responde con `HTTP 403 Forbidden` y el Frontend oculta reactivamente las tarjetas financieras en el Dashboard.
* **`TC-PII-01`: Privacidad y Protección de Datos Personales:**
  - Endpoint público `/api/v1/publico/tracking/{codigo}` retorna datos de remitente y destinatario ofuscados (ej. `987***321`, `L*** M***`), garantizando cumplimiento de la Ley de Protección de Datos Personales (Ley N° 29733).
