# Parámetros y Estándares Técnicos para un Backend Seguro

Este documento detalla los parámetros de configuración, defensas de red, cabeceras HTTP, sanitización de datos y directrices para que el backend **CargaExpress** apruebe con éxito las evaluaciones de **software de seguridad automatizado (SAST y DAST)** como SonarQube, OWASP ZAP, Bandit y Semgrep.

---

## 1. Encabezados HTTP de Seguridad (Security Headers)

El servidor FastAPI debe retornar en **todas** las respuestas HTTP cabeceras que mitiguen ataques del lado del cliente, sniffing de MIME y clickjacking. Se implementará mediante un middleware global:

```python
# app/core/middlewares.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Prevenir que el navegador interprete archivos con tipos MIME diferentes al declarado
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevenir ataques de Clickjacking impidiendo que la API sea embebida en iframes
        response.headers["X-Frame-Options"] = "DENY"
        
        # Filtro XSS heredado para navegadores antiguos
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Limitar el envío del encabezado Referer para proteger rutas con identificadores
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Desactivar APIs invasivas del navegador (geolocalización, cámara, micrófono)
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Forzar HTTPS estricto durante 1 año en entornos de producción
        if not request.url.is_secure and request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            
        return response
```

---

## 2. Validación Estricta y Sanitización de Entradas (Pydantic v2)

Para evitar inyecciones, desbordamientos de buffer o inconsistencias lógicas en el negocio logístico peruano, todos los DTOs de entrada deben aplicar expresiones regulares (*regex*) y límites estrictos:

```python
# app/schemas/common.py y app/schemas/cliente.py
from pydantic import BaseModel, Field, field_validator
import re

class DocumentoIdentidadMixin(BaseModel):
    tipo_documento: str = Field(..., pattern=r"^(DNI|RUC|CE)$")
    numero_documento: str

    @field_validator("numero_documento")
    @classmethod
    def validar_documento(cls, valor: str, info):
        tipo = info.data.get("tipo_documento")
        valor = valor.strip()
        
        if tipo == "DNI" and not re.fullmatch(r"^\d{8}$", valor):
            raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        if tipo == "RUC" and not re.fullmatch(r"^\d{11}$", valor):
            raise ValueError("El RUC debe contener exactamente 11 dígitos numéricos.")
        if tipo == "CE" and not re.fullmatch(r"^[A-Za-z0-9]{8,12}$", valor):
            raise ValueError("El Carné de Extranjería debe tener entre 8 y 12 caracteres alfanuméricos.")
            
        return valor

class TelefonoPeruanoField(BaseModel):
    telefono: str = Field(
        ...,
        pattern=r"^9\d{8}$",
        description="Número de celular peruano de 9 dígitos comenzando con 9"
    )
```

### Reglas de Sanitización de Texto:
- Eliminar espacios redundantes antes y después de cadenas (`str_strip_whitespace=True`).
- Para campos de observaciones o descripción de mercadería, sanitizar caracteres especiales HTML (`<`, `>`, `"`, `'`) o validar longitud máxima estricta (`max_length=255`) para prevenir inyecciones indirectas.

---

## 3. Manejo de Secretos y Variables de Entorno

### Políticas de Cero Secretos en Código
1. **Archivo `.env` excluido:** El archivo `.env` está registrado en `.gitignore` y **nunca** debe ser subido al repositorio Git.
2. **Plantilla `.env.example` limpia:** Solo se sube `.env.example` con valores ficticios y descriptivos:
   ```bash
   PROJECT_NAME="CargaExpress API"
   ENVIRONMENT="development"
   DEBUG=False
   SECRET_KEY="generar-clave-segura-minimo-64-caracteres-con-openssl-rand-hex-32"
   DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/cargaexpress"
   CORS_ORIGINS=["http://localhost:5173"]
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```
3. **Generación de Claves Criptográficas:**
   Para producción, las claves secretas deben generarse mediante entropía criptográfica:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

---

## 4. Respuestas Normalizadas y Formato de Errores (Envelope Pattern)

Para facilitar la interoperabilidad con [CargaExpressFront](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront) y evitar fugas de información interna en auditorías DAST:

### Respuesta Exitosa (`200 OK`, `201 Created`):
```json
{
  "success": true,
  "data": {
    "id": 105,
    "codigo_seguimiento": "CE-2026-00105",
    "estado": "REGISTRADO",
    "precio_flete": 45.50
  },
  "message": "Envío registrado correctamente."
}
```

### Respuesta de Error (`400`, `401`, `403`, `404`, `422`, `500`):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no cumplen con el formato requerido.",
    "details": [
      {
        "field": "destinatario_telefono",
        "issue": "El número de celular debe comenzar con 9 y contener 9 dígitos."
      }
    ]
  }
}
```

> **Aviso de Seguridad:** En caso de errores `500 Internal Server Error`, el mensaje retornado debe ser genérico: `"Ocurrió un error inesperado al procesar la solicitud. Contacte al administrador con el ID de referencia."`. La traza interna de la excepción se envía exclusivamente a los logs protegidos del servidor con un `request_id` único.

---

## 5. Auditoría y Trazabilidad (Security Logging & Correlation ID)

Cada petición entrante debe asociarse a un identificador único de trazabilidad (`X-Request-ID`):
1. Si el cliente envía `X-Request-ID`, el backend lo valida y preserva. Si no lo envía, el backend genera un UUIDv4 nuevo.
2. Dicho ID se inyecta en la respuesta HTTP (`response.headers["X-Request-ID"]`) y acompaña a cada línea de log.
3. **Estructura del Log JSON de Seguridad:**
   ```json
   {
     "timestamp": "2026-10-01T20:55:00.123Z",
     "level": "WARNING",
     "request_id": "c1f7a83d-6b58-45a1-bf8a-e478546b9a89",
     "event": "FAILED_LOGIN_ATTEMPT",
     "client_ip": "192.168.1.50",
     "usuario_intentado": "operador_surquillo",
     "user_agent": "Mozilla/5.0 ...",
     "endpoint": "/api/v1/auth/login"
   }
   ```

---

## 6. Verificación de Seguridad Automatizada (SAST & DAST)

El software será sometido a análisis de seguridad antes de su puesta en producción. Cada desarrollador debe ejecutar localmente las siguientes herramientas:

### 1. Análisis Estático de Código (SAST)
```bash
# Análisis de vulnerabilidades y malas prácticas en código Python
pip install bandit
bandit -r app/ -ll -ii

# Análisis de vulnerabilidades en dependencias instaladas
pip install pip-audit
pip-audit
```

### 2. Detección de Fuga de Secretos
```bash
# Verificar que no existan credenciales quemadas en el código
pip install detect-secrets
detect-secrets scan --all-files
```

### 3. Preparación para Escáner Dinámico (DAST - OWASP ZAP / SonarQube)
- Todos los formularios y endpoints tipo POST deben exigir cabecera `Content-Type: application/json`.
- Rechazar peticiones con verbos no permitidos con código `405 Method Not Allowed`.
- Asegurar que no existan puertos de depuración expuestos (`--reload` desactivado en producción).
- Comprobar que los cookies de sesión (si se usan para refresh tokens) contengan los flags:
  `HttpOnly; Secure; SameSite=Strict`.
