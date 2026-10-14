# 🏢 Guía Técnica de Exposición 08: Sedes y Agencias Provinciales

Esta guía explica la arquitectura, el modelo de datos, la integridad referencial y el consumo del catálogo de **Sedes y Agencias Provinciales** en **CargaExpress Perú**.

---

## 1. Visión General del Negocio

El modelo de transporte de encomiendas de CargaExpress opera bajo una topología de **red de agencias físicas distribuidas a nivel nacional**.

Cada agencia:
1. Actúa como **nodo logístico de origen o destino** para la admisión, despacho, recepción y entrega de paquetes.
2. Es la **sede de adscripción del personal operativo**: los cajeros atienden en una ventanilla de una agencia específica (`agencia_id`) y los almaceneros gestionan la bodega local.
3. Cuenta con un **código oficial único** de 4 dígitos (ej. `1001`, `1002`, `1010`) que viaja en las guías y rotulados.

---

## 2. Diagrama de Conexión de Componentes

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                                   │
│                                                                                        │
│   [Directorio Admin: AgenciasList.jsx]      [Selectores en RegistrarPedido/Cotizador] │
│                    │                                           │                       │
│                    ▼                                           ▼                       │
│             [publicService.getAgencias()] ◄────────────────────┘                       │
└────────────────────┬───────────────────────────────────────────────────────────────────┘
                     │ HTTP GET /api/v1/publico/agencias
┌────────────────────▼───────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI Core)                                    │
│                                                                                        │
│   [Router: publico.py] ────────► [Service: publico_service.py]                        │
│                                            │                                           │
│                                            ▼                                           │
│                             [SQLAlchemy ORM: models/agencia.py]                        │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
                                             ▼
                             ┌────────────────────────────────┐
                             │       TABLA: agencias          │
                             ├────────────────────────────────┤
                             │ id (PK)                        │
                             │ codigo_agencia (UNIQUE)        │
                             │ nombre, direccion              │
                             │ departamento, provincia, dist. │
                             │ estado ('habilitado')          │
                             └───────┬────────────────┬───────┘
                                     │                │
            ┌────────────────────────┘                └────────────────────────┐
            │ 1 : N                                                            │ 1 : N
            ▼                                                                  ▼
┌────────────────────────┐                                            ┌────────────────────────┐
│     TABLA: envios      │                                            │    TABLA: usuarios     │
├────────────────────────┤                                            ├────────────────────────┤
│ agencia_origen_id (FK) │                                            │ agencia_id (FK)        │
│ agencia_destino_id(FK) │                                            │ Personal asignado a    │
│ Rutas de transporte    │                                            │ cada sede física       │
└────────────────────────┘                                            └────────────────────────┘
```

---

## 3. Estado de Implementación: Lo que SÍ está y lo Pendiente

Para sustentar con total transparencia técnica:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         ESTADO TÉCNICO DEL MÓDULO AGENCIAS                             │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│  🟢 IMPLEMENTADO Y OPERATIVO           │  🟡 PENDIENTE / EN ROADMAP                    │
├────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Modelo relacional 3NF 'agencias'     │ • Formulario interactivo en Frontend para que │
│ • Restricción de clave foránea en DB   │   el Admin cree/edite agencias desde la web   │
│   (envios.origen_id y destino_id)      │ • Endpoint administrativo POST/PUT de sedes   │
│ • Endpoint 'GET /publico/agencias'     │ • Georreferenciación con coordenadas lat/long │
│ • Directorio visual en AgenciasList    │                                               │
│ • Sedes oficiales sembradas en DB      │                                               │
└────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 4. Persistencia en Base de Datos: Red Nacional de Agencias

En la base de datos relacional ([`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db)), la tabla `agencias` almacena las sedes activas:

### Registros Actuales en la Base de Datos:
1. **Sede Central Lima:**
   * `id`: `1` | `codigo_agencia`: `1001`
   * `nombre`: `"AGENCIA LIMA - LIMA CENTRAL"`
   * `departamento`: `"Lima"` | `provincia`: `"Lima"` | `distrito`: `"Lima"`
   * `direccion`: `"Av. Nicolás de Piérola 1220, Lima"`
2. **Sede Sur Arequipa:**
   * `id`: `2` | `codigo_agencia`: `1002`
   * `nombre`: `"AGENCIA AREQUIPA - AREQUIPA"`
   * `departamento`: `"Arequipa"` | `provincia`: `"Arequipa"` | `distrito`: `"Arequipa"`
   * `direccion`: `"Calle Mercaderes 314, Arequipa"`
3. **Sede Imperial Cusco:**
   * `id`: `10` | `codigo_agencia`: `1010`
   * `nombre`: `"AGENCIA CUSCO - CUSCO"`
   * `departamento`: `"Cusco"` | `provincia`: `"Cusco"` | `distrito`: `"Cusco"`
   * `direccion`: `"Calle Matará 241, Cusco"`

---

## 5. Integridad Referencial y Reglas de Negocio

### A. Regla de Enrutamiento (`BR-ENV-01`):
* Un envío **no puede** tener la misma agencia como origen y destino simultáneamente:
  $$\text{agencia\_origen\_id} \neq \text{agencia\_destino\_id}$$
* Esta validación se ejecuta tanto en el frontend ([`RegistrarPedido.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/public/RegistrarPedido.jsx)) como en el backend ([`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py)).

### B. Adscripción de Personal por Sede:
* Al registrar un colaborador en [UsuariosList.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/usuarios/UsuariosList.jsx), el sistema exige seleccionar la agencia donde trabajará.
* Esto permite filtrar los reportes de cierre de caja y los despachos de almacén según la sede física del usuario autenticado.

---

## 6. Módulos de Código Exactos para Mostrar en la Exposición

### Backend:
1. [app/models/agencia.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/models/agencia.py):
   * Modelo SQLAlchemy `Agencia` con campos de ubicación geográfica (departamento, provincia, distrito, dirección) y `codigo_agencia` único.
2. [app/api/v1/endpoints/publico.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py):
   * Línea 24: Endpoint `GET /agencias` que expone la lista de sedes operativas.
3. [app/services/publico_service.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py):
   * Línea 30: Método `listar_agencias_activas()` que consulta `Agencia.estado == 'habilitado'`.

### Frontend:
1. [src/pages/admin/agencias/AgenciasList.jsx](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/pages/admin/agencias/AgenciasList.jsx):
   * Vista de catálogo con buscador en vivo por departamento, provincia y dirección.
   * Renderizado de tarjetas con códigos de agencia, badges de estado y botones de geolocalización.
2. [src/services/publicService.js](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/services/publicService.js):
   * Método `getAgencias()` consumido por los módulos de cotización, admisión y despacho.

---

## 7. Preguntas Frecuentes del Jurado / Evaluador y Respuestas

| Pregunta Típica | Respuesta Técnica |
|:---|:---|
| **¿Por qué las agencias tienen un `codigo_agencia` numérico además de un `id`?** | *"El `id` es la clave primaria interna autonumérica para optimización de índices en el motor relacional. El `codigo_agencia` (1001, 1002, 1010) es el identificador de negocio visible en los rótulos de carga y manifiestos de transporte conforme a la nomenclatura logística provincial."* |
| **¿Cómo se expande la red a nuevas provincias?** | *"Actualmente la base de datos cuenta con las sedes troncales (Lima, Arequipa, Cusco). El modelo está totalmente normalizado para admitir nuevas sedes mediante el script de migraciones/seed o insertando en la tabla `agencias`. El formulario interactivo de creación web está planificado para el siguiente sprint administrativo."* |
| **¿Qué ocurre si se elimina una agencia de la base de datos?** | *"Las claves foráneas en `envios` y `usuarios` protegen la integridad referencial (`RESTRICT` / `NO ACTION`), impidiendo borrar una agencia que tenga histórico de encomiendas o personal vinculado. Solo se puede cambiar su estado a inactivo (`estado = 'deshabilitado'`)."* |
