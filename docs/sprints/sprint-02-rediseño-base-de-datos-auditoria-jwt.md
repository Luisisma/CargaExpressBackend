# Sprint 02: Entrega de Arquitectura - Nueva Base de Datos Relacional Normalizada, Auditoría OWASP y Preparación Star Schema

> **Módulo:** Persistencia, Seguridad Relacional, Auditoría Inmutable y Modelado Dimensional  
> **Archivo Maestro:** [`cargaexpress.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress.sql) *(Sobrescrito y sincronizado)*  
> **Respaldo de Referencia:** [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql)  
> **Estado del Sprint:** ✅ **100% COMPLETADO Y SINCRONIZADO**

---

## 1. Objetivos del Sprint Cumplidos

El objetivo principal de este sprint fue reemplazar el volcado original desestructurado por una **base de datos de grado de producción**, normalizada en Tercera Forma Normal (3NF), blindada según los lineamientos de **OWASP Top 10** y **OWASP API Security Top 10**, con soporte integral para autenticación **JWT**, control de pistas de auditoría inmutables y optimizada para extracción hacia un **Data Warehouse (Esquema Estrella)**.

---

## 2. Matriz de Entregables y Cambios Implementados

### 2.1. Normalización Relacional (3NF) y Datos Semilla (Seeds)
* **Ubigeo y Regiones Oficiales:** Se creó y pobló la tabla `departamentos` con los 25 departamentos del Perú con códigos INEI.
* **Enlace Estricto de Sedes:** Las 52 agencias nacionales fueron re-enlazadas con clave foránea `departamento_id REFERENCES departamentos(id) ON DELETE RESTRICT`, eliminando registros nulos y redundancias.
* **Tipos de Dominio (ENUM):** Se crearon 15 tipos ENUM nativos (`rol_usuario_enum`, `tipo_envio_enum`, `estado_envio_enum`, `estado_pago_enum`, `tipo_comprobante_enum`, etc.) para impedir que el motor acepte estados inconsistentes.

### 2.2. Seguridad OWASP Top 10 y Gestión de JWT
* **Aislamiento por Sede (OWASP API1 / BOLA):** Inclusión mandatoria de `agencia_id` con índice B-Tree en `usuarios` y validación de `agencia_origen_id` / `agencia_destino_id` en `envios`.
* **Revocación Global de JWT (OWASP API2 / A07):** Inclusión de `sesion_version INTEGER DEFAULT 1` en `usuarios`. Cada vez que el usuario cambia de credenciales o presiona Logout, este número se incrementa y la API rechaza al instante cualquier token previo.
* **Rotación y Auditoría de Refresh Tokens:** Creación de la tabla `sesiones_jwt` para almacenar hash SHA-256 (`token_hash`), `jti`, IP, User-Agent y expiración.
* **Control Anti-Fuerza Bruta:** Columnas `intentos_fallidos`, `bloqueado` y `bloqueado_hasta` para lockout temporal exponencial.
* **MFA / TOTP:** Columnas dedicadas `totp_secret` y `totp_configurado`.

### 2.3. Módulo Financiero y Facturación Electrónica (SUNAT)
* Se implementó el desglose contable en la tabla `envios`:
  * `monto_subtotal`: Valor neto antes de impuestos.
  * `monto_descuento`: Descuentos comerciales o promociones.
  * `monto_igv`: 18% del neto gravado.
  * `precio_envio`: Total bruto final a pagar.
* Restricciones `CHECK` para garantizar que ningún monto sea negativo (`chk_envios_subtotal_positivo`, etc.).

### 2.4. Sistema Dual de Auditoría Inmutable (OWASP A09:2021)
* **`auditoria_seguridad`:** Registro de eventos de autenticación (`LOGIN_EXITOSO`, `LOGIN_FALLIDO`, `2FA_EXITOSO`, `BLOQUEO_CUENTA`, `LOGOUT`), IP, User-Agent y JSONB.
* **`auditoria_operaciones`:** Registro de operaciones DML en tablas críticas con fotografía previa y nueva (`valores_previos`, `valores_nuevos` en JSONB), usuario y `request_id`.
* **Append-Only Enforcement:** Disparadores PL/pgSQL que impiden de forma terminante cualquier sentencia `UPDATE` o `DELETE` sobre las tablas de auditoría.

### 2.5. Habilitadores para Migración a Esquema Estrella (Power BI / Data Warehouse)
* **CDC (Change Data Capture) Incremental:** Se agregaron columnas `actualizado_en` y triggers automáticos en `vehiculos`, `asignaciones_vehiculo` y `aperturas_caja`.
* **Georreferenciación:** Columna `ubigeo VARCHAR(6)` en `agencias` para mapas y dashboards geográficos.
* **Tarificación y Métricas Logísticas:** Columna `peso_volumetrico NUMERIC(8,2)` en `envios` para análisis de densidad de carga y llenado de unidades en la tabla de hechos `Fact_Envios`.

---

## 3. Estado de la Sincronización

* **Archivo Maestro:** [`cargaexpress.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress.sql) ha sido sobrescrito y sincronizado exitosamente con el esquema limpio.
* **Compatibilidad de Diagramado:** El archivo utiliza sintaxis SQL ANSI estándar (sin directivas `\restrict` ni comandos propietarios `COPY`), garantizando la generación inmediata del Diagrama Entidad-Relación en **DBeaver**, **drawSQL**, **dbdiagram.io** y **pgAdmin 4**.
* **Próxima Fase:** Desarrollo integral de los modelos SQLAlchemy 2.0 y endpoints en [`CargaExpressBackend`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend).
