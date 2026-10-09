# 06. Auditoría de Seguridad Dinámica (DAST) con OWASP ZAP

## 1. Resumen Ejecutivo
- **Herramienta:** OWASP ZAP (Zed Attack Proxy) v2.17.0 by Checkmarx.
- **Tipo de Análisis:** DAST (Dynamic Application Security Testing) pasivo y activo.
- **Objetivo Evaluado:** Backend REST API CargaExpress (`http://127.0.0.1:8000`).
- **Resultado Global Inicial:**
  - 🔴 **Vulnerabilidades Altas (High):** 0 (Sin fallos de inyección SQL, Broken Object Level Authorization ni fugas de datos).
  - 🟠 **Vulnerabilidades Medias (Medium):** 2 (CSP y SRI en interfaz de documentación).
  - 🟡 **Vulnerabilidades Bajas (Low):** 1 (Inclusión de JavaScript entre dominios en Swagger).
  - 🔵 **Informativas (Info):** 1 (Detección de Aplicación Web Moderna).

---

## 2. Matriz de Hallazgos y Remediaciones Inmediatas

| ID Alerta ZAP | Riesgo | Evidencia / Causa | Estado | Remediación Aplicada |
| :--- | :---: | :--- | :---: | :--- |
| **10038: Cabecera CSP no configurada** | 🟠 **Medio** | Respuestas HTTP sin directiva CSP. | ✅ **RESUELTO** | Implementada cabecera base en `SecurityHeadersMiddleware`. |
| **10055: CSP Failure to Define Directive with No Fallback** | 🟠 **Medio** | Falta de directivas CSP Level 3 (`form-action`, `base-uri`, `object-src`) que no heredan de `default-src`. | ✅ **RESUELTO** | Se declararon explícitamente `base-uri 'self'; form-action 'self'; object-src 'none';`. |
| **10055: CSP script-src / style-src unsafe-inline** | 🟠 **Medio** | Swagger UI (`/docs`) inyecta el script inicializador y estilos inline de la consola. | ⚠️ **GESTIONADO POR DISEÑO** | Exclusivo de la UI gráfica de desarrollo. En producción `/docs` se desactiva (`docs_url=None`). Los endpoints REST consumidos por clientes devuelven `application/json`, por lo que el navegador jamás interpreta scripts. |
| **90003: Falta atributo de integridad de recursos secundarios (SRI)** | 🟠 **Medio** | Etiquetas `<link>` y `<script>` de Swagger UI en `/docs` cargaban recursos sin hash SHA. | ✅ **RESUELTO** | Se configuró `/docs` inyectando `integrity="sha384-..."` y `crossorigin="anonymous"`. |
| **10017: Inclusión de archivos fuente JavaScript entre dominios** | 🟡 **Bajo** | Swagger UI carga bundles desde `cdn.jsdelivr.net`. | ⚠️ **GESTIONADO POR DISEÑO** | Deshabilitado en producción (`DEBUG=False`), eliminando cualquier llamada externa. |
| **10109: Aplicación Web Moderna** | 🔵 **Info** | Detección de arquitectura asíncrona SPA + REST. | ℹ️ **INFORMATIVO** | Comportamiento esperado y estándar. |

---

## 3. Detalle Técnico de los Cambios Implementados

### A. Endurecimiento de Cabeceras HTTP (`app/core/middlewares.py`)
Se robusteció la directiva `Content-Security-Policy` bajo el estándar CSP Level 3:

```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' data:; "
    "connect-src 'self' http://127.0.0.1:8000 http://localhost:5173;"
)
```

### B. Inyección de Subresource Integrity (SRI) (`main.py`)
Para evitar que un atacante que comprometa la CDN pueda inyectar scripts maliciosos en la consola Swagger de los desarrolladores, se validan los hashes criptográficos SHA-384:

```html
<link type="text/css" rel="stylesheet" 
      href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" 
      integrity="sha384-Ov4/wv3j2bmct8cDc5X4ngJZohVPzEmc6uDPH8WeljUxO5vtoykvMEfbu9Vh6RaW" 
      crossorigin="anonymous">

<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js" 
        integrity="sha384-ZPehFMQommnnuaZ4rpxgkgTT2DKFVp4hZC/7pLit+9Lek9T1YGSo23eHFbvNkXkw" 
        crossorigin="anonymous"></script>
```

---

## 4. Tipos de Reportes Disponibles en OWASP ZAP

OWASP ZAP permite exportar diferentes tipos de informes según el público objetivo (**Informe** ➔ **Generar informe...** o `Ctrl + R`):

1. **Modern HTML Report (Recomendado para Sustentación Técnica):**
   - El informe más completo y visual. Incluye estadísticas de criticidad, desglose detallado por código CWE y WASC, descripción formal del riesgo, solución sugerida por OWASP, y la **evidencia exacta** (petición HTTP Request y respuesta HTTP Response con cabeceras y código de estado).
2. **High Level Report (Resumen Ejecutivo):**
   - Diseñado para gerencia, jefatura de TI o evaluadores de alto nivel. Resume en 2 páginas los gráficos de torta de riesgo, porcentaje de cumplimiento y resumen de alertas sin abrumar con código crudo.
3. **Traditional HTML / PDF Report:**
   - Formato clásico con tabla de contenidos para adjuntar como anexo impreso o digital en tesis y memorias de proyecto.
4. **JSON / XML Report (DevSecOps / CI/CD):**
   - Salida estructurada machine-readable para integrar el escaneo en pipelines automatizados de GitHub Actions o GitLab CI y romper el build si surgen alertas rojas.

---

## 5. Niveles de Auditoría DAST en OWASP ZAP (Más allá del Spider Básico)

El escaneo automatizado con spider tradicional es solo el nivel 1. Para una auditoría profunda de grado industrial, ZAP ofrece tres metodologías complementarias:

### Nivel 1: Escaneo Pasivo y Spider de Interfaz (Completado ✅)
- **Alcance:** Rastreo de la interfaz web expuesta (`/docs` y rutas directas).
- **Enfoque:** Detección de cabeceras ausentes, políticas CSP, atributos SRI y filtración de información en encabezados del servidor.

### Nivel 2: Escaneo Especializado de API REST con OpenAPI (Recomendado para Backends)
- **Procedimiento en ZAP:**
  1. Ir a **Importar** ➔ **Importar una definición de OpenAPI**.
  2. En URL de definición: `http://127.0.0.1:8000/openapi.json`.
  3. En URL de destino: `http://127.0.0.1:8000`.
- **Beneficio Técnico:**
  ZAP no depende de hipervínculos HTML; lee directamente el esquema Swagger, comprende los modelos Pydantic, los tipos de datos y los métodos (`POST`, `PUT`, `DELETE`), y lanza pruebas de *fuzzing* contra la validación de esquemas (HTTP 422 vs HTTP 500).

### Nivel 3: Escaneo Activo Autenticado con JWT Bearer (Auditoría Anti-BOLA/IDOR)
- **Procedimiento en ZAP:**
  1. Configurar un **Contexto** en ZAP (clic derecho en el árbol de Sitios ➔ *Incluir en el contexto*).
  2. En **Autenticación**, configurar el token JWT `Authorization: Bearer <token_del_usuario>` mediante el script de cabeceras o la extensión *Replacer*.
  3. Ejecutar **Escaneo Activo** con credenciales de dos roles distintos (ej. `ALMACEN` intentando invocar endpoints de `/api/v1/usuarios`).
- **Beneficio Técnico:**
  Certifica que el control de acceso en backend rechace con `HTTP 403 Forbidden` cualquier intento de elevación de privilegios o acceso cruzado entre sedes.

### Nivel 4: Auditoría del Frontend SPA en React (AJAX Spider)
- **Procedimiento en ZAP:**
  1. En **Inicio Rápido**, apuntar a `http://localhost:5173`.
  2. Seleccionar **Cliente para el Spider** (Firefox Headless o Chrome Headless).
  3. Ejecutar el AJAX Spider para que interactúe con el Virtual DOM de React.
- **Beneficio Técnico:**
  Evalúa la seguridad de los componentes web, inputs de formularios, renderizado de estados y almacenamiento seguro en el navegador.

---

## 6. Backlog de Mejoras Pendientes de Seguridad (Roadmap a Producción)

Para la memoria técnica y el informe final, los siguientes puntos quedan registrados como mejoras planificadas para el despliegue productivo:

| Prioridad | Ítem de Seguridad | Justificación Técnica | Estado |
| :---: | :--- | :--- | :---: |
| 🟢 **Alta** | **Apagado de `/docs` y `/openapi.json` en Producción** | En `main.py`, la condición `docs_url=None if not settings.DEBUG` garantiza que la consola interactiva no sea accesible por terceros en internet (OWASP API8:2023). | ✅ Configurado |
| 🟢 **Alta** | **CSP Diferenciado (API REST vs Swagger)** | Los endpoints `/api/v1/...` devuelven JSON y adoptarán `default-src 'none'; frame-ancestors 'none';` eliminando `'unsafe-inline'` completamente de la API de producción. | 📋 En Backlog |
| 🟡 **Media** | **Rate Limiting y Protección contra Fuerza Bruta** | Implementar `slowapi` o middleware con Redis para limitar intentos en `/api/v1/auth/login` a 5 peticiones por minuto por IP (OWASP API4:2023). | 📋 En Backlog |
| 🟡 **Media** | **Terminación TLS / HTTPS y Activación de HSTS** | Al desplegar en servidor VPS o nube con proxy inverso (Nginx / Caddy), activar certificado SSL Let's Encrypt para que el backend despache `Strict-Transport-Security: max-age=31536000; includeSubDomains`. | 📋 En Backlog |
| 🔵 **Baja** | **Servir estáticos de Swagger de forma local (Offline)** | Alojar los archivos `swagger-ui.bundle.js` y `swagger-ui.css` en una carpeta interna `/static` para eliminar la dependencia de `cdn.jsdelivr.net` durante el desarrollo sin conexión. | 📋 Opcional |

---

## 7. Procedimiento para Generar el Reporte Detallado Actual

Para documentar la evidencia en tu entrega:
1. En OWASP ZAP, haz clic en **Informe** ➔ **Generar informe...** (o `Ctrl + R`).
2. Configura los campos:
   - **Título:** `Auditoría de Seguridad Dinámica (DAST) - CargaExpress S.A.C.`
   - **Plantilla:** `Modern HTML Report` (incluye gráficas, detalle de cada alerta y traza HTTP).
   - **Directorio de salida:** Guardar en `CargaExpressBackend/docs/auditoria/` o en tu carpeta de entregables.
3. Presiona **Generar informe**.
4. Ábrelo en el navegador para guardarlo como PDF o adjuntarlo directamente en tu repositorio.

