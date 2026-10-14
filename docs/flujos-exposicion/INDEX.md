# 🗺️ Índice General: Guías Técnicas de Flujos para Exposición

Este directorio contiene las especificaciones **prácticas, técnicas y de arquitectura** de cada funcionalidad del sistema **CargaExpress Perú**. Están diseñadas para preparar la sustentación del proyecto, responder preguntas de código, diagramas de conexión, base de datos y auditoría de seguridad.

---

## 🧭 Mapa de Funcionalidades del Sistema

| N° | Funcionalidad | Estado de Documentación | Alcance Técnico Principal |
|:---|:---|:---:|:---|
| **01** | [Inicio de Sesión, JWT, 2FA y Roles (RBAC)](01-inicio-sesion-y-seguridad.md) | ✅ **Listo para Exposición** | Autenticación desacoplada, Bcrypt, PyOTP, JWT dual-scope, control de sesiones y tablas `usuarios` / `auditoria_seguridad`. |
| **02** | **Flujo Integral de Envío Agencia - Agencia** | ⏳ *Siguiente en agenda* | Cotización, pesaje volumétrico, generación de orden, guía de remisión, manifiesto de despacho y arribo a destino. |
| **03** | **Caja y Recepción en Mostrador** | 📝 *Planificado* | Cobros en ventanilla, arqueo ciego, emisión de comprobantes (Boleta/Factura) y control de turnos. |
| **04** | **Almacén: Despacho a Ruta y Arribos** | 📝 *Planificado* | Lectura de bultos por código de barras, consolidación en camión, hoja de ruta y recepción en sede destino. |
| **05** | **Courier y Reparto a Domicilio** | 📝 *Planificado* | Asignación de entregas de última milla, toma de foto de constancia y firma digital del receptor. |
| **06** | **Tracking Público y Consulta de Estados** | 📝 *Planificado* | Consulta abierta por código de seguimiento, línea de tiempo inmutable e integración RENIEC/SUNAT. |

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
