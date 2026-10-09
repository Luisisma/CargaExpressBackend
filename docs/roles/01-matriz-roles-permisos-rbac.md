# Matriz de Control de Acceso Basado en Roles (RBAC) y Permisos

> **Módulo:** Seguridad y Gestión de Privilegios del Sistema  
> **Estándar:** NIST SP 800-162 (ABAC/RBAC) | OWASP API Security Top 10 (API5: Broken Function Level Authorization)  
> **Backend Guard:** [`app/api/deps.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/deps.py) (`require_role`)  
> **Frontend Guard:** [`src/components/layout/AdminLayout.jsx`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressFront/src/components/layout/AdminLayout.jsx)  
> **Estado:** 🛡️ **ESPECIFICACIÓN OFICIAL DE ROLES Y PERMISOS**

---

## 1. Principio Rector: Cero Simulación, RBAC Basado en Tokens Criptográficos

El sistema ha eliminado la simulación manual de roles en el cliente. **La identidad y el rol operativo se derivan exclusivamente del token JWT firmado por el backend**:

1. El Administrador da de alta al personal asignándole un rol formal (`tipo`) y sucursal (`agencia_id`).
2. Al iniciar sesión (con verificación opcional 2FA/TOTP), el backend emite un `access_token` que contiene el rol y la versión de sesión (`sesion_version`).
3. El frontend adapta la navegación, tarjetas de métricas y acciones rápidas según el rol real extraído del token.
4. El backend rechaza con `HTTP 403 Forbidden` cualquier intento de invocar un endpoint no autorizado, aun si el usuario intentara forzar la llamada HTTP directamente.

---

## 2. Catálogo Oficial de Roles Operativos

| Rol | Tipo en BD | Alcance y Responsabilidad Principal |
| :--- | :--- | :--- |
| **`ADMINISTRADOR`** | `administrador` | Gestión global del sistema: alta/baja de personal, auditoría forense, agencias y políticas maestras. |
| **`SUPERVISOR`** | `supervisor` | Control operativo de sucursal: monitoreo de recaudación de caja, reasignación de encomiendas y resolución de incidencias. |
| **`CAJERO`** | `cajero` | Atención presencial en ventanilla: pesaje en balanza oficial, cobro de fletes, entrega a destinatarios y cuadre de caja. |
| **`ALMACEN`** | `almacen` | Custodia física de bodega: clasificación de bultos, carga a camión (despacho a ruta) y descarga de camiones arribados. |
| **`COURIER`** | `courier` | Logística de última milla: reparto a domicilio del destinatario y recojo en domicilio del remitente con validación de DNI. |
| **`TRANSPORTISTA`** | `transportista` | Traslado interprovincial: transporte físico de flota en carretera nacional entre agencias de origen y destino. |

---

## 3. Matriz de Acceso a Módulos del Frontend (React Vite)

| Módulo / Vista | Ruta Frontend | `ADMIN` | `SUPERVISOR` | `CAJERO` | `ALMACEN` | `COURIER` | `TRANSPORTISTA` |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dashboard Operativo** | `/admin/dashboard` | ✅ | ✅ | ✅ | ✅ (Solo Carga) | ✅ (Solo Entregas) | ✅ |
| **Nuevo Envío (Mostrador)** | `/registrar-pedido` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Mis Envíos (Lista General)**| `/admin/envios` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Recepción (Ventanilla)** | `/admin/caja/recepcion`| ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Caja Chica y Arqueos** | `/admin/caja` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Despacho a Ruta (Camiones)**| `/admin/almacen/despacho`| ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Arribos (Descarga Bodega)** | `/admin/almacen/arribos` | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Guías de Remisión** | `/admin/guias` | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Manifiestos de Carga** | `/admin/manifiestos` | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Mis Entregas Asignadas** | `/admin/courier` | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Personal y Usuarios** | `/admin/usuarios` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Sedes y Agencias** | `/admin/agencias` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 4. Matriz de Endpoints Protegidos en Backend (FastAPI)

| Endpoint REST | Método | Roles Permitidos en Backend (`require_role`) | Código si no autorizado |
| :--- | :---: | :--- | :---: |
| `/api/v1/usuarios/*` | `CRUD` | `ADMINISTRADOR` | `403 Forbidden` |
| `/api/v1/dashboard/resumen` | `GET` | `ADMINISTRADOR`, `SUPERVISOR`, `CAJERO`, `ALMACEN`, `COURIER`, `TRANSPORTISTA` | `401 Unauthorized` |
| `/api/v1/envios` (Listado) | `GET` | `ADMINISTRADOR`, `SUPERVISOR`, `CAJERO`, `ALMACEN`, `COURIER`, `TRANSPORTISTA` | `403 Forbidden` |
| `/api/v1/envios/{id}` (Ficha) | `GET` | `ADMINISTRADOR`, `SUPERVISOR`, `CAJERO`, `ALMACEN`, `COURIER`, `TRANSPORTISTA` | `403 Forbidden` |
| `/api/v1/envios/{id}/recepcionar` | `POST`| `CAJERO`, `ADMINISTRADOR`, `SUPERVISOR`, `ALMACEN` | `403 Forbidden` |
| `/api/v1/envios/{id}/despachar` | `POST`| `ALMACEN`, `ADMINISTRADOR`, `SUPERVISOR`, `TRANSPORTISTA` | `403 Forbidden` |
| `/api/v1/envios/{id}/arribar` | `POST`| `ALMACEN`, `ADMINISTRADOR`, `SUPERVISOR`, `CAJERO` | `403 Forbidden` |
| `/api/v1/caja/*` (Aperturas/Cierre) | `ALL` | `CAJERO`, `SUPERVISOR`, `ADMINISTRADOR` | `403 Forbidden` |
| `/api/v1/agencias/*` | `POST/PUT` | `ADMINISTRADOR` | `403 Forbidden` |

---

## 5. Prevención de BFLA (Broken Function Level Authorization)

1. **Defensa en Profundidad:** El Frontend oculta visualmente los botones que el usuario no tiene permitido accionar. Sin embargo, **la seguridad no descansa en el frontend**; el backend valida criptográficamente cada petición mediante `require_role(...)`.
2. **Registro de Auditoría de Intentos Denegados:** Si un usuario con rol `almacen` intenta consumir un endpoint de usuarios o caja alterando su cliente HTTP, se genera un evento `ACCESO_DENEGADO_RBAC` en la tabla `auditoria_seguridad` con nivel `WARN` indicando su IP y usuario responsable.
