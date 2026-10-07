# Guía de Inicio Rápido - CargaExpress Backend

Esta guía detalla los pasos para configurar, levantar y probar el servidor FastAPI de **CargaExpress Perú** en tu entorno local con Windows.

---

## 1. Requisitos Previos

* **Python:** 3.10 o superior (verificado con Python 3.14).
* **Base de Datos:** PostgreSQL 17 en ejecución (con la base de datos `cargaexpress` restaurada de `cargaexpress.sql`).
* **Terminal:** PowerShell o CMD en Windows.

---

## 2. Pasos para Levantar el Servidor

### Paso 1: Abrir la terminal en la carpeta del backend
```powershell
cd c:\Users\User\Documents\VSC-Integrador\CargaExpressBackend
```

### Paso 2: Activar el entorno virtual (`.venv`)
* **En PowerShell:**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(Si PowerShell muestra error de permisos de ejecución de scripts, ejecuta una sola vez: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

* **En CMD (Símbolo del sistema):**
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

*(Sabrás que está activo cuando veas `(.venv)` al inicio de la línea de comandos).*

---

### Paso 3: Verificar las Variables de Entorno (`.env`)
El archivo `.env` ya se encuentra configurado en la raíz. Asegúrate de que las credenciales de PostgreSQL coincidan con tu servidor local:

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/cargaexpress
SECRET_KEY=ce_dev_secret_key_9f8b2c1a4e6d3f5a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
ENVIRONMENT=development
DEBUG=True
```

---

### Paso 4: (Opcional) Aplicar las mejoras de auditoría en PostgreSQL
Si deseas aplicar las nuevas tablas de auditoría y campos de seguridad en tu PostgreSQL local:

```powershell
psql -U postgres -d cargaexpress -f migrations\001_seguridad_y_auditoria.sql
```

---

### Paso 5: Ejecutar el Servidor FastAPI

Puedes levantarlo de cualquiera de estas dos formas:

#### Opción A: Usando el script principal (Recomendado)
```powershell
python main.py
```

#### Opción B: Usando Uvicorn CLI con recarga automática (*Hot Reload*)
```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verás una salida similar a:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process using WatchFiles
INFO:     Application startup complete.
```

---

## 3. Enlaces y Documentación Interactiva

Una vez levantado el servidor, abre tu navegador en los siguientes enlaces:

| Recurso | URL | Descripción |
| :--- | :--- | :--- |
| **Documentación Swagger UI** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interfaz gráfica interactiva para probar cada endpoint con el botón *Try it out*. |
| **Documentación ReDoc** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Especificación OpenAPI estructurada para revisión técnica. |
| **Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Verificación rápida del estado del microservicio. |

---

## 4. Ejemplos de Prueba Rápida de Endpoints

### 1. Comprobar Salud del Servicio
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "CargaExpress API",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### 2. Iniciar Sesión (Paso 1: `/api/v1/auth/login`)
```powershell
$body = @{
    identificador = "admin@cargaexpress.pe"
    password = "TuPassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $body
```

* Si el usuario tiene **2FA activo**, devolverá `mfa_requerido: true` y un `temp_token` (vida útil: 5 minutos).
* Si el usuario no tiene 2FA activo, devolverá directamente `access_token` y `refresh_token`.

---

### 3. Verificar Código TOTP (Paso 2: `/api/v1/auth/2fa`)
```powershell
$body2fa = @{
    temp_token = "EL_TEMP_TOKEN_OBTENIDO"
    codigo_totp = "123456"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/2fa" -Method Post -ContentType "application/json" -Body $body2fa
```

---

### 4. Consultar Perfil Autenticado (`/api/v1/auth/me`)
```powershell
$headers = @{
    Authorization = "Bearer EL_ACCESS_TOKEN_AQUI"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/me" -Method Get -Headers $headers
```

---

## 5. Ejecutar la Suite de Pruebas Automatizadas

Para validar que todos los flujos de seguridad, 2FA, bloqueo anti-fuerza bruta y headers funcionen al 100%:

```powershell
pytest -v
```

**Resultado esperado:**
```text
====================== 10 passed in 12.77s ======================
```
