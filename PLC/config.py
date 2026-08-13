# config.py
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1

# Direcciones de los DBs (Data Blocks)
DB_RECETA = 10
DB_SENSORES = 11

# Tiempos
# 200 ms is safe for Siemens S7 Snap7 reads (typical HMI poll is 100–250 ms).
# Also fine if an Arduino sits as a bridge — this is only a sensor DB poll, not
# a write storm. The growth sequencer in monitor_247.py ticks separately at ~50 ms.
TIEMPO_MUESTREO_MS = 200