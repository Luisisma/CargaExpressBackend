# CargaExpress Backend - API RESTful Segura

Backend independiente para **CargaExpress Perú**, desarrollado con **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2** y conectado a la base de datos **PostgreSQL 17**, diseñado bajo la metodología **Spec-Driven Development (SDD)** y los estándares de seguridad **OWASP Top 10 (2021)** y **OWASP API Security Top 10 (2023)**.

---

## Enlaces Rápidos

* **[Guía de Inicio Rápido (Levantar Servidor)](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/INICIO_RAPIDO.md)**: Comandos para activar el `.venv`, ejecutar Uvicorn y probar los endpoints.
* **[Metodología Spec-Driven Development (SDD)](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/README.md)**: Manifiesto y protocolo de migración por endpoint.
* **[Checklist de Migración y Matriz de Endpoints](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/checklist-seguridad-migracion.md)**: Bitácora de seguimiento por sprint.
* **[Especificación Sprint 1: Autenticación 2FA y Auditoría](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/sprints/sprint-01-autenticacion-mfa.md)**: Flujos, contratos y esquemas del primer módulo.
* **[Guías Técnicas de Seguridad OWASP](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad)**:
  - [OWASP Top 10 Desarrollo Web](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/01-owasp-top-10-desarrollo.md)
  - [OWASP API Security Top 10](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/02-owasp-api-security-top-10.md)
  - [Parámetros de Endurecimiento y SAST/DAST](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/03-parametros-backend-seguro.md)
  - [Auditoría y Mejoras en Base de Datos](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/docs/seguridad/04-auditoria-y-base-de-datos.md)

---

## Comandos Esenciales

```powershell
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Levantar el servidor en desarrollo
python main.py
# O con Uvicorn directo:
uvicorn main:app --reload --port 8000

# 3. Ejecutar pruebas automatizadas
pytest -v
```

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
