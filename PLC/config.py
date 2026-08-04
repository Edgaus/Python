# config.py
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1

# Direcciones de los DBs (Data Blocks)
DB_RECETA = 10
DB_SENSORES = 11

# Tiempos
TIEMPO_MUESTREO_MS = 500  # Medio segundo para leer datos sin usar sleep()