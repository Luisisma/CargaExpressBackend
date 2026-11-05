# 🗺️ Guía Técnica de Exposición 14: Mapa Integral de Rutas, Endpoints y Servicios

Esta guía es el **mapa de navegación técnica definitivo** de la API de **CargaExpress Perú**. Permite responder en segundos ante cualquier pregunta del evaluador o jurado sobre qué archivo, ruta, servicio o modelo procesa cada petición del sistema.

---

## 1. Arquitectura de 3 Capas (Controlador ➔ Servicio ➔ Persistencia)

El backend de FastAPI sigue el patrón arquitectónico de **Separación de Responsabilidades**:
1. **Capa de Controladores / Rutas (`app/api/v1/endpoints/`):** Valida esquemas Pydantic y aplica seguridad con dependencias (`deps.py`).
2. **Capa de Servicios de Negocio (`app/services/`):** Contiene la lógica pura, cálculos de cubicaje, algoritmos criptográficos, notificaciones por correo y auditoría.
3. **Capa de Persistencia y Modelos ORM (`app/models/`):** Mapeo de tablas de base de datos en SQLAlchemy 2.0.

```text
[Cliente Web / Móvil] 
        │ HTTP JSON Request
        ▼
[app/api/v1/endpoints/*.py] ── (Valida esquemas Pydantic y Tokens JWT)
        │ Invocación
        ▼
[app/services/*_service.py]  ── (Aplica Reglas de Negocio y Notificaciones)
        │ Transacción ORM
        ▼
[app/models/*.py] ──────────► [PostgreSQL 17 / SQLite 3]
```

---

## 2. Catálogo Maestro de Rutas y Servicios del Sistema

### 2.1. Módulo Público y Autoservicio (Clientes e Invitados)
| Método | Endpoint URL | Archivo Controlador | Servicio Invocado | Función Clave | Rol RBAC |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/publico/cotizar` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `cotizar(...)` con cubicaje 6000 | Público |
| `POST` | `/api/v1/publico/pedidos/registro` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `registrar_pedido_publico(...)` | Público |
| `GET` | `/api/v1/publico/tracking/{codigo}` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `consultar_tracking_publico(...)` | Público |
| `GET` | `/api/v1/publico/agencias` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `listar_agencias_activas(...)` | Público |
| `POST` | `/api/v1/publico/pedidos/cancelar` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) | `cancelar_pedido_publico(...)` | Público |
| `POST` | `/api/v1/publico/consultar-documento` | [`publico.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/publico.py) | [`consulta_documento_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/consulta_documento_service.py) | `consultar_dni_o_ruc(...)` | Público |

---

### 2.2. Módulo de Autenticación, Seguridad y 2FA
| Método | Endpoint URL | Archivo Controlador | Servicio Invocado | Función Clave | Rol RBAC |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/login` | [`auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | [`auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | `autenticar_usuario(...)` con Bcrypt | Público |
| `POST` | `/api/v1/auth/verificar-2fa` | [`auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | [`auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | `verificar_totp(...)` vía PyOTP | Autenticado |
| `POST` | `/api/v1/auth/recuperar-password` | [`auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | [`auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | `solicitar_recuperacion(...)` | Público |
| `POST` | `/api/v1/auth/restablecer-password` | [`auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | [`auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | `restablecer_password(...)` | Token JWT |
| `GET` | `/api/v1/auth/me` | [`auth.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/auth.py) | [`auth_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/auth_service.py) | `obtener_perfil_actual(...)` | Bearer Token |

---

### 2.3. Módulo de Operaciones, Balanza y Cadena Logística
| Método | Endpoint URL | Archivo Controlador | Servicio Invocado | Función Clave | Rol RBAC |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/envios/{id}/pesar-recepcionar` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `recepcionar_y_pesar(...)` | Cajero / Almacén |
| `POST` | `/api/v1/envios/despachar-lote` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `despachar_en_transito(...)` | Almacén / Supervisor |
| `POST` | `/api/v1/envios/{id}/recibir-agencia-destino` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `arribar_agencia_destino(...)` | Almacén / Cajero |
| `POST` | `/api/v1/envios/{id}/declarar-siniestro` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `declarar_siniestro(...)` | Supervisor / Admin |
| `GET` | `/api/v1/envios/{id}/guia-remision` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py) | `generar_guia_remision(...)` | Todos los roles |

---

### 2.4. Módulo de Courier y Reparto a Domicilio (Última Milla)
| Método | Endpoint URL | Archivo Controlador | Servicio Invocado | Función Clave | Rol RBAC |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/admin/courier/mis-entregas` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`courier_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py) | `listar_entregas_courier(...)` | Courier / Admin |
| `POST` | `/api/v1/envios/{id}/iniciar-reparto` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`courier_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py) | `iniciar_ruta_reparto(...)` | Courier / Supervisor |
| `POST` | `/api/v1/envios/{id}/entregar-domicilio` | [`envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/envios.py) | [`courier_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/courier_service.py) | `entregar_con_firma_y_foto(...)` | Courier / Transportista |

---

### 2.5. Módulo de Finanzas, Caja Chica y Arqueos
| Método | Endpoint URL | Archivo Controlador | Servicio Invocado | Función Clave | Rol RBAC |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/caja/aperturar` | [`caja.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/caja.py) | [`caja_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/caja_service.py) | `aperturar_caja(...)` | Cajero / Admin |
| `POST` | `/api/v1/caja/cobrar-presencial` | [`caja.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/caja.py) | [`caja_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/caja_service.py) | `registrar_cobro_caja(...)` | Cajero |
| `POST` | `/api/v1/caja/arqueo-ciego` | [`caja.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/caja.py) | [`caja_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/caja_service.py) | `ejecutar_arqueo_ciego(...)` | Cajero / Supervisor |
| `POST` | `/api/v1/caja/cerrar` | [`caja.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/caja.py) | [`caja_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/caja_service.py) | `cerrar_turno_caja(...)` | Cajero / Supervisor |

---

### 2.6. Módulo Administrativo y Dashboard Operativo
| Método | Endpoint URL | Archivo Controlador | Servicio Invocado | Función Clave | Rol RBAC |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/dashboard/resumen` | [`dashboard.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/dashboard.py) | Consultas SQL Agregadas | `obtener_metricas_hoy(...)` | Admin / Supervisor |
| `GET` | `/api/v1/usuarios/` | [`usuarios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/usuarios.py) | Operaciones ORM Usuario | `listar_colaboradores(...)` | Administrador |
| `GET` | `/api/v1/agencias/` | [`agencias.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/agencias.py) | [`agencia_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/agencia_service.py) | `listar_sedes_provinciales(...)` | Todos los roles |
| `GET` | `/api/v1/clientes/` | [`clientes.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/api/v1/endpoints/clientes.py) | Operaciones ORM Cliente | `listar_directorio_clientes(...)` | Admin / Cajero |

---

## 3. Resumen Rápido para Exposición

Cuando te pregunten sobre la estructura del código:
* *"El sistema está organizado bajo una arquitectura limpia por capas en FastAPI.*
* *Las peticiones HTTP ingresan por **`endpoints/*.py`**, donde se autentica el usuario mediante tokens JWT y se valida el esquema Pydantic.*
* *La lógica del negocio se procesa de forma desacoplada en **`services/*.py`** (por ejemplo, **`publico_service.py`** para cubicaje con divisor 6000, **`courier_service.py`** para entrega domiciliaria con firma digital, y **`email_service.py`** para el despacho de correos SMTP con STARTTLS).*
* *Los datos se persisten atómicamente en **`models/*.py`** utilizando SQLAlchemy 2.0 ORM con integridad referencial estricta."*

