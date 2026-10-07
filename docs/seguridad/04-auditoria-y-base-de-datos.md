# Auditoría de Base de Datos y Parámetros de Seguridad en Persistencia

Este documento especifica las mejoras de seguridad, trazabilidad e inmutabilidad requeridas en la base de datos PostgreSQL 17 para **CargaExpress**, complementando el esquema original de `cargaexpress.sql`.

---

## 1. Justificación y Deficiencias del Esquema Original

En una auditoría de seguridad y cumplimiento normativo (SAST/DAST, ISO 27001, PCI-DSS):
1. **Ausencia de Pista de Auditoría (Audit Trail):** El esquema original solo registraba `historial_envios` para fines operativos de cara al cliente, pero **no existía ningún registro de quién modificó usuarios, quién cambió roles, ni bitácora de intentos fallidos de autenticación**.
2. **Falta de Aislamiento de Sucursal en Usuarios:** La tabla `usuarios` no contaba con un campo `agencia_id`. Esto impedía aplicar de forma estricta la regla **OWASP API1:2023 (BOLA)** para confinar al personal de ventanilla y almacén a su propia sede física.
3. **Control de Invalidez de Sesiones:** Sin un campo de control de versión o invalidación de tokens (`sesion_version`), si un empleado era despedido o su contraseña cambiada, los tokens JWT previamente emitidos continuaban siendo válidos hasta su expiración natural.

---

## 2. Mejoras de Seguridad a Implementar

### 2.1. Tabla `auditoria_seguridad` (Eventos de Autenticación y Acceso)
Registra de forma inmutable cada intento de acceso, activación de 2FA, fallos de credenciales y bloqueos:

```sql
CREATE TABLE public.auditoria_seguridad (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
    evento VARCHAR(50) NOT NULL, -- 'LOGIN_EXITOSO', 'LOGIN_FALLIDO', '2FA_EXITOSO', '2FA_FALLIDO', 'BLOQUEO_CUENTA', 'LOGOUT', 'CAMBIO_PASSWORD'
    direccion_ip VARCHAR(45) NOT NULL, -- Compatible con IPv4 e IPv6
    user_agent TEXT,
    detalles JSONB, -- Datos adicionales en formato JSON estructurado
    nivel_riesgo VARCHAR(10) DEFAULT 'INFO', -- 'INFO', 'WARN', 'CRITICAL'
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_auditoria_seg_usuario ON public.auditoria_seguridad(usuario_id);
CREATE INDEX idx_auditoria_seg_evento ON public.auditoria_seguridad(evento);
CREATE INDEX idx_auditoria_seg_fecha ON public.auditoria_seguridad(creado_en);
```

### 2.2. Tabla `auditoria_operaciones` (Trazabilidad de Cambios en Datos Críticos)
Registra cualquier alteración (INSERT, UPDATE, DELETE) en tablas financieras, usuarios o envíos:

```sql
CREATE TABLE public.auditoria_operaciones (
    id BIGSERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(60) NOT NULL,
    registro_id INTEGER NOT NULL,
    accion VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    valores_previos JSONB,
    valores_nuevos JSONB,
    usuario_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
    direccion_ip VARCHAR(45),
    request_id VARCHAR(36), -- Correlation ID
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_auditoria_ops_tabla_reg ON public.auditoria_operaciones(tabla_afectada, registro_id);
CREATE INDEX idx_auditoria_ops_usuario ON public.auditoria_operaciones(usuario_id);
```

### 2.3. Ampliación de Seguridad en `usuarios`
Se agregan los siguientes campos a la tabla existente `usuarios`:

| Columna | Tipo | Propósito de Seguridad |
| :--- | :--- | :--- |
| `agencia_id` | `INTEGER REFERENCES agencias(id)` | Confinamiento BOLA: Restringe al cajero/almacenero a los datos de su sede. |
| `ultimo_login` | `TIMESTAMP` | Detección de cuentas inactivas y verificación de última actividad legítima. |
| `ultimo_cambio_password` | `TIMESTAMP` | Expiración forzada periódica y políticas de cambio de credenciales. |
| `sesion_version` | `INTEGER DEFAULT 1` | Invalidación instantánea de JWTs emitidos al cerrar sesión o cambiar clave. |
| `bloqueado_hasta` | `TIMESTAMP` | Bloqueo temporal exponencial ante ataques de fuerza bruta (anti-brute force). |

---

## 3. Inmutabilidad de los Registros de Auditoría
* Los registros en `auditoria_seguridad` y `auditoria_operaciones` son **Append-Only** (solo inserción).
* Queda estrictamente prohibido implementar endpoints o permisos de base de datos que ejecuten `UPDATE` o `DELETE` sobre las tablas de auditoría.
