# 💾 Guía Técnica: Respaldo (Backup) y Restauración de Base de Datos SQLite

Esta guía documenta los procedimientos oficiales, herramientas y comandos para **exportar, consultar y restaurar** la base de datos de **CargaExpress Perú** ([`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db)) en cualquier momento del ciclo de vida del proyecto.

---

## 1. Principio Fundamental de SQLite

A diferencia de motores cliente-servidor (como PostgreSQL o MySQL) que requieren procesos demonios y credenciales de red, **SQLite almacena el 100% de la base de datos (esquema, tablas, índices y datos) en un único archivo de disco local:**

* **Archivo Principal Activo:** [`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db) (Ubicado en la raíz de `CargaExpressBackend`).
* **Conexión SQLAlchemy:** `sqlite:///./cargaexpress.db`.

Esto permite dos tipos de respaldo:
1. **Respaldo Lógico (Dump SQL en texto plano):** Sentencias `CREATE TABLE` e `INSERT INTO` portables a otros motores o editores.
2. **Respaldo Físico (Copia Binaria `.db`):** Duplicado exacto byte a byte del archivo SQLite.

---

## 2. Herramienta Automatizada: `backup_db.py`

En la raíz del backend se encuentra el script utilitario [backup_db.py](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/backup_db.py), diseñado para ejecutarse sin librerías externas adicionales.

### 🚀 Comandos Rápidos de Uso

| Acción | Comando en Terminal (Powershell) | Descripción |
|:---|:---|:---|
| **Exportar Backup Completo** | `py backup_db.py` | Genera el SQL Dump en la raíz ([cargaexpress_backup.sql](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress_backup.sql)), guarda una copia histórica en `backups/` y clona el binario `.db`. |
| **Consultar Estado de Filas** | `py backup_db.py --status` | Imprime la tabla con el total de filas por cada tabla en la base de datos. |
| **Restaurar desde SQL** | `py backup_db.py --restore` | Reconstruye la base de datos desde `cargaexpress_backup.sql`. |
| **Restaurar desde un SQL específico** | `py backup_db.py --restore backups/archivo.sql` | Restaura los datos desde una copia histórica específica. |
| **Restaurar desde un binario `.db`** | `py backup_db.py --restore-db backups/archivo.db` | Reemplaza la base de datos activa por la copia binaria indicada. |

---

## 3. Ejemplo de Salida en Consola

Al ejecutar `py backup_db.py`, la consola mostrará:

```text
🔄 Iniciando respaldo de 'cargaexpress.db'...

=======================================================
 📊 ESTADO ACTUAL DE REGISTROS EN CARGAEXPRESS DB
=======================================================
Tabla                          |       N° Registros
-------------------------------------------------------
agencias                       |                  3
auditoria_operaciones          |                  8
auditoria_seguridad            |                340
clientes                       |                  6
envios                         |                  5
historial_envios               |                 16
usuarios                       |                  8
-------------------------------------------------------
TOTAL GENERAL                  |                386
=======================================================

✅ ¡RESPALDO COMPLETADO CON ÉXITO!
  📄 Dump SQL (raíz):       C:\...\CargaExpressBackend\cargaexpress_backup.sql (113.1 KB)
  📁 Dump SQL (historial):  C:\...\CargaExpressBackend\backups\cargaexpress_backup_20261013_204047.sql
  💾 Binario .db (copia):   C:\...\CargaExpressBackend\backups\cargaexpress_backup_20261013_204047.db (224.0 KB)
```

---

## 4. Respaldar en 1 Sola Línea (Sin scripts externos)

Si te encuentras en otra máquina o prefieres hacerlo mediante un comando de una sola línea en terminal:

```powershell
py -c "import sqlite3; con = sqlite3.connect('cargaexpress.db'); open('cargaexpress_backup.sql', 'w', encoding='utf-8').write('\n'.join(con.iterdump())); print('Backup generado')"
```

Este comando utiliza el método nativo `iterdump()` de Python, extrayendo la estructura completa y cada fila con formato estándar SQL.

---

## 5. ¿Cómo Consultar e Inspeccionar los Datos?

Para visualizar, editar o consultar las tablas de forma gráfica:

### Opción A: Extensión "SQLite Viewer" en VS Code (Recomendada)
1. Presiona `Ctrl + Shift + X` en Visual Studio Code.
2. Busca e instala la extensión **"SQLite Viewer"** (autor: *Florian Klampfer*).
3. Haz clic sobre el archivo [`cargaexpress.db`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress.db).
4. Se abrirá una interfaz con pestañas para cada tabla (`usuarios`, `envios`, `agencias`, `auditoria_seguridad`) con buscador y paginación.

### Opción B: Software de Escritorio "DB Browser for SQLite"
1. Descarga **[DB Browser for SQLite](https://sqlitebrowser.org/dl/)** (cuenta con versión portátil *.zip* sin instalación).
2. Abre el archivo `cargaexpress.db`.
3. Podrás ejecutar queries arbitrarias en la pestaña **"Execute SQL"**, ver esquemas y exportar tablas a CSV/JSON/Excel.

### Opción C: Ver el Script SQL Generado
Puedes abrir directamente [`cargaexpress_backup.sql`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/cargaexpress_backup.sql) como archivo de texto plano en cualquier editor.

---

## 6. Procedimiento de Restauración ante Emergencias

Si por algún motivo la base de datos se corrompe, se borran registros por error o se quiere volver a un estado previo:

1. **Restauración Automática Segura:**
   ```powershell
   py backup_db.py --restore
   ```
   * *Mecanismo de seguridad:* Antes de sobrescribir, el script automáticamente crea una copia preventiva llamada `cargaexpress_antes_de_restaurar_YYYYMMDD_HHMMSS.db` en la carpeta `backups/`, garantizando que nunca pierdas datos por accidente.

2. **Restauración Manual por Copia de Archivo:**
   Si tienes un archivo `.db` de respaldo en `backups/`, simplemente:
   * Detén el servidor FastAPI (`Ctrl + C` en la terminal de `py main.py`).
   * Copia el archivo respaldado sobre `cargaexpress.db`.
   * Reinicia el servidor FastAPI.

---

## 7. Estructura de Tablas Respaldadas en CargaExpress

| Tabla | Propósito en el Negocio | Registros Actuales |
|:---|:---|:---:|
| `usuarios` | Cuentas de personal, credenciales hasheadas (Bcrypt), secretos 2FA y roles. | 8 |
| `agencias` | Sedes y puntos de atención (Lima, Arequipa, Cusco). | 3 |
| `clientes` | Remitentes y destinatarios con DNI/RUC. | 6 |
| `envios` | Paquetes y encomiendas registradas con tracking, precios y estados. | 5 |
| `historial_envios` | Trazabilidad temporal de cada cambio de estado logístico. | 16 |
| `auditoria_seguridad` | Logs inmutables de inicios de sesión, 2FA, bloqueos e IPs. | 340 |
| `auditoria_operaciones` | Trazabilidad de creaciones y modificaciones de personal. | 8 |
