-- =======================================================================
-- MIGRACIÓN 001: MEJORAS DE SEGURIDAD, AUDITORÍA Y CONTROL DE ACCESO
-- Proyecto: CargaExpress Perú (Backend FastAPI)
-- Base de Datos: PostgreSQL 17
-- =======================================================================

-- 1. Ampliación de seguridad en la tabla de usuarios
ALTER TABLE public.usuarios 
    ADD COLUMN IF NOT EXISTS agencia_id INTEGER REFERENCES public.agencias(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP(6) WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS ultimo_cambio_password TIMESTAMP(6) WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS sesion_version INTEGER DEFAULT 1 NOT NULL,
    ADD COLUMN IF NOT EXISTS bloqueado_hasta TIMESTAMP(6) WITHOUT TIME ZONE;

-- Índices de rendimiento y unicidad para autenticación rápida
CREATE INDEX IF NOT EXISTS idx_usuarios_agencia_id ON public.usuarios(agencia_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_dni ON public.usuarios(dni);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON public.usuarios(email);

-- 2. Tabla inmutable de eventos de seguridad (Autenticación, 2FA, Bloqueos)
CREATE TABLE IF NOT EXISTS public.auditoria_seguridad (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
    evento VARCHAR(50) NOT NULL, -- 'LOGIN_EXITOSO', 'LOGIN_FALLIDO', '2FA_EXITOSO', '2FA_FALLIDO', 'BLOQUEO_CUENTA', 'LOGOUT', 'CAMBIO_PASSWORD'
    direccion_ip VARCHAR(45) NOT NULL,
    user_agent TEXT,
    detalles JSONB,
    nivel_riesgo VARCHAR(10) DEFAULT 'INFO' NOT NULL, -- 'INFO', 'WARN', 'CRITICAL'
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auditoria_seg_usuario ON public.auditoria_seguridad(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_seg_evento ON public.auditoria_seguridad(evento);
CREATE INDEX IF NOT EXISTS idx_auditoria_seg_fecha ON public.auditoria_seguridad(creado_en);

-- 3. Tabla inmutable de auditoría de operaciones de datos
CREATE TABLE IF NOT EXISTS public.auditoria_operaciones (
    id BIGSERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(60) NOT NULL,
    registro_id INTEGER NOT NULL,
    accion VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    valores_previos JSONB,
    valores_nuevos JSONB,
    usuario_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
    direccion_ip VARCHAR(45),
    request_id VARCHAR(36),
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_auditoria_ops_tabla_reg ON public.auditoria_operaciones(tabla_afectada, registro_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_ops_usuario ON public.auditoria_operaciones(usuario_id);
