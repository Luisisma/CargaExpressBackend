# 👤 Guía Técnica de Exposición 09: Directorio y Gestión de Clientes

Esta guía explica la arquitectura, el modelo relacional, la búsqueda dinámica y el cálculo de métricas del módulo de **Directorio de Clientes** (`/admin/clientes`) en **CargaExpress Perú**.

---

## 1. Visión General del Negocio

En una empresa de transporte interprovincial y logística express, los clientes intervienen bajo dos roles en cada orden:
* **Remitente:** Quien contrata el servicio y consigna la carga en origen.
* **Destinatario:** Quien recibe la carga en destino.

Para evitar duplicidad de registros y permitir una trazabilidad centralizada de hábitos de consumo, CargaExpress cuenta con un **padrón unificado de clientes**:
1. Un cliente se registra una sola vez en la base de datos (por su DNI o RUC único).
2. El cliente puede figurar como remitente en algunos envíos y como destinatario en otros.
3. El panel administrativo permite buscar clientes y calcular al vuelo su volumen histórico de operaciones.

---

## 2. Diagrama de Conexión de Componentes (Frontend ⇄ Backend ⇄ Base de Datos)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                                   │
│                                                                                        │
│   [Vista Directorio: ClientesList.jsx] ───────► [Servicio: clienteService.js]          │
│   - Buscador por DNI/RUC, Nombre o Email       - GET /api/v1/clientes?busqueda=...     │
│   - Tabla con badge Persona Natural/Jurídica   - Inyección de Token Bearer JWT         │
│   - Contador de Total Envíos por Cliente                                               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP GET (Headers: Authorization Bearer)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                              BACKEND (FastAPI Core)                                    │
│                                                                                        │
│   [Router: endpoints/clientes.py] ◄──────────► [Control de Acceso: deps.py]            │
│   - Endpoint: GET /api/v1/clientes              - require_role(["ADMINISTRADOR",       │
│   - Filtro OR: DNI, RUC, Nombre, Email            "SUPERVISOR", "CAJERO"])             │
│   - Subconsulta SQL: COUNT(Envios)                                                     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
                             ┌────────────────────────────────┐
                             │        TABLA: clientes         │
                             ├────────────────────────────────┤
                             │ id (PK)                        │
                             │ tipo_documento (dni / ruc)     │
                             │ numero_documento (UNIQUE, IDX) │
                             │ nombre_completo, email, teléf. │
                             │ tipo_cliente (natural / juríd) │
                             │ activo (BOOLEAN)               │
                             └──────────────┬─────────────────┘
                                            │
                                            │ 1 : N
                                            ▼
                             ┌────────────────────────────────┐
                             │         TABLA: envios          │
                             ├────────────────────────────────┤
                             │ remitente_id (FK -> clientes)  │
                             │ destinatario_id(FK -> clientes)│
                             └────────────────────────────────┘
```

---

## 3. Estado de Implementación: Lo que SÍ está y lo Pendiente

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         ESTADO TÉCNICO DEL MÓDULO CLIENTES                             │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│  🟢 IMPLEMENTADO Y OPERATIVO           │  🟡 PENDIENTE / EN ROADMAP                    │
├────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Tabla relacional 'clientes' con      │ • Exportación masiva de padrón a Excel / CSV  │
│   índice único en 'numero_documento'   │ • Clasificación VIP / Fidelización según      │
│ • Endpoint protegido 'GET /clientes'   │   monto facturado acumulado                   │
│ • Búsqueda flexible por texto libre    │ • Modal administrativo para modificar correo  │
│ • Cálculo dinámico de 'total_envios'   │   o teléfono de clientes antiguos             │
│ • Clasificación natural vs jurídica    │                                               │
└────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 4. Persistencia en Base de Datos y Consulta de Métricas

### A. Tabla `clientes` ([`app/models/cliente.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/cliente.py))

| Columna | Tipo | Función |
|:---|:---|:---|
| `id` | `INTEGER PRIMARY KEY` | Identificador único del cliente. |
| `tipo_documento` | `VARCHAR(10)` | `'dni'` (8 dígitos) o `'ruc'` (11 dígitos). |
| `numero_documento` | `VARCHAR(20) UNIQUE INDEX` | Clave natural indexada para búsquedas ultra rápidas. |
| `nombre_completo` | `VARCHAR(200)` | Nombres y apellidos oficiales o Razón Social. |
| `email` | `VARCHAR(150)` | Correo electrónico para notificaciones. |
| `telefono` | `VARCHAR(20)` | Celular de contacto para avisos de arribo o entrega. |
| `tipo_cliente` | `VARCHAR(20)` | `'persona_natural'` o `'persona_juridica'`. |
| `activo` | `BOOLEAN` | Estado habilitado en la plataforma. |

---

### B. Cálculo Dinámico de Volumen Operativo (`total_envios`)
En [`app/api/v1/endpoints/clientes.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/clientes.py#L46-L54), el backend no requiere almacenar contadores estáticos desactualizados; calcula en tiempo real el historial acumulado mediante SQLAlchemy:

```python
count_envios = db.scalar(
    select(func.count(Envio.id)).where(
        or_(
            Envio.remitente_id == c.id,
            Envio.destinatario_id == c.id
        )
    )
) or 0
```

Esto consolida tanto las veces que el cliente envió encomiendas como las veces que fue receptor de paquetes en cualquier sede del país.

---

### C. Payloads de Red (API REST)

#### Petición con Búsqueda:
```http
GET /api/v1/clientes?busqueda=47852140 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
```

#### Respuesta Estructurada:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "tipo_documento": "DNI",
      "numero_documento": "47852140",
      "nombre_completo": "Carlos Mendoza Salazar",
      "email": "cmendoza@gmail.com",
      "telefono": "987654321",
      "tipo_cliente": "persona_natural",
      "activo": true,
      "total_envios": 3,
      "creado_en": "2026-10-07T05:10:02Z"
    }
  ]
}
```

---

## 5. Módulos de Código Exactos para Mostrar en la Exposición

### Backend:
1. [app/models/cliente.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/cliente.py):
   * Definición del modelo relacional con índice único en `numero_documento`.
2. [app/api/v1/endpoints/clientes.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/clientes.py):
   * Líneas 16-72: Endpoint `listar_clientes()` con filtros `or_()`, paginación y agregación SQL `func.count(Envio.id)`.

### Frontend:
1. [src/pages/admin/clientes/ClientesList.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/clientes/ClientesList.jsx):
   * Líneas 11-22: Función `cargarClientes()` que consume la API.
   * Líneas 54-135: Formulario de búsqueda rápida, badges de tipo de cliente y renderizado de la tabla con total de envíos.
2. [src/services/clienteService.js](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/clienteService.js):
   * Función `getClientes({ busqueda })`.

---

## 6. Preguntas Frecuentes del Jurado / Evaluador y Respuestas

| Pregunta Típica | Respuesta Técnica y de Base de Datos |
|:---|:---|
| **¿Por qué remitentes y destinatarios comparten la misma tabla `clientes`?** | *"Para evitar redundancia de datos (Tercera Forma Normal - 3NF). Una misma persona o empresa puede enviar encomiendas por la mañana y recibir otra por la tarde. Mantenerlos en una sola tabla permite calcular su volumen total y autocompletar sus datos sin duplicar registros."* |
| **¿Qué ocurre si un cliente cambia de número de teléfono?** | *"Durante el pre-registro de un nuevo envío, si el número de documento ya existe, el sistema recupera al cliente existente y actualiza sus datos de contacto en la tabla `clientes`, manteniendo siempre actualizado el teléfono y correo más reciente."* |
| **¿El endpoint de clientes está protegido o es público?** | *"Está estrictamente protegido por el middleware `require_role(["ADMINISTRADOR", "SUPERVISOR", "CAJERO"])`. A diferencia del tracking público que solo muestra datos anonimizados, el directorio de clientes exige autenticación JWT para proteger la información de contacto de los usuarios."* |
