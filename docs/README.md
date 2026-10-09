# Documentación Spec-Driven Development (SDD) - CargaExpress Backend

Bienvenido al centro de documentación técnica, arquitectura y reglas de negocio guiadas por especificaciones (**Spec-Driven Development - SDD**) para el backend de **CargaExpress Perú**.

Este repositorio implementa la capa de servicios REST API con **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** y **PostgreSQL 17** (con soporte SQLite local), completamente desacoplada de la interfaz de usuario ([CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront)).

---

## 1. Principio Fundamental: Separación entre Especificación Viva y Sprints

Para evitar acumular toda la lógica de negocio y arquitectura en notas temporales de entrega, la documentación se divide en tres niveles fundamentales:

1. **🏛️ Arquitectura Técnica Viva ([`docs/arquitectura/`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/arquitectura)):** Define cómo está construido el backend (capas, flujos de datos, modelos ORM, seguridad JWT, RBAC y dependencias). Es la fuente canónica de diseño técnico del sistema.
2. **📋 Reglas de Negocio Codificadas ([`docs/negocio/`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio)):** Define **QUÉ** se puede y **QUÉ NO** se puede hacer en el negocio logístico (estados de envíos, fórmulas de flete, identificación fiscal RENIEC/SUNAT, arqueo de caja y cancelaciones). Son de obligatorio cumplimiento para el backend.
3. **🏃 Bitácora de Sprints y Roadmap ([`docs/sprints/`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints)):** Registra el progreso cronológico y las fases de entrega del equipo. Los sprints implementan y consumen la arquitectura y las reglas de negocio, pero no las sustituyen.

```text
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│     ARQUITECTURA TÉCNICA        │     │        REGLAS DE NEGOCIO        │
│    (docs/arquitectura/*.md)     │     │       (docs/negocio/*.md)       │
│  - Capas Limpias (FastAPI)      │     │  - BR-ENV: Estados y Envíos     │
│  - Modelo de Datos 3NF          │     │  - BR-TAR: Tarifario y Cubicaje │
│  - Seguridad, JWT y RBAC        │     │  - BR-CLI: RENIEC/SUNAT Fiscal  │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │   HISTORIAL DE SPRINTS  │
                        │    (docs/sprints/*.md)  │
                        │   Sprint 01 al Sprint 06│
                        └─────────────────────────┘
```

---

## 2. Mapa Integral de la Documentación SDD

```text
CargaExpressBackend/docs/
├── README.md                                        # Índice general y metodología SDD (este archivo)
├── checklist-seguridad-migracion.md                 # Matriz de verificación obligatoria por endpoint
│
├── arquitectura/                                    # 🏛️ ESPECIFICACIÓN VIVA DE ARQUITECTURA
│   ├── 01-arquitectura-backend-capas.md             # Clean Layers: Routers, Services, Schemas y ORM
│   ├── 02-modelo-datos-persistencia.md            # Diagrama ERD, 3NF, integridad referencial y PostgreSQL/SQLite
│   └── 03-seguridad-autenticacion-rbac.md         # JWT, TOTP 2FA, invalidación sesion_version y RBAC
│
├── negocio/                                         # 📋 REGLAS DE NEGOCIO Y POLÍTICAS (BUSINESS RULES)
│   ├── 01-politicas-cancelaciones-reembolsos.md     # BR-CAN: Cancelaciones, Notas de Crédito y Reembolsos
│   ├── 02-modelo-cobros-qr-pasarela-recalculo.md    # BR-COB: Cobros duales, Webhooks y Pesaje Real
│   ├── 03-ciclo-vida-envio-transicion-estados.md   # BR-ENV: Matriz de estados, actores y transiciones secuenciales
│   ├── 04-motor-tarifario-cubicaje-flete.md        # BR-TAR: Cubicaje (L*A*H)/6000, flete base y recálculo
│   ├── 05-clientes-identidad-fiscal.md             # BR-CLI: Validación RENIEC/SUNAT y límites de Boleta/Factura
│   └── 06-caja-arqueo-comprobantes.md              # BR-CAJ: Turnos de caja, métodos de pago y arqueo ciego
│
├── roles/                                           # 👥 MATRIZ RBAC Y FLUJOS DE TRABAJO OPERATIVOS
│   ├── 01-matriz-roles-permisos-rbac.md             # Matriz NIST RBAC: módulos de Frontend y endpoints Backend
│   ├── 02-flujo-trabajo-almacen.md                  # Rol ALMACEN: Despacho a ruta y arribo/descarga en bodega
│   └── 03-flujo-trabajo-cajero-ventanilla.md        # Rol CAJERO: Apertura caja, pesaje balanza y entrega con DNI
│
├── seguridad/                                       # 🛡️ MARCO DE SEGURIDAD Y NORMATIVAS OWASP
│   ├── 01-owasp-top-10-desarrollo.md                # OWASP Top 10 (2021) aplicado al Backend
│   ├── 02-owasp-api-security-top-10.md              # OWASP API Security Top 10 (2023) para REST
│   ├── 03-parametros-backend-seguro.md              # Headers, CORS, criptografía y análisis DAST
│   ├── 04-auditoria-y-base-de-datos.md              # Trazabilidad forense y mitigación de fugas
│   ├── 05-diseno-base-de-datos-auditoria-jwt.md     # Especificación DDL y normalización 3NF
│   └── 06-auditoria-dast-owasp-zap.md              # Informe de auditoría DAST con OWASP ZAP y remediaciones SRI/CSP
│
└── sprints/                                         # 🏃 HISTORIAL Y BITÁCORA DE ENTREGAS
    ├── sprint-01-autenticacion-mfa.md               # Autenticación, JWT y segundo factor TOTP
    ├── sprint-02-rediseño-base-de-datos-auditoria-jwt.md # Migración DDL y base de datos canónica
    ├── sprint-03-conexion-autenticacion-frontend.md # Conexión E2E de login y 2FA con React Vite
    ├── sprint-03b-recuperacion-password-mailtrap.md # Flujo de recuperación de credenciales por email
    ├── sprint-04-portal-publico-tracking-cotizador.md # Tracking seguro, agencias y pre-orden web
    ├── sprint-04b-administracion-usuarios-rbac-minimo-privilegio.md # CRUD de personal y control RBAC
    ├── sprint-05-caja-cobros-recepcion-comprobantes.md # Especificación de caja chica y cobranzas
    ├── sprint-05b-consulta-reniec-api-preorden.md   # Consulta de DNI y RUC en pre-ordenes
    └── sprint-06-operativa-core-estados.md          # Flujo operativo de recepción, despacho y arribo
```

---

## 3. Catálogo Rápido de Reglas de Negocio (Business Rules)

Para facilitar la revisión cruzada durante el desarrollo y los code reviews:

| Código | Área | Descripción Resumida | Documento Fuente |
| :--- | :--- | :--- | :--- |
| **`BR-ENV-01`** | Envíos | Pesaje obligatorio en balanza certificada para recepcionar encomiendas. | [03-ciclo-vida-envio-transicion-estados.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/03-ciclo-vida-envio-transicion-estados.md) |
| **`BR-ENV-02`** | Envíos | Prohibido despachar a camión (`en_ruta`) paquetes con pago pendiente en origen. | [03-ciclo-vida-envio-transicion-estados.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/03-ciclo-vida-envio-transicion-estados.md) |
| **`BR-ENV-03`** | Envíos | Secuencialidad obligatoria: no se arriba a destino si no estuvo previamente `en_ruta`. | [03-ciclo-vida-envio-transicion-estados.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/03-ciclo-vida-envio-transicion-estados.md) |
| **`BR-ENV-04`** | Envíos | Entrega de paquete condicionada a pago cancelado y registro de DNI del receptor físico. | [03-ciclo-vida-envio-transicion-estados.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/03-ciclo-vida-envio-transicion-estados.md) |
| **`BR-TAR-01`** | Tarifas | Determinación exclusiva de tarifas en backend: `(L*A*H)/6000`, base S/ 8.00 + S/ 2.50/kg. | [04-motor-tarifario-cubicaje-flete.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/04-motor-tarifario-cubicaje-flete.md) |
| **`BR-TAR-02`** | Tarifas | Cobro obligatorio de reintegro en ventanilla si el peso en balanza supera lo declarado. | [04-motor-tarifario-cubicaje-flete.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/04-motor-tarifario-cubicaje-flete.md) |
| **`BR-CLI-01`** | Clientes | Factura electrónica exige obligatoriamente RUC en estado ACTIVO y HABIDO ante SUNAT. | [05-clientes-identidad-fiscal.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/05-clientes-identidad-fiscal.md) |
| **`BR-CLI-02`** | Clientes | Boletas de venta iguales o mayores a S/ 700.00 exigen DNI y nombre completo por ley. | [05-clientes-identidad-fiscal.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/05-clientes-identidad-fiscal.md) |
| **`BR-CAJ-01`** | Caja | Prohibido cobrar o admitir encomiendas sin una apertura de turno de caja activa. | [06-caja-arqueo-comprobantes.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/06-caja-arqueo-comprobantes.md) |
| **`BR-CAJ-03`** | Caja | Cierre de turno bajo modalidad de arqueo ciego y detección automática de descuadres. | [06-caja-arqueo-comprobantes.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/06-caja-arqueo-comprobantes.md) |
| **`BR-CAN-01`** | Finanzas | Cancelación de encomienda facturada exige obligatoriamente Nota de Crédito Electrónica. | [01-politicas-cancelaciones-reembolsos.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio/01-politicas-cancelaciones-reembolsos.md) |

---

## 4. Estado de los Sprints de Implementación

| Sprint | Hito | Alcance Principal | Estado |
| :--- | :--- | :--- | :---: |
| **Sprint 01** | [Autenticación y MFA](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-01-autenticacion-mfa.md) | Auth Service / JWT / TOTP 2FA / Passlib | ✅ Completado |
| **Sprint 02** | [Rediseño BDD y Auditoría](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-02-rediseño-base-de-datos-auditoria-jwt.md) | PostgreSQL 17 / 3NF / cargaexpress_clean.sql | ✅ Completado |
| **Sprint 03** | [Conexión Auth Frontend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-03-conexion-autenticacion-frontend.md) | React Vite ➔ FastAPI (Login + 2FA + Recuperación) | ✅ Certificado E2E |
| **Sprint 03B**| [Recuperación Password](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-03b-recuperacion-password-mailtrap.md) | Tokens temporales y despacho SMTP Mailtrap | ✅ Certificado E2E |
| **Sprint 04** | [Portal Público y Cotizador](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-04-portal-publico-tracking-cotizador.md) | Agencias / Cotizador / Tracking Seguro PII / Pedidos Web | ✅ Certificado E2E |
| **Sprint 04B**| [Administración RBAC](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-04b-administracion-usuarios-rbac-minimo-privilegio.md) | CRUD Personal / Mínimo Privilegio / NIST Password | ✅ Certificado E2E |
| **Sprint 05** | [Caja, Cobros y Webhook](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-05-caja-cobros-recepcion-comprobantes.md) | Aperturas Caja / Cobro Presencial / Webhooks de Pago | 📋 En Ejecución |
| **Sprint 05B**| [Consulta RENIEC / SUNAT](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-05b-consulta-reniec-api-preorden.md) | API DNI/RUC en tiempo real para pre-registro | ✅ Certificado E2E |
| **Sprint 06** | [Operativa Core y Estados](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-06-operativa-core-estados.md) | Recepción en Balanza / Despacho / Arribo / Entrega | ✅ Completado E2E |

---

## 5. Protocolo de Desarrollo para Nuevos Endpoints (SDD Workflow)

Cada vez que se traslade o cree una funcionalidad en el backend:

1. **Consultar la Regla de Negocio:**
   - Ubicar el identificador `BR-*` correspondiente en [`docs/negocio/`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/negocio).
2. **Consultar el Estándar de Seguridad:**
   - Verificar [01-owasp-top-10-desarrollo.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/01-owasp-top-10-desarrollo.md) y [02-owasp-api-security-top-10.md](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/02-owasp-api-security-top-10.md).
3. **Definir el Contrato en Pydantic (`app/schemas/`):**
   - Tipado estricto, regex de documentos y validaciones de rango numérico.
4. **Implementar en Capa de Servicio (`app/services/`):**
   - Centralizar las validaciones de negocio en el servicio, no en el router.
5. **Completar Checklist:**
   - Validar los criterios en [`checklist-seguridad-migracion.md`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/checklist-seguridad-migracion.md).
