# Guía Técnica: Catálogo de Scripts Ejecutables y Mantenimiento de Datos

Esta guía documenta los scripts ejecutables ubicados en [`CargaExpressBackend/scripts/`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts), indicando **para qué caso específico se debe utilizar cada uno**, los comandos exactos de terminal y el flujo de regularización de datos en **CargaExpress Perú**.

---

## 1. Matriz Rápida de Scripts y Casos de Uso

| Script | Propósito Principal | ¿Cuándo ejecutarlo? | Comando Windows PowerShell |
| :--- | :--- | :--- | :--- |
| **`populate_full_dwh_2026.py`** | Poblador maestro 2026 (84 agencias, 1,200+ envíos, 4 modalidades, estacionalidad, movimientos de caja). | Cuando se necesita poblar la base de datos completa con datos realistas para demostración y analítica anual. | `.\.venv\Scripts\python.exe scripts\populate_full_dwh_2026.py` |
| **`regularize_historial_envios.py`** | Reconstrucción cronológica de hitos de auditoría en la tabla `historial_envios`. | Cuando las encomiendas aparecen en tracking público sin su línea de tiempo (*"No hay hitos adicionales"* / órdenes fantasma). | `.\.venv\Scripts\python.exe scripts\regularize_historial_envios.py` |
| **`export_dwh_for_powerbi.py`** | Extracción ETL dimensional (Star Schema) a archivos CSV (`dwh_powerbi/`). | Cuando se crean o modifican envíos y se desea actualizar el modelo en **Power BI Desktop**. | `.\.venv\Scripts\python.exe scripts\export_dwh_for_powerbi.py` |
| **`diagnostico_usuarios.py`** | Auditoría y listado de credenciales, roles RBAC y accesos de colaboradores. | Cuando se necesita consultar contraseñas, correos institucionales o verificar usuarios activos por sede. | `.\.venv\Scripts\python.exe scripts\diagnostico_usuarios.py` |
| **`sync_sql_and_db.py`** | Sincronización entre `cargaexpress.db` (SQLite) y `cargaexpress.sql` (PostgreSQL). | Cuando se realizan cambios en SQLite y se requiere regenerar el script SQL maestro de base de datos. | `.\.venv\Scripts\python.exe scripts\sync_sql_and_db.py` |
| **`reparar_agencias_y_usuarios.py`** | Verificación de integridad referencial entre colaboradores y agencias operativas. | Si algún usuario queda huérfano de sede o se agregan agencias nuevas que requieren personal asignado. | `.\.venv\Scripts\python.exe scripts\reparar_agencias_y_usuarios.py` |

---

## 2. Detalle de Ejecución por Caso de Uso

### Caso 1: Quiero poblar todo el sistema para 2026 (Demostración / Dashboard / Power BI)
* **Archivo:** [`CargaExpressBackend/scripts/populate_full_dwh_2026.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/populate_full_dwh_2026.py)
* **¿Qué hace exactamente?:**
  1. Conecta con las **84 agencias** a nivel nacional en los **25 departamentos** del Perú (INEI Ubigeo).
  2. Crea **clientes naturales y corporativos** (DNI y RUC validados).
  3. Inserta **1,200+ encomiendas** distribuidas cronológicamente a lo largo de 2026, con curvas de estacionalidad (picos en Q3/Q4 por Fiestas Patrias y fin de año).
  4. Balancea las **4 modalidades de entrega**:
     - `agencia_agencia` (Ventanilla a Ventanilla)
     - `agencia_domicilio` (Ventanilla con entrega a puerta)
     - `domicilio_agencia` (Recojo a domicilio para retiro en agencia)
     - `domicilio_domicilio` (Servicio puerta a puerta integral)
  5. Asocia transacciones de cobro en caja chica (`caja_movimientos`).
  6. **Ejecuta automáticamente** la regularización de historial (`regularize_historial_envios.py`) y exporta los datasets de Power BI (`export_dwh_for_powerbi.py`).
* **Comando:**
  ```powershell
  cd C:\Users\User\Documents\VSC-Integrador\CargaExpressBackend
  .\.venv\Scripts\python.exe scripts\populate_full_dwh_2026.py
  ```

---

### Caso 2: El Tracking en Tiempo Real no muestra los eventos de un envío (Órdenes sin hitos)
* **Archivo:** [`CargaExpressBackend/scripts/regularize_historial_envios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/regularize_historial_envios.py)
* **¿Cuándo usarlo?:**  
  Si al ingresar un código de seguimiento en el portal web (ej: `CE26111263`) el estado general dice *ENTREGADO* o *EN RUTA*, pero abajo aparece el mensaje:
  > *"No hay hitos adicionales registrados para esta encomienda"*
* **¿Qué hace el script?:**  
  Recorre cada encomienda en `envios` y reconstruye su línea de tiempo cronológica en la tabla `historial_envios`:
  1. `REGISTRADO`: Fecha inicial de registro, código QR emitido.
  2. `RECEPCIONADO`: Pasó por balanza oficial, pesaje físico y rotulado.
  3. `EN_RUTA`: Despachado en camión interprovincial con manifiesto en carretera nacional.
  4. `EN_AGENCIA_DESTINO`: Arribo a bodega de destino, clasificado para retiro o reparto.
  5. `ENTREGADO`: Entrega final conforme con verificación de DNI y firma de constancia.
* **Comando:**
  ```powershell
  cd C:\Users\User\Documents\VSC-Integrador\CargaExpressBackend
  .\.venv\Scripts\python.exe scripts\regularize_historial_envios.py
  ```

---

### Caso 3: Deseo actualizar los gráficos en Power BI Desktop
* **Archivo:** [`CargaExpressBackend/scripts/export_dwh_for_powerbi.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/export_dwh_for_powerbi.py)
* **¿Cuándo usarlo?:**  
  Cuando registras nuevos envíos o ejecutas pruebas y quieres que los tableros analíticos de Power BI Desktop reflejen los datos más recientes.
* **¿Qué genera?:**  
  Exporta 5 tablas en formato CSV en la carpeta `CargaExpressBackend/dwh_powerbi/`:
  - `dim_agencia.csv` (84 agencias, departamentos, provincias, distritos, ubigeo)
  - `dim_cliente.csv` (Directorio de clientes clasificados: Persona Natural vs Jurídica)
  - `dim_tiempo.csv` (Calendario 2026: trimestres, meses, semanas, laborables)
  - `fact_envios.csv` (Hechos de envíos: fletes, pesos, IGV, modalidad, estado)
  - `fact_caja_movimientos.csv` (Hechos de tesorería: ingresos, egresos, medios de pago)
* **Comando:**
  ```powershell
  cd C:\Users\User\Documents\VSC-Integrador\CargaExpressBackend
  .\.venv\Scripts\python.exe scripts\export_dwh_for_powerbi.py
  ```
* **Paso en Power BI Desktop:**  
  Una vez ejecutado, abre tu archivo `.pbix` y en la pestaña superior presiona el botón **🔄 Actualizar**.

---

### Caso 4: Consultar credenciales de prueba o verificar usuarios del sistema
* **Archivo:** [`CargaExpressBackend/scripts/diagnostico_usuarios.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/scripts/diagnostico_usuarios.py)
* **¿Cuándo usarlo?:**  
  Si necesitas recordar las credenciales de un cajero, almacenero o courier para iniciar sesión en el frontend.
* **Comando:**
  ```powershell
  cd C:\Users\User\Documents\VSC-Integrador\CargaExpressBackend
  .\.venv\Scripts\python.exe scripts\diagnostico_usuarios.py
  ```
* **Convención General de Credenciales:**
  - **Contraseña universal de colaboradores:** `CargaExp#2026`
  - **Formato de email:** `nombre.apellido@cargaexpress.pe`
  - **Administrador General:** `admin@cargaexpress.pe`

---

## 3. Consideraciones Importantes de Ejecución en Windows

1. **Uso obligatorio del entorno virtual (`.venv`):**  
   Siempre ejecuta los scripts invocando el ejecutable del entorno virtual:
   ```powershell
   .\.venv\Scripts\python.exe scripts\<nombre_script>.py
   ```
   Esto garantiza que se utilicen las dependencias instaladas (`SQLAlchemy`, `FastAPI`, `Pydantic`).

2. **Ruta de Base de Datos:**  
   Todos los scripts operan de forma centralizada sobre:
   [`CargaExpressBackend/cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db).

