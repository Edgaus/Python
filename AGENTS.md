# AGENTS.md

## Cursor Cloud specific instructions

### Primary scope: `PLC/` only

**Default focus for Cloud Agents is the MBE (Molecular Beam Epitaxy) cell
control / automation stack under `PLC/`.** Do not work on other top-level
folders (`Interpolate_Data/`, `Compress Images/`, `Sender Gmail Emails/`,
`Notes/`) unless the user explicitly asks. The GitHub repo is the sync link
across Cloud Agent, laptop, and other devices — commit and push so all sides
stay aligned.

Python is 3.12. There is no web server, database, or shared build system.

### Environment / how deps are installed

- Python dependencies live in a virtualenv at `.venv/` (created by the startup
  update script from `requirements.txt`). Run everything with `.venv/bin/python`
  (or activate with `source .venv/bin/activate`).
- The GUI (`PLC/main.py`, `PLC/builder.py`) uses PyQt6 and needs Qt system
  libraries (`libEGL`, `libxkbcommon`, the `libxcb-*` family, etc.). Those are
  OS packages baked into the environment image, not installed by the update
  script. `python3.12-venv` is likewise baked into the image.
- `python-snap7` is intentionally **not** in `requirements.txt` (needs native
  `libsnap7` + a real Siemens PLC). Hardware integration is currently disabled
  in code.

### Lint / test

- There is **no test suite and no lint config**. Use
  `python -m py_compile PLC/*.py` as a syntax/compile check.

### `PLC/` — MBE SCADA stack (how to run)

| Process | Command | Role |
|---|---|---|
| Backend sequencer | `cd PLC && ../.venv/bin/python monitor_247.py` | UDP server: commands on `127.0.0.1:5000`, state on `127.0.0.1:5001`; CSV logs → `PLC/historial/` (gitignored) |
| Operator HMI | `cd PLC && DISPLAY=:1 ../.venv/bin/python main.py` | Load recipes, timeline (plan), start/pause/stop. Needs display `:1` in cloud VMs |
| Historial vivo (UI4) | `cd PLC && DISPLAY=:1 ../.venv/bin/python historial_vivo.py` | Real-time timeline from `historial/*.csv` that the monitor writes (realidad). Also launchable from main sidebar |
| Recipe builder (optional) | `cd PLC && DISPLAY=:1 ../.venv/bin/python builder.py` | Visual editor; also launchable from `main.py` via subprocess |

**File roles:** `builder.py` (recipe editor) → JSON in `recetas/` / `Recetario/` →
`main.py` (HMI) ↔ UDP ↔ `monitor_247.py` (`MotorSecuenciador`) → optional Snap7
via `plc_client.py` / `plc_worker.py` → Siemens S7 (`config.py`: IP / rack / slot / DBs).
`styles.py` is the shared PyQt stylesheet.

### Non-obvious caveats (PLC)

1. **UDP is commented out in `main.py` ("Modo Visual").** The GUI currently
   visualizes recipes locally and does **not** talk to `monitor_247.py`. To
   exercise the backend end-to-end, send UDP JSON commands (`load`, `start`,
   `pause`, `stop`, `update_recipe`) to port 5000 directly. Snap7/`MonitorPLCWorker`
   is also commented out in `monitor_247.py`.
2. **Two recipe shapes.** On disk: `name`, `growth_time`, `element_data`.
   Engine expects: `material`, `tiempo_total_crecimiento_sec`, `parametros_celdas`.
   `main.py`'s `normalize_step()` converts before send — keep that in mind if
   wiring UDP back up or changing the builder export format.
3. **Core hello-world action:** load a JSON recipe from `PLC/recetas/` (e.g.
   `receta_actual.json`) and confirm the growth timeline renders with per-cell
   colored bars.
4. **UI2 vs UI4:** `main.py` TimelineWidget = planned recipe (JSON). 
   `historial_vivo.py` = reality timeline built by tailing the CSV that
   `monitor_247.py` writes (with `flush` after each row so the UI can follow live).

### Out of scope (unless user asks)

- `Interpolate_Data/`, `Compress Images/`, `Sender Gmail Emails/`, `Notes/` —
  unrelated personal Python utilities / coursework in the same repo.
