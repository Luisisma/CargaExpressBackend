# Especificación de Arquitectura de Base de Datos: Normalización, Auditoría y Seguridad JWT

**Proyecto:** CargaExpress Perú  
**Motor:** PostgreSQL 15 / 16 / 17  
**Archivo DDL Maestro:** [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql)  
**Estándares de Cumplimiento:** OWASP Top 10 (2021) | OWASP API Security Top 10 (2023) | ISO 27001 (Audit Trail)

---

## 1. Resumen Ejecutivo y Motivación del Rediseño

El esquema heredado (`cargaexpress.sql`) presentaba limitaciones que comprometían tanto el desempeño operativo como la postura de seguridad de la API:
1. **Redundancia y falta de 3NF:** Las 52 agencias registraban el nombre del departamento como cadena de texto, mientras que la tabla maestra `departamentos` se encontraba vacía y desconectada (`departamento_id` nulo).
2. **Ausencia de Aislamiento por Sede (BOLA / OWASP API1):** Los usuarios operativos (cajeros, supervisores) no estaban formalmente confinados a una agencia en la base de datos, impidiendo restringir consultas por sucursal en el backend FastAPI.
3. **Gestión Insegura de JWT y Sesiones (OWASP API2):** No existía mecanismo de invalidación reactiva de tokens (`sesion_version`) ni almacenamiento para rotación de refresh tokens (`sesiones_jwt`).
4. **Carencia de Auditoría Integral (OWASP A09):** Las modificaciones financieras (`movimientos_caja`), aperturas de turno y cambios de estado en guías carecían de trazabilidad formal inmutable.
5. **Formato Propietario pg_dump:** El archivo original contenía directivas restrictivas (`\restrict`) y comandos binarios (`COPY`) que bloqueaban la generación automática de diagramas en herramientas como DBeaver, dbdiagram.io o drawSQL.

---

## 2. Principios de Normalización (Tercera Forma Normal - 3NF)

El nuevo diseño en [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql) implementa:

```
[departamentos] (1) <--- (N) [agencias] (1) <--- (N) [usuarios]
                                |
                                +--- (1) <--- (N) [envios] (origen / destino)
                                |
                                +--- (1) <--- (N) [guias_remision]
```

* **1NF (Atomicidad):** Separación rigurosa de nombres, apellidos, ubicaciones y códigos de identificación (DNI, RUC, serie y correlativo de comprobantes).
* **2NF (Dependencia Funcional Completa):** Eliminación de dependencias parciales en tablas intermedias como `guias_remision_detalle` y `manifiestos_detalle`, las cuales utilizan restricciones de unicidad compuestas (`uq_guia_envio`, `uq_manifiesto_envio`).
* **3NF (Eliminación de Dependencias Transitivas):** 
  * Se pobló el catálogo oficial de los 25 departamentos del Perú con códigos INEI.
  * Cada una de las 52 agencias está enlazada mediante `departamento_id REFERENCES departamentos(id) ON DELETE RESTRICT`.

---

## 3. Matriz de Mitigación: OWASP Top 10 & API Security

| Riesgo OWASP | Vector de Vulnerabilidad | Implementación en la Base de Datos (`cargaexpress_clean.sql`) |
| :--- | :--- | :--- |
| **A01:2021 & API1:2023**<br>Broken Object Level Authorization (BOLA) | Operador de sede A modifica o consulta encomiendas de sede B manipulando el ID en la URL. | `usuarios.agencia_id` con índice B-Tree forzoso. `envios.agencia_origen_id` y `envios.agencia_destino_id` con `REFERENCES agencias(id) ON DELETE RESTRICT`. Permite cláusulas obligatorias `WHERE agencia_id = current_user.agencia_id` en SQLAlchemy. |
| **A02:2021**<br>Cryptographic Failures | Hashes vulnerables o filtración de credenciales. | `password_hash VARCHAR(255)` compatible con Argon2id y Bcrypt (12 rondas). Protección de secretos MFA en `totp_secret VARCHAR(32)`. Los tokens JWT no se guardan en texto plano; `sesiones_jwt.token_hash` almacena únicamente el hash SHA-256. |
| **A03:2021 & API8:2023**<br>Injection & Security Misconfiguration | Parámetros manipulados y estados arbitrarios. | Tipos `ENUM` nativos de PostgreSQL y restricciones `CHECK` a nivel motor (`chk_usuarios_dni_formato`, `chk_envios_peso_positivo`, `chk_movimientos_monto_positivo`, `chk_aperturas_saldo_inicial`). |
| **A04:2021**<br>Insecure Design | Descuadres de caja o importes negativos. | Restricciones `CHECK` para montos mayores a cero en `movimientos_caja` e importes no negativos en `aperturas_caja` y `envios`. |
| **A07:2021 & API2:2023**<br>Authentication & Session Failures | Robo de JWT, fuerza bruta y falta de expiración reactiva. | 1. **Revocación Global:** Columna `sesion_version INTEGER DEFAULT 1`. Al cambiar clave o pulsar logout, `sesion_version` se incrementa, invalidando inmediatamente todos los Access Tokens previos.<br>2. **Anti-Brute Force:** Columnas `intentos_fallidos`, `bloqueado` y `bloqueado_hasta` para bloqueo temporal exponencial.<br>3. **Rotación de Refresh Tokens:** Tabla `sesiones_jwt` con seguimiento de `jti`, IP y expiración. |
| **A08:2021**<br>Data Integrity Failures | Eliminación accidental en cascada de registros contables o guías. | Llaves foráneas con `ON DELETE RESTRICT` en transacciones críticas (`envios`, `guias_remision`, `aperturas_caja`). El borrado accidental de una agencia o cliente con envíos activos es bloqueado por el motor. |
| **A09:2021**<br>Security Logging Failures | Carencia de bitácora inmutable o auditoría alterable. | Tablas duales de auditoría inmutable: `auditoria_seguridad` y `auditoria_operaciones` protegidas con triggers plpgsql que abortan cualquier intento de `UPDATE` o `DELETE`. |

---

## 4. Arquitectura de Autenticación JWT y Flujo de Sesión

### 4.1. Ciclo de Vida del Token

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario / Frontend
    participant API as FastAPI Backend
    participant BD as PostgreSQL 17

    U->>API: POST /api/v1/auth/login {dni, password}
    API->>BD: SELECT * FROM usuarios WHERE dni = :dni
    BD--API: Datos del usuario (hash, intentos, sesion_version, agencia_id)
    
    alt Usuario con 2FA activo
        API-->>U: temp_token (5 min, scope: mfa_pending)
        U->>API: POST /api/v1/auth/2fa {temp_token, totp_code}
        API->>API: Valida TOTP con pyotp
    end

    API->>BD: INSERT INTO auditoria_seguridad ('LOGIN_EXITOSO', IP, user_agent)
    API->>BD: INSERT INTO sesiones_jwt (jti, token_hash, expira_en)
    API-->>U: {access_token (30m), refresh_token (7d)}

    Note over U,API: En cada petición subsecuente
    U->>API: GET /api/v1/admin/envios (Bearer access_token)
    API->>API: Decodifica JWT (sub, rol, agencia_id, sesion_version)
    API->>BD: Valida sesion_version contra tabla usuarios
    API-->>U: 200 OK con datos filtrados por agencia_id
```

### 4.2. Invalidación Forzada de Tokens (Logout / Cambio de Clave)
Cuando un usuario cambia su contraseña o el administrador suspende su cuenta:
```sql
UPDATE public.usuarios 
SET sesion_version = sesion_version + 1,
    ultimo_cambio_password = CURRENT_TIMESTAMP
WHERE id = :usuario_id;
```
Cualquier petición subsiguiente con un JWT que tenga `sesion_version` desactualizada es rechazada con código HTTP `401 Unauthorized`.

---

## 5. Sistema Dual de Pistas de Auditoría

### 5.1. `auditoria_seguridad` (Eventos de Acceso y MFA)
* **Objetivo:** Cumplimiento con auditorías de seguridad e investigación forense.
* **Eventos auditados:** `LOGIN_EXITOSO`, `LOGIN_FALLIDO`, `2FA_EXITOSO`, `2FA_FALLIDO`, `BLOQUEO_CUENTA`, `LOGOUT`, `CAMBIO_PASSWORD`, `REFRESH_TOKEN`.
* **Metadatos:** Dirección IP (IPv4/IPv6), User-Agent, nivel de riesgo (`INFO`, `WARN`, `CRITICAL`) y JSONB estructurado.

### 5.2. `auditoria_operaciones` (Modificaciones DML en Datos Críticos)
* **Objetivo:** Cumplimiento contable y fiscal (no repudio).
* **Captura:** `tabla_afectada`, `registro_id`, `accion` (`INSERT`, `UPDATE`, `DELETE`), `valores_previos` (JSONB) y `valores_nuevos` (JSONB), enlazados a `usuario_id` y al `request_id` (Correlation ID) de la solicitud HTTP.

### 5.3. Garantía de Inmutabilidad (*Append-Only Enforcement*)
A nivel de motor de base de datos se aplicaron disparadores automáticos:
```sql
CREATE TRIGGER trg_inmutable_auditoria_seguridad
    BEFORE UPDATE OR DELETE ON public.auditoria_seguridad
    FOR EACH ROW EXECUTE FUNCTION public.fn_prevenir_modificacion_auditoria();

CREATE TRIGGER trg_inmutable_auditoria_operaciones
    BEFORE UPDATE OR DELETE ON public.auditoria_operaciones
    FOR EACH ROW EXECUTE FUNCTION public.fn_prevenir_modificacion_auditoria();
```
Cualquier intento de modificar o borrar un registro de auditoría emite una excepción fatal:
`ERROR: VIOLACIÓN DE SEGURIDAD (OWASP A09): No está permitido modificar ni eliminar registros de la pista de auditoría inmutable.`

---

## 6. Guía de Exportación y Visualización de Diagrama Entidad-Relación (ER)

El archivo [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql) está escrito en **SQL ANSI estándar para PostgreSQL**, lo cual permite importarlo y visualizar su diagrama en múltiples herramientas:

### Opción A: DBeaver (Recomendado para trabajo local)
1. Abre **DBeaver** y conéctate a tu base de datos PostgreSQL local o de desarrollo.
2. Abre el editor SQL (`F3` o `Ctrl + ]`) y carga el archivo [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql).
3. Ejecuta todo el script con `Alt + X` (Execute SQL Script).
4. En el panel izquierdo *Navegador de Base de Datos*, haz doble clic sobre el esquema `public`.
5. Ve a la pestaña **Diagrama ER**: verás todas las relaciones, claves primarias, foráneas e índices perfectamente conectados sin errores.

### Opción B: dbdiagram.io / drawSQL (En línea sin instalar software)
1. Abre [dbdiagram.io](https://dbdiagram.io/) o [drawSQL](https://drawsql.app/).
2. Haz clic en **Import** -> **Import PostgreSQL script**.
3. Pega el contenido de [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql).
4. La herramienta generará automáticamente el esquema interactivo con todas las entidades.

### Opción C: pgAdmin 4
1. En pgAdmin, haz clic derecho sobre tu base de datos -> **Query Tool**.
2. Abre y ejecuta [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql).
3. Haz clic derecho sobre la base de datos o el esquema `public` -> **Generate ERD** (Generar diagrama de relaciones).

---

## 7. Mapeo de Entidades y Compatibilidad con Backend FastAPI

| Tabla en BD | Modelo SQLAlchemy | Propósito Principal |
| :--- | :--- | :--- |
| `departamentos` | `app.models.departamento.Departamento` | Catálogo maestro de regiones con código INEI. |
| `agencias` | `app.models.agencia.Agencia` | Sedes y puntos de emisión/recepción con Ubigeo. |
| `usuarios` | `app.models.usuario.Usuario` | Cuentas, roles RBAC, hashes bcrypt, 2FA y control de versión JWT. |
| `sesiones_jwt` | `app.models.sesion.SesionJWT` | Trazabilidad de Refresh Tokens emitidos y activos. |
| `clientes` | `app.models.cliente.Cliente` | Directorio unificado de remitentes y destinatarios (DNI/RUC). |
| `vehiculos` | `app.models.vehiculo.Vehiculo` | Flota vehicular de transporte. |
| `asignaciones_vehiculo` | `app.models.vehiculo.AsignacionVehiculo` | Vínculo conductor - unidad de transporte. |
| `aperturas_caja` | `app.models.caja.AperturaCaja` | Turnos y arqueos financieros por ventanilla. |
| `movimientos_caja` | `app.models.caja.MovimientoCaja` | Ingresos y egresos en efectivo vinculados a envíos. |
| `envios` | `app.models.envio.Envio` | Gestión operativa central de encomiendas y fletes. |
| `historial_envios` | `app.models.envio.HistorialEnvio` | Hitos cronológicos de cara al tracking web del cliente. |
| `guias_remision` | `app.models.logistica.GuiaRemision` | Guías electrónicas de traslado de encomiendas. |
| `guias_remision_detalle` | `app.models.logistica.GuiaRemisionDetalle` | Encomiendas consolidadas en una guía. |
| `manifiestos` | `app.models.logistica.Manifiesto` | Despachos interprovinciales por camión. |
| `manifiestos_detalle` | `app.models.logistica.ManifiestoDetalle` | Paquetes y guías asignados al manifiesto. |
| `auditoria_seguridad` | `app.models.auditoria.AuditoriaSeguridad` | Registro inmutable de autenticación y 2FA. |
| `auditoria_operaciones` | `app.models.auditoria.AuditoriaOperaciones` | Registro inmutable de modificaciones en datos críticos. |

---

## 8. Preguntas Frecuentes de Arquitectura y Negocio

### 8.1. ¿Cómo se almacenan los montos (Neto, Bruto, IGV y Descuentos)?
Para cumplir con las normas de facturación electrónica en Perú (SUNAT) y permitir futuras políticas comerciales (cupones, convenios corporativos o descuentos por volumen), la tabla `envios` desglosa el cálculo financiero en 4 columnas con precisión fija `NUMERIC(10,2)`:

1. `monto_subtotal`: Valor neto antes de impuestos (base imponible).
2. `monto_descuento`: Deducción comercial aplicada (por defecto `0.00`).
3. `monto_igv`: Impuesto General a las Ventas correspondiente al 18% legal del neto gravado.
4. `precio_envio`: Importe total bruto a pagar por el cliente (`(subtotal - descuento) + IGV`).

Cada una de estas columnas cuenta con restricciones `CHECK` que impiden montos negativos a nivel de base de datos (`chk_envios_subtotal_positivo`, `chk_envios_descuento_positivo`, etc.).

### 8.2. ¿Dónde se almacena el Bearer Token en la Base de Datos?
**El Bearer Token (Access Token) NO se almacena en la base de datos.**
* **Principio Stateless (Sin Estado):** El Access Token viaja en la cabecera HTTP `Authorization: Bearer <token>`. El servidor backend verifica su firma criptográfica en memoria en microsegundos utilizando la clave secreta `SECRET_KEY`, sin necesidad de hacer lecturas a la base de datos en cada request.
* **¿Qué sí se persiste en la BD?**:
  1. `usuarios.sesion_version`: Permite revocación instantánea. Si el usuario cierra sesión o cambia clave, este número se incrementa en la BD y el backend rechaza de inmediato cualquier Bearer Token con una versión anterior.
  2. `sesiones_jwt`: Registra únicamente el hash del **Refresh Token** (larga duración) para rotación y control de dispositivos activos.

### 8.3. ¿Quién genera el JWT y cuánto dura? ¿Es configurable?
* **Emisor:** El backend **FastAPI**, mediante el módulo `app.core.security` (`create_access_token` y `create_refresh_token`).
* **Vigencias recomendadas y por defecto (OWASP):**
  * **Access Token (Bearer):** **30 minutos**. Breve duración para mitigar riesgos si el token es interceptado en tránsito.
  * **Refresh Token:** **7 días**. Duración extendida para renovar el Access Token de forma transparente sin solicitar nuevamente el login.
  * **Token Temporal 2FA (`mfa_pending`):** **5 minutos**. Tiempo de gracia estricto para validar el código de 6 dígitos de Google Authenticator.
* **Configuración:** Es 100% configurable mediante variables de entorno en el archivo `.env` del backend a través de la clase `Settings` (`app.core.config.py`):
  * `ACCESS_TOKEN_EXPIRE_MINUTES = 30`
  * `REFRESH_TOKEN_EXPIRE_DAYS = 7`
  * `TEMP_TOKEN_EXPIRE_MINUTES = 5`
  * Puede parametrizarse para que roles con caja abierta expiren antes por política de turno laboral.

---

## 9. Preparación para Migración a Esquema Estrella (Data Warehouse / BI)

La base de datos actual está diseñada bajo el paradigma **OLTP (3NF)** para garantizar transacciones ACID rápidas y seguras. Para su posterior extracción hacia un **Data Warehouse (OLAP / Esquema Estrella)** en Power BI o Snowflake, se dejaron preparadas las siguientes bases arquitectónicas:

### 9.1. Soporte para Extracción Incremental (CDC - Change Data Capture)
Todo proceso ETL/ELT moderno requiere extraer solo los datos nuevos o modificados sin sobrecargar el servidor operacional:
* **Timestamps y Triggers Universales:** Las tablas clave (`envios`, `aperturas_caja`, `vehiculos`, `asignaciones_vehiculo`, `agencias`, `clientes`, `usuarios`, `guias_remision`, `manifiestos`) cuentan con columnas `creado_en` y `actualizado_en`, sincronizadas automáticamente mediante el disparador `fn_actualizar_timestamp()`.
* **Filtro de Extracción (Watermark):** La herramienta ETL (Airflow, dbt o Azure Data Factory) puede ejecutar:
  ```sql
  SELECT * FROM public.envios WHERE actualizado_en > :ultima_fecha_etl;
  ```
* **Trazabilidad de Eliminaciones Físicas:** Si en el OLTP se eliminara algún registro, la tabla inmutable `auditoria_operaciones` mantiene el registro `DELETE` con su `registro_id`, permitiendo al Data Warehouse marcar registros inactivos o aplicar *Soft Deletes* sin inconsistencias.

### 9.2. Modelo Dimensional Propuesto (Star Schema)

```
                       ┌─────────────────────────┐
                       │       Dim_Fecha         │
                       └────────────┬────────────┘
                                    │
┌────────────────────────┐          │          ┌────────────────────────┐
│      Dim_Cliente       ├──────────┤          │   Dim_Agencia_Origen   │
│ (Remitente/Destinat.)  │          │          │   (Ubigeo / Región)    │
└────────────────────────┘          │          └───────────┬────────────┘
                                    │                      │
                       ┌────────────┴────────────┐         │
                       │       Fact_Envios       ├─────────┘
                       │ ─────────────────────── │
                       │ * fecha_registro_id     │          ┌────────────────────────┐
                       │ * fecha_entrega_id      ├──────────┤  Dim_Agencia_Destino   │
                       │ * remitente_id          │          └────────────────────────┘
                       │ * destinatario_id       │
                       │ * agencia_origen_id     │          ┌────────────────────────┐
                       │ * agencia_destino_id    ├──────────┤      Dim_Vehiculo      │
                       │ * vehiculo_id           │          └────────────────────────┘
                       │ * estado_id             │
                       │ ─────────────────────── │          ┌────────────────────────┐
                       │ [Métricas Aditivas]     ├──────────┤       Dim_Estado       │
                       │ + peso_kg               │          └────────────────────────┘
                       │ + peso_volumetrico      │
                       │ + peso_facturable       │          ┌────────────────────────┐
                       │ + monto_subtotal        ├──────────┤      Dim_Operador      │
                       │ + monto_descuento       │          └────────────────────────┘
                       │ + monto_igv             │
                       │ + precio_envio_total    │
                       │ + tiempo_entrega_horas  │
                       │ + dias_retraso          │
                       └─────────────────────────┘
```

### 9.3. Métricas y Atributos ya Disponibles en el OLTP
1. **Georreferenciación y Jerarquías:** Campo `ubigeo` (código INEI de 6 dígitos) en `agencias` para mapas de calor provinciales y departamentales en Power BI.
2. **Métricas de Tarificación y Carga:** `peso_kg`, `alto_cm`, `ancho_cm`, `largo_cm` y `peso_volumetrico` permiten calcular en el DW la densidad de carga (`volumen m³`) y el factor de llenado vehicular.
3. **Métricas Financieras Auditables:** `monto_subtotal`, `monto_descuento`, `monto_igv` y `precio_envio` permiten analizar margen neto, impacto de promociones y recaudación tributaria.
4. **SLA y Tiempos de Servicio:** Las columnas `creado_en`, `fecha_estimada` y `fecha_entrega_real` permiten calcular automáticamente en el DW:
   * **Tiempo de Ciclo:** `EXTRACT(EPOCH FROM (fecha_entrega_real - creado_en)) / 3600` (horas).
   * **Cumplimiento de Promesa (On-Time Delivery):** `CASE WHEN fecha_entrega_real::date <= fecha_estimada THEN 1 ELSE 0 END`.


