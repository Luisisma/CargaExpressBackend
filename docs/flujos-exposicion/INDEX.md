# 🗺️ Índice General: Guías Técnicas de Flujos para Exposición

Este directorio contiene las especificaciones **prácticas, técnicas y de arquitectura** de cada funcionalidad del sistema **CargaExpress Perú**. Están diseñadas para preparar la sustentación del proyecto, responder preguntas de código, diagramas de conexión, base de datos y auditoría de seguridad.

---

## 🧭 Mapa de Funcionalidades del Sistema

| N° | Funcionalidad | Estado de Documentación | Alcance Técnico Principal |
|:---|:---|:---:|:---|
| **01** | [Inicio de Sesión, JWT, 2FA y Roles (RBAC)](01-inicio-sesion-y-seguridad.md) | ✅ **Listo para Exposición** | Autenticación desacoplada, Bcrypt, PyOTP, JWT dual-scope, control de sesiones y tablas `usuarios` / `auditoria_seguridad`. |
| **02** | [Flujo Integral de Envío Agencia a Agencia](02-flujo-envio-agencia-agencia.md) | ✅ **Listo para Exposición** | Cadena de custodia (5 actores), máquina de estados, cubicaje IATA (L*A*H)/6000, tablas `envios` y `historial_envios`. |
| **03** | [Caja, Recepción en Mostrador y Arqueo Ciego](03-caja-recepcion-y-mostrador.md) | ✅ **Listo para Exposición** | Cobros en ventanilla, balanza digital, recálculo de sobrepeso, arqueo ciego, desglose IGV 18% SUNAT y comprobantes. |
| **04** | [Almacén: Despacho a Ruta y Arribos](04-almacen-despacho-y-arribos.md) | ✅ **Listo para Exposición** | Lectura con pistola láser continua, estiba en camión, precondiciones de estado y recepción en bodega destino. |
| **05** | [Courier y Reparto a Domicilio (Última Milla)](05-courier-y-reparto-domicilio.md) | ✅ **Listo para Exposición** | Estado real del módulo: esquema DB, recargos de delivery (+S/ 12.00), rol RBAC y delimitación de pendientes (fotos/firma). |
| **06** | [Tracking Público y Consulta RENIEC / SUNAT](06-tracking-publico-y-consultas.md) | ✅ **Listo para Exposición** | Consulta abierta por código de seguimiento, línea de tiempo inmutable, enmascaramiento PII y búsqueda híbrida fiscal. |
| **07** | [Gestión de Personal y Usuarios (Admin)](07-gestion-usuarios-y-personal.md) | ✅ **Listo para Exposición** | Alta de colaboradores, asignación de roles/agencias, reseteo de claves, toggle 2FA y revocación `sesion_version`. |
| **08** | [Gestión de Sedes y Agencias Provinciales](08-gestion-sedes-y-agencias.md) | ✅ **Listo para Exposición** | Catálogo de sucursales (Lima 1001, Arequipa 1002, Cusco 1010), ubigeo departamental e integridad referencial FK. |
| **09** | [Directorio y Gestión de Clientes](09-directorio-gestion-clientes.md) | ✅ **Listo para Exposición** | Padrón unificado de clientes (3NF), cálculo dinámico de volumen de envíos y búsqueda indexada por DNI/RUC. |
| **10** | [Dashboard Gerencial, KPIs y Métricas](10-dashboard-gerencial-kpis.md) | ✅ **Listo para Exposición** | Agregaciones SQL (`COUNT`, `SUM`), facturación en tiempo real, KPIs del turno y encomiendas recientes. |
| **11** | [Recuperación de Contraseñas por Email](11-recuperacion-password-email.md) | ✅ **Listo para Exposición** | Tokens de 15 min (scope `password_reset`), integración Mailtrap API, anti-enumeración y revocación `sesion_version`. |

---

## 🎯 Estructura Estándar de cada Guía de Exposición

Cada documento de este repositorio sigue una estructura estricta orientada a defensa de tesis o evaluación técnica de software:

1. **Visión General y Propósito del Módulo.**
2. **Diagrama de Conexión de Componentes (Frontend ⇄ Backend ⇄ Base de Datos).**
3. **¿Cómo se construyó? (Arquitectura Limpia y Desacoplamiento).**
4. **Persistencia en Base de Datos (Tablas, Campos Críticos y Transacciones).**
5. **Criptografía y Seguridad Real (Hashing vs Cifrado, Tokens, Anti-Brute-Force).**
6. **Módulos de Código Exactos a Revisar (Guía rápida para responder mirando el código).**
7. **Preguntas Típicas del Jurado / Evaluador y Cómo Responderlas.**
