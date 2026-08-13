# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **personal Python workspace** containing several independent
projects (no web server, no database, no shared build system). Each subfolder is
its own standalone tool. Python is 3.12.

### Environment / how deps are installed

- Python dependencies live in a virtualenv at `.venv/` (created by the startup
  update script from `requirements.txt`). Run everything with `.venv/bin/python`
  (or activate with `source .venv/bin/activate`).
- The GUI app (`PLC/`) uses PyQt6, which needs Qt's system libraries
  (`libEGL`, `libxkbcommon`, the `libxcb-*` family, etc.). These are OS packages
  baked into the environment image, not installed by the update script.
- `python3.12-venv` is also an OS package baked into the image (needed to create
  `.venv`).
- Two dependencies are intentionally NOT installed because they cannot work on
  Linux and are excluded from `requirements.txt`: `comtypes` (Windows Word COM
  automation) and `python-snap7` (needs native `libsnap7` + real Siemens PLC
  hardware). See per-project notes below.

### Lint / test

- There is **no test suite and no lint config** in this repo. Use
  `python -m py_compile <files>` as a syntax/compile check.

### Projects and how to run them

- **`PLC/` — MBE / SCADA control (the main multi-process app).**
  - Backend sequencer: `cd PLC && ../.venv/bin/python monitor_247.py`. It is a
    UDP server: listens for commands on `127.0.0.1:5000` and publishes state to
    `127.0.0.1:5001`. It writes CSV run logs to `PLC/historial/` (gitignored).
  - GUI: `cd PLC && DISPLAY=:1 ../.venv/bin/python main.py`. Needs a display
    (`:1` is available in cloud VMs). Loading a recipe JSON from `PLC/recetas/`
    or `PLC/Recetario/` renders the growth timeline — this is the core action.
  - NON-OBVIOUS: in `main.py` the UDP networking is **commented out** ("Modo
    Visual"), so the GUI does NOT actually talk to `monitor_247.py`; it only
    visualizes recipes locally. To exercise the backend end-to-end, send UDP
    JSON commands (`load`, `start`, `pause`, `stop`) to port 5000 directly.
  - NON-OBVIOUS: the backend/engine reads the normalized recipe shape
    (`material`, `tiempo_total_crecimiento_sec`, `parametros_celdas`). The recipe
    files on disk use the raw shape (`name`, `growth_time`, `element_data`);
    `main.py`'s `normalize_step()` converts between them before sending.
  - `builder.py` (visual recipe editor) is optional; `main.py` launches it via
    `subprocess`.

- **`Interpolate_Data/` — SciPy spline smoothing CLI.**
  Run `cd Interpolate_Data && ../.venv/bin/python Interpolate_data.py`. Reads
  `Data_to_interpolate/*.txt`, writes `Data_now_interpolated/*_fitted.txt`.

- **`Compress Images/` — Pillow image compressor CLI.**
  Run `cd "Compress Images" && ../.venv/bin/python Main.py`. Writes to
  `Compressed/`.
  NON-OBVIOUS: `Main.py` calls `Image.show()` as its last step, which spawns a
  blocking OS image viewer. The compressed file is already saved before this, so
  the viewer only matters interactively — a piped/headless run may appear to
  "hang" on that final viewer step even though the work is done.

- **`Sender Gmail Emails/` — bulk Gmail mail-merge scripts.**
  Standalone one-off scripts. Several import `comtypes` (Windows + Microsoft Word
  COM) and all need real Gmail SMTP credentials, so they are **not runnable on a
  Linux cloud VM**. Treat as out of scope for automated runs.

- **`Notes/` — Jupyter learning notebooks.** Educational only, not a deployable
  service.
