# Sprint 05B: Integración de Consulta Oficial RENIEC/SUNAT en Pre-Órdenes y Gestión de Usuarios

## 📋 Resumen Ejecutivo
En este sprint se extrajo, modernizó y potenció la capacidad de consulta de identidad del proyecto heredado (`cargaexpress-\app/modules/api/services.py`) para integrarla en la arquitectura moderna de **FastAPI** (`CargaExpressBackend`) y **React Vite** (`CargaExpressFront`).

El sistema ahora cuenta con un **mecanismo de búsqueda híbrida en 2 niveles**:
1. **Nivel 1 (Base de Datos Local CargaExpress):** Verifica si el documento ya pertenece a un cliente frecuente o recurrente.
2. **Nivel 2 (API Oficial RENIEC / SUNAT):** Si el cliente no existe en la base de datos local, consulta en tiempo real mediante API ciudadana pública obteniendo los nombres y apellidos exactos del portador/titular de forma oficial.

---

## 🏗️ Arquitectura y Componentes Implementados

### 1. Backend: Servicio Resiliente de Consulta de Identidad
- **Archivo:** `app/services/consulta_documento_service.py`
- **Tecnología:** Cliente HTTP con `httpx` (para API REST RENIEC) y `requests` con headers emulados de navegador (para bypass del WAF de SUNAT), timeout de 8.0 segundos y parser HTML tolerante a fallos.
- **Endpoints externos soportados:**
  - **DNI (8 dígitos):** `http://martinnauca.com/api/reniec/dni/{dni}`. Retorna `nombres`, `apellido_paterno`, `apellido_materno`, formateando el `nombre_completo` exacto (`fuente: "reniec"`).
  - **RUC (11 dígitos):** `https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias`. Parsea en tiempo real la respuesta oficial de SUNAT recuperando la Razón Social, Nombre Comercial, Estado Contribuyente (ACTIVO) y Condición (HABIDO) (`fuente: "sunat"`). Si SUNAT no responde, degrada a digitación manual.

### 2. Capa de Servicios Públicos y Esquemas Pydantic
- **Archivos:**
  - `app/schemas/publico.py`: Esquema `ClientePublicoResponse` con `fuente` (`"local"`, `"reniec"`, `"sunat"` o `"manual"`), `tipo_cliente` (`"persona_natural"` o `"empresa"`) y `mensaje`.
  - `app/services/publico_service.py`: Método `buscar_cliente()` con resolución jerárquica: BD Local ➔ RENIEC / SUNAT ➔ Modo Manual.

---

## 💻 Integración en el Frontend (React Vite)

### 1. Formulario de Pre-Orden de Envíos (`/registrar-pedido`)
- **Archivo:** `src/pages/public/RegistrarPedido.jsx`
- **Comportamiento:**
  - Al ingresar el DNI del remitente o destinatario (8 dígitos) y presionar **"Buscar"**, el sistema consulta a RENIEC en tiempo real.
  - Autocompleta automáticamente el campo **"Nombre completo o Razón Social \*"** con el nombre del portador.
  - Muestra un badge visual de confirmación:
    `✓ RENIEC: Portador verificado (NOMBRE COMPLETO)`
  - Si la API no responde o el documento no existe, habilita inmediatamente el modo de ingreso manual sin frustrar la experiencia de usuario.

### 2. Alta de Colaboradores en Panel Administrativo (`/admin/usuarios`)
- **Archivo:** `src/pages/admin/usuarios/UsuariosList.jsx`
- **Comportamiento:**
  - En el modal de creación de nuevos colaboradores, se incorporó el botón **RENIEC** junto al campo DNI.
  - Al hacer clic, consulta la identidad oficial, descompone nombres y apellidos, y los autocompleta automáticamente en los inputs correspondientes.

---

## 🧪 Pruebas Realizadas y Resultados

| Prueba | Entrada | Resultado Esperado | Resultado Obtenido | Estado |
| :--- | :--- | :--- | :--- | :---: |
| **Prueba API Directa** | DNI `79665184` | Nombre oficial RENIEC | `"ADRIANO MATHIAS RIOS CORREA"` | ✅ APROBADO |
| **Prueba API Alterna** | DNI `43567890` | Nombre oficial RENIEC | `"NEISSER DANIEL LLACSA ANGULO"` | ✅ APROBADO |
| **Endpoint Backend** | `GET /api/v1/publico/buscar-cliente/79665184` | HTTP 200 con `fuente: "reniec"` | JSON estructurado con `encontrado: true` | ✅ APROBADO |
| **Navegador E2E** | `/registrar-pedido` (DNI Remitente) | Autocompletado reactivo en pantalla | Nombre completado + Badge verde de verificación | ✅ APROBADO |
| **Compilación Frontend** | `npm run build` | 0 errores de TypeScript/Vite | Build exitoso en 2.79s | ✅ APROBADO |

---

## 🔒 Consideraciones de Seguridad y Buenas Prácticas
1. **Protección PII (Datos Sensibles):** La consulta pública únicamente expone el nombre del titular para facilitar el despacho y evitar fraudes o suplantaciones en la recepción del paquete; teléfonos y correos locales se mantienen estrictamente enmascarados según la Ley N° 29733.
2. **Tolerancia a Fallos:** Si el servicio externo de RENIEC tiene alta latencia o no responde, el sistema no lanza un HTTP 500, sino que degrada suavemente a `fuente: "manual"`, permitiendo que el cliente continúe su registro de pedido sin interrupciones.
