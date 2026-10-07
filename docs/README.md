# Documentación Spec-Driven Development (SDD) - CargaExpress Backend

Bienvenido a la documentación de desarrollo y arquitectura guiada por especificaciones (**Spec-Driven Development - SDD**) para el backend independiente de **CargaExpress Perú**.

Este repositorio implementa la capa de servicios REST API con **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** y **PostgreSQL 17**, desacoplada de la interfaz de usuario ([CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront)).

---

## 1. ¿Qué es Spec-Driven Development (SDD) en CargaExpress?

El desarrollo guiado por especificaciones (SDD) establece que **ningún endpoint o modelo de base de datos se codifica sin una especificación técnica formal previa**, la cual define de manera estricta:
1. **Contrato de Interfaz:** Esquemas de entrada y salida validados con tipos estrictos (Pydantic v2).
2. **Parámetros de Seguridad:** Cumplimiento verificado de los estándares **OWASP Top 10 (2021)** y **OWASP API Security Top 10 (2023)**.
3. **Control de Acceso y Autorización:** Roles requeridos (RBAC), verificación de propiedad de recursos (anti-BOLA) y alcances de token JWT.
4. **Criterios de Aceptación para Auditoría:** Condiciones que deben superar las pruebas automatizadas y los escáneres de seguridad de código estático (SAST) y dinámico (DAST).

```text
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  1. Especificación      │ ──> │  2. Implementación      │ ──> │  3. Verificación SAST/  │
│  (Contrato + Seguridad) │     │  (FastAPI + Pydantic)   │     │     DAST & Migración    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

---

## 2. Estructura de la Documentación

La documentación se organiza en módulos progresivos para consultar durante cada fase de migración:

```text
CargaExpressBackend/docs/
├── README.md                                    # Índice general y metodología SDD (este archivo)
├── checklist-seguridad-migracion.md             # Matriz de verificación obligatoria por endpoint
├── seguridad/
│   ├── 01-owasp-top-10-desarrollo.md            # OWASP Top 10 (2021) aplicado a desarrollo Backend
│   ├── 02-owasp-api-security-top-10.md          # OWASP API Security Top 10 (2023) para endpoints REST
│   ├── 03-parametros-backend-seguro.md          # Parámetros técnicos: Headers, Cripto, CORS, Logs y DAST
│   ├── 04-auditoria-y-base-de-datos.md          # Pistas de auditoría y mitigación de fugas
│   └── 05-diseno-base-de-datos-auditoria-jwt.md # Arquitectura 3NF, JWT, inmutabilidad y exportación ER
└── sprints/
    ├── sprint-01-autenticacion-mfa.md           # Especificación de autenticación y 2FA
    ├── sprint-02-rediseño-base-de-datos-auditoria-jwt.md # Entrega de base de datos y sincronización
    ├── sprint-03-conexion-autenticacion-frontend.md # Integración y pruebas de login Frontend-Backend
    └── sprint-04-portal-publico-tracking-cotizador.md # Portal público, cotizador, tracking y pedidos
```

### Estado de Sprints de Migración (SDD)
| Sprint | Nombre | Módulo | Estado |
| :--- | :--- | :--- | :---: |
| **Sprint 01** | [Autenticación y MFA](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-01-autenticacion-mfa.md) | Backend Auth / JWT / 2FA | ✅ Completado |
| **Sprint 02** | [Rediseño BDD, Auditoría y JWT](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-02-rediseño-base-de-datos-auditoria-jwt.md) | PostgreSQL 17 / 3NF / Esquema Estrella | ✅ Completado |
| **Sprint 03** | [Conexión Auth Frontend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-03-conexion-autenticacion-frontend.md) | React Vite ➔ FastAPI (Login + 2FA + QR) | ✅ Certificado E2E |
| **Sprint 04** | [Portal Público, Tracking y Cotizador](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-04-portal-publico-tracking-cotizador.md) | Agencias / Cotizador / Tracking PII / Pedidos Web | 🚀 Listo para Conexión |

> **Base de Datos Canónica Activa:** [`cargaexpress_clean.sql`](file:///c:/Users/User/Documents/VSC-Integrador/cargaexpress_clean.sql) (PostgreSQL 17, 3NF, pistas de auditoría inmutables, tablas maestras y desglose contable).  
> **Modo Local:** SQLite [`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db) inicializado con [`init_local_db.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/init_local_db.py).

## 3. Protocolo de Migración por Endpoint / Módulo

Cada vez que se traslade una funcionalidad desde el sistema legacy (`cargaexpress-`) hacia este backend (`CargaExpressBackend`), el desarrollador debe seguir este ciclo:

1. **Revisar el catálogo de riesgos OWASP:**
   - Comprobar [01-owasp-top-10-desarrollo.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/01-owasp-top-10-desarrollo.md).
   - Comprobar [02-owasp-api-security-top-10.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/02-owasp-api-security-top-10.md).
2. **Definir el Contrato de Datos (Pydantic v2):**
   - Reglas estrictas de validación de campos (`min_length`, `max_length`, `regex`, `gt`, `le`).
   - Prohibición de asignación masiva (`extra = 'forbid'`).
3. **Aplicar los Parámetros de Endurecimiento:**
   - Seguir las directrices de [03-parametros-backend-seguro.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/03-parametros-backend-seguro.md).
4. **Completar el Checklist de Seguridad:**
   - Marcar los puntos correspondientes en [checklist-seguridad-migracion.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/checklist-seguridad-migracion.md).
5. **Ejecutar Pruebas y Análisis de Seguridad:**
   - Análisis estático de código (SAST) con `bandit` y linters de seguridad.
   - Verificación de contratos con suites de tests automatizados (`pytest`).
