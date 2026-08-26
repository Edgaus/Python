# Python / MBE Control

Repositorio personal de herramientas en Python. El producto principal es el
sistema de **control y monitoreo de celdas MBE** (Molecular Beam Epitaxy)
dentro de la carpeta [`PLC/`](PLC/).

Si es tu primera vez aquí: empieza por **`PLC/`**. El resto de carpetas
(`Interpolate_Data/`, `Compress Images/`, `Sender Gmail Emails/`, `Notes/`)
son utilidades aparte y no forman parte del control MBE.

---

## ¿Qué hace el sistema PLC?

Controla y registra la **apertura/cierre de celdas de efusión** (Ga, Al, In,
As, N) durante un crecimiento epitaxial:

1. Diseñas una **receta** (capas + tiempos Continuo/Ciclo).
2. El **monitor 24/7** ejecuta la receta y decide en cada instante qué celda
   abrir o cerrar.
3. Esas órdenes van (o irán) al **PLC Siemens** vía Snap7.
4. Mientras corre, se escribe un **CSV de historial** con el estado de cada
   celda — esa es la fuente natural para una **base de datos de monitoreo**.

```text
  [UI1 builder.py]  crea receta JSON
         │
         ▼
  [UI2+UI3 main.py]  plan + luces "ahora"  ◄──UDP──►  [C4+C5 monitor_247.py]
         │                                              │
         │                                              ├──► Siemens PLC (Snap7)
         │                                              └──► historial/*.csv
         │                                                         │
         └──────────────► [UI4 historial_vivo.py] ◄────────────────┘
                          timeline de la REALIDAD
```

| Pieza | Archivo | Rol |
|---|---|---|
| **UI1** Crear recetas | `PLC/builder.py` | Editor visual → exporta JSON |
| **UI2** Timeline del plan | parte de `PLC/main.py` | Dibuja la receta JSON |
| **UI3** Luces abiertas/cerradas | parte de `PLC/main.py` | Estado “ahora” + start/pause/stop |
| **UI4** Historial vivo | `PLC/historial_vivo.py` | Timeline desde el CSV (realidad) |
| **Cerebro 4** Secuenciador | `MotorSecuenciador` en `monitor_247.py` | Decide cuándo abrir/cerrar |
| **Cerebro 5** Monitor 24/7 | bucle UDP en `monitor_247.py` | No se apaga; escribe CSV; habla con PLC |

Archivos de soporte:

| Archivo | Rol |
|---|---|
| `PLC/config.py` | IP del PLC, rack/slot, números de DB Snap7, periodo de muestreo |
| `PLC/plc_client.py` | Driver Snap7 (leer/escribir Data Blocks) |
| `PLC/plc_worker.py` | Hilo Qt que sondea sensores del PLC periódicamente |
| `PLC/styles.py` | Estilos visuales compartidos de las UIs PyQt |
| `PLC/recetas/`, `PLC/Recetario/` | Recetas JSON |
| `PLC/historial/` | CSV de corridas (generados en runtime; gitignored) |

---

## Cómo arrancar (desarrollo)

Este proyecto **no requiere `.venv`**. Usa tu Python normal de Windows.

### Windows (tu laptop)

1. **Elimina `.venv` si existe** (PowerShell, en la raíz del repo):
   ```powershell
   deactivate   # si estaba activado; si falla, ignóralo
   Remove-Item -Recurse -Force .\.venv -ErrorAction SilentlyContinue
   ```
2. Instala las librerías en tu Python del sistema:
   ```powershell
   .\install_deps.bat
   ```
   o a mano:
   ```powershell
   python -m pip install --user -r requirements.txt
   ```
3. En Cursor/VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → elige tu
   Python normal (ruta **sin** `.venv` en el medio).
4. Corre el programa:
   ```powershell
   cd PLC
   python main.py
   ```

### Linux / Cloud (agentes)

En cloud a veces se usa `.venv` solo en la VM. En tu laptop, no es necesario.

```bash
python3 -m pip install --user -r requirements.txt
cd PLC
python3 main.py
python3 monitor_247.py
```

También puedes abrir Builder y UI4 desde el menú lateral de `main.py`.

**Nota actual:** en `main.py` la red UDP está comentada (“Modo Visual”), así que
la GUI visualiza recetas localmente y aún no manda `start`/`stop` al monitor.
Para probar el cerebro + CSV, envía comandos UDP a `127.0.0.1:5000` o
rehabilita los sockets en `main.py`. Snap7 hacia el PLC físico también está
comentado en el monitor hasta conectar hardware.

Más detalle operativo: [`AGENTS.md`](AGENTS.md).

---

## Para quien monta la base de datos de monitoreo

Hoy el “log de verdad” de apertura/cierre de celdas es el CSV que escribe
`monitor_247.py` en `PLC/historial/historial_YYYYMMDD_HHMMSS.csv`.

### Formato actual del CSV

```text
Tiempo_Global(s),Ga,Al,In,As,N
0.1,CERRADA,CERRADA,CERRADA,CERRADA,ABIERTA
0.2,CERRADA,ABIERTA,CERRADA,CERRADA,ABIERTA
...
```

| Columna | Significado |
|---|---|
| `Tiempo_Global(s)` | Segundos desde el inicio del crecimiento |
| `Ga`, `Al`, `In`, `As`, `N` | `ABIERTA` o `CERRADA` en ese instante |

El monitor hace **flush** tras cada fila para que UI4 (y un futuro importer a
DB) puedan leer en tiempo casi real.

### Esquema SQL sugerido (punto de partida)

Una tabla de muestras (una fila = un instante del monitor):

```sql
CREATE TABLE cell_state_samples (
    id              BIGSERIAL PRIMARY KEY,
    run_id          UUID NOT NULL,          -- una corrida / un CSV
    t_global_s      DOUBLE PRECISION NOT NULL,
    ga_open         BOOLEAN NOT NULL,
    al_open         BOOLEAN NOT NULL,
    in_open         BOOLEAN NOT NULL,
    as_open         BOOLEAN NOT NULL,
    n_open          BOOLEAN NOT NULL,
    recorded_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE growth_runs (
    run_id          UUID PRIMARY KEY,
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    recipe_name     TEXT,
    source_csv      TEXT                    -- ej. historial_20260814_003151.csv
);
```

Ideas útiles:

- **Booleans** (`ga_open`) en vez de strings `ABIERTA`/`CERRADA` facilitan
  consultas (`WHERE al_open AND NOT ga_open`).
- Guarda `run_id` para agrupar una corrida completa.
- Más adelante puedes añadir columnas de sensores (temperaturas del
  `DB_SENSORES` vía `plc_worker.py`) en otra tabla `sensor_samples`.
- El punto de enganche en código es el bloque “Guardar CSV On-The-Fly” en
  `monitor_247.py`: ahí mismo (o justo después) se puede hacer un `INSERT`
  a la DB además del CSV.

Puertos UDP locales del monitor:

| Puerto | Dirección | Uso |
|---|---|---|
| `5000` | UI → monitor | Comandos JSON: `load`, `start`, `pause`, `stop`, `update_recipe` |
| `5001` | monitor → UI | Estado JSON: receta, tiempos, `estado_luces_ui` |

---

## Otras carpetas (fuera del foco MBE)

| Carpeta | Qué es |
|---|---|
| `Interpolate_Data/` | Suavizado/interpolación de datos científicos (SciPy) |
| `Compress Images/` | Compresión de imágenes (Pillow) |
| `Sender Gmail Emails/` | Scripts de mail-merge (varios requieren Windows + Word) |
| `Notes/` | Notebooks de aprendizaje |

---

## Dependencias

Ver [`requirements.txt`](requirements.txt). En Windows (sin `.venv`):

```powershell
python -m pip install --user -r requirements.txt
# or: .\install_deps.bat
```

`python-snap7` no está en el requirements todavía: necesita la librería nativa
`libsnap7` y el PLC en red. `comtypes` es solo Windows (scripts de Gmail).
