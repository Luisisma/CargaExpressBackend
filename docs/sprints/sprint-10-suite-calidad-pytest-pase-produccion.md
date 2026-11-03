# Sprint 10: Suite de Calidad, Cobertura Pytest > 75% y Pase a Producción

> **Módulos:**
> 1. Suite de Pruebas Unitarias Automatizadas con `pytest` y `pytest-cov`
> 2. Pruebas de Carga y Concurrencia Masiva (k6 / Locust)
> 3. Matriz de Hardening de Servidor y Certificación OWASP Final
> 4. Contenerización Docker Multi-Stage y Despliegue en VPS Linux  
> **Backend:** [CargaExpressBackend](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend) (FastAPI + Uvicorn + PostgreSQL 17)  
> **QA Framework:** Pytest, HTTPX AsyncClient, Factory Boy, Coverage.py  
> **Estado del Sprint:** 📋 **ESPECIFICADO Y LISTO PARA EJECUCIÓN (SDD)**

---

## 1. Justificación y Objetivos de Negocio

El **Sprint 10** es el cierre de aseguramiento de calidad (**QA**) y preparación de infraestructura para el lanzamiento comercial de CargaExpress Perú:

1. **Blindaje contra Regresiones:** Construir una batería automatizada de más de 80 pruebas unitarias y de integración que verifiquen cada cálculo tarifario, regla de estado, seguridad de contraseñas y validaciones fiscales en menos de 15 segundos.
2. **Resistencia a Picos de Demanda (Cyber Days y Campañas Navideñas):** Certificar mediante pruebas de carga que la plataforma soporte al menos **200 usuarios concurrentes simultáneos** cotizando fletes y consultando tracking sin caídas ni latencias $> 1.5\text{ seg}$.
3. **Hardening y Cero Vulnerabilidades Críticas:** Ejecutar escaneo final SAST/DAST para validar que ningún endpoint exponga stack traces, cabeceras inseguras o fugas de datos.

---

## 2. Alcance de la Suite Automatizada Pytest

Se estructuran pruebas aisladas por dominio con base de datos en memoria / SQLite temporal de pruebas:

| Módulo de Prueba | Archivo de Prueba | Casos Clave a Certificar | Meta Cobertura |
| :--- | :--- | :--- | :---: |
| **Autenticación y 2FA** | `tests/test_auth.py` | Login, bloqueo anti-fuerza bruta (5 intentos), rotación JWT, verificación TOTP y reseteo de claves. | $> 85\%$ |
| **Portal Público y Tracking** | `tests/test_publico.py` | Cotizador server-side, generación criptosegura no correlativa (`CE-YYYY-XXXXXXX`), enmascaramiento PII. | $> 85\%$ |
| **Operativa Core de Envíos** | `tests/test_envios.py` | Recepción en balanza, recálculo por sobrepeso (`BR-TAR-02`), despacho a camión, arribo y entrega con DNI. | $> 80\%$ |
| **Caja y Cobranzas** | `tests/test_caja.py` | Apertura de turno, cobro presencial, arqueo ciego y política de sobrepagos Yape. | $> 80\%$ |
| **Mantenimiento y RBAC** | `tests/test_usuarios.py` | BFLA (API5): Prohibir acceso de cajeros o almaceneros a endpoints de administración de personal. | $> 90\%$ |

---

## 3. Pruebas de Carga y Rendimiento (k6 / Locust)

### Escenario de Estrés:
* **Duración:** 5 minutos.
* **Carga:** Rampa de 10 a 200 usuarios virtuales concurrentes (*VUs*).
* **Endpoints objetivo:**
  * `POST /api/v1/publico/cotizar` (40% de tráfico)
  * `GET /api/v1/publico/tracking/{codigo}` (40% de tráfico)
  * `GET /api/v1/dashboard/resumen` (20% de tráfico autenticado)
* **Criterios de Aprobación (SLA):**
  * Tasa de error $< 0.1\%$.
  * Percentil 95 ($p95$) de tiempo de respuesta $< 800\text{ ms}$.

---

## 4. Checklist Final de Pase a Producción

- [ ] Suite completa de `pytest` ejecutada con éxito y cobertura $\ge 75\%$.
- [ ] Variables de entorno `.env` de producción configuradas con secretos criptográficos de alta entropía.
- [ ] Base de datos PostgreSQL 17 configurada con pool de conexiones optimizado (`pool_size=20, max_overflow=10`).
- [ ] Conexión HTTPS TLS 1.3 con certificados SSL de Let's Encrypt y proxy inverso Nginx con compresión Gzip.
- [ ] Backups automáticos diarios de base de datos configurados con script de rotación.
