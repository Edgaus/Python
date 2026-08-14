# config.py
"""
Configuración del PLC Siemens y del muestreo de sensores.

Tu amigo (DB / monitoreo): aquí están la IP, rack/slot y los números de
Data Block (DB) que Snap7 usa. El periodo TIEMPO_MUESTREO_MS controla cada
cuánto plc_worker.py pregunta temperaturas al PLC — NO es el tick del
secuenciador de celdas (ese vive en monitor_247.py ~50 ms).
"""

# --- Conexión Snap7 al PLC ---
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1

# --- Data Blocks en el PLC ---
# DB_RECETA: donde se podría escribir la receta / órdenes de celdas.
# DB_SENSORES: lecturas (ej. temperatura Real en offset 0).
DB_RECETA = 10
DB_SENSORES = 11

# --- Muestreo de sensores (plc_worker.py) ---
# 200–500 ms es un rango típico y seguro para HMI Siemens.
# Si bajas mucho (<100 ms) aumentas carga de red sin mucho beneficio visual.
TIEMPO_MUESTREO_MS = 500  # Medio segundo para leer datos del PLC
