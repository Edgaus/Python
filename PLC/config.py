# config.py
# Mapa dummy para armar el DB en TIA Portal. Ajusta números de DB/offsets
# cuando tu tabla real esté lista; los nombres de celdas ya son los definitivos.

PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1

# True = Python simula el PLC en memoria (sin Snap7).
# False = receta y banderas van al Siemens; el PLC/Arduino ejecuta los tiempos.
SIMULAR_PLC = True

# ---------------------------------------------------------------------------
# Celdas dummy (índice = bit en DB_CELDAS)
# 0 Al, 1 Ga, 2 In, 3 N, 4 As, 5 Si, 6 Be, 7 Mn, 8 Mg
# ---------------------------------------------------------------------------
CELDAS = ["Al", "Ga", "In", "N", "As", "Si", "Be", "Mn", "Mg"]

# Direcciones de Data Blocks
DB_RECETA = 10
DB_SENSORES = 11
DB_CELDAS = 12
DB_CONTROL = 13

# DB12 DB_CELDAS — feedback real (el PLC/Arduino escribe)
# Byte 0: Al Ga In N As Si Be Mn
# Byte 1: Mg . . . . . . .
MAPA_CELDAS = {
    "Al": {"db": DB_CELDAS, "byte": 0, "bit": 0},
    "Ga": {"db": DB_CELDAS, "byte": 0, "bit": 1},
    "In": {"db": DB_CELDAS, "byte": 0, "bit": 2},
    "N":  {"db": DB_CELDAS, "byte": 0, "bit": 3},
    "As": {"db": DB_CELDAS, "byte": 0, "bit": 4},
    "Si": {"db": DB_CELDAS, "byte": 0, "bit": 5},
    "Be": {"db": DB_CELDAS, "byte": 0, "bit": 6},
    "Mn": {"db": DB_CELDAS, "byte": 0, "bit": 7},
    "Mg": {"db": DB_CELDAS, "byte": 1, "bit": 0},
}
CELDAS_BYTES = 2

# DB13 DB_CONTROL
# Byte 0 (PC escribe pulsos; PLC puede escribir estado)
#  0.0 Start
#  0.1 Pause
#  0.2 Stop
#  0.3 RecipeUpdated
#  0.4 Running   (PLC)
#  0.5 Paused    (PLC)
#  0.6 Terminado (PLC)
CTRL_BYTE = 0
CTRL_START = 0
CTRL_PAUSE = 1
CTRL_STOP = 2
CTRL_RECIPE_UPDATED = 3
CTRL_RUNNING = 4
CTRL_PAUSED = 5
CTRL_TERMINADO = 6

# DB10 DB_RECETA — layout dummy (bytes, big-endian Siemens)
# Header 16 bytes:
#   0  INT  num_etapas
#   2  INT  version
#   4  REAL tiempo_global   (PLC)
#   8  REAL tiempo_etapa    (PLC)
#  12  INT  etapa_activa    (PLC)
#  14  INT  reserved
# Cada etapa: 160 bytes desde offset 16
#   0  REAL tiempo_total_sec
#   4  INT  paso
#   6  INT  reserved
#   8  9 celdas × 16 bytes:
#        0 INT mode (0=off, 1=continuo, 2=ciclo)
#        2 INT manual_is_open (0/1, solo continuo)
#        4 REAL t_shift
#        8 REAL t_open
#       12 REAL t_close
RECETA_HEADER_BYTES = 16
ETAPA_BYTES = 160
CELDA_EN_ETAPA_BYTES = 16
CELDA_DATOS_OFFSET = 8
MAX_ETAPAS = 20
RECETA_BYTES = RECETA_HEADER_BYTES + MAX_ETAPAS * ETAPA_BYTES

MODE_OFF = 0
MODE_CONTINUO = 1
MODE_CICLO = 2

# Red local: las UIs preguntan; el monitor responde al emisor
MONITOR_HOST = '127.0.0.1'
MONITOR_PUERTO = 25000

# Tiempos
# Motor/UI en PC: 20 Hz. Lectura/escritura Snap7 al PLC: 2 Hz (no saturar).
CICLO_MONITOR_S = 0.05
TIEMPO_MUESTREO_MS = 500
TIMEOUT_UI_S = 1.0
