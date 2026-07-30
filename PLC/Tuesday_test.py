import snap7

# ==========================================
# 1. CONFIGURACIÓN DE RED
# ==========================================
IP_PLC = '192.168.0.1'  # ⚠️ CAMBIA ESTO por la IP real de tu PLC
RACK = 0
SLOT = 1

# Crear el cliente Snap7
plc = snap7.client.Client()

print(f"Intentando conectar al PLC en la IP: {IP_PLC}...")

try:
    # 2. Iniciar la conexión
    plc.connect(IP_PLC, RACK, SLOT)
    
    # Verificar si estamos conectados
    if plc.get_connected():
        print("✅ ¡ÉXITO! Conexión establecida con el PLC.")
        
        # ==========================================
        # 3. LECTURA DE PRUEBA (SOLO LECTURA)
        # ==========================================
        # Vamos a leer 1 solo byte del inicio (Offset 0) de tu DB
        NUMERO_DB = 1  # ⚠️ CAMBIA ESTO por el número de tu DB_PYTHON (ej. si es DB5, pon 5)
        BYTE_INICIAL = 0
        CANTIDAD_BYTES = 1
        
        try:
            # Leer el área de memoria
            datos_crudos = plc.db_read(NUMERO_DB, BYTE_INICIAL, CANTIDAD_BYTES)
            print(f"📘 Lectura exitosa del DB{NUMERO_DB}: {datos_crudos}")
            print("Tu PC y el PLC se están comunicando perfectamente.")
            
        except Exception as error_lectura:
            print("⚠️ Conectó al PLC, pero falló al leer el DB.")
            print("Verifica que:")
            print(f" 1. El DB {NUMERO_DB} exista en el PLC.")
            print(" 2. Le hayas quitado el 'Acceso optimizado al bloque'.")
            print(" 3. Hayas cargado (Download) los cambios al PLC.")
            print(f"Detalle del error: {error_lectura}")

    else:
        print("❌ Falló la conexión (el PLC rechazó la petición o está apagado).")

except Exception as e:
    print(f"❌ Error crítico de red: {e}")
    print("Verifica que:")
    print(" 1. Tu PC tenga una IP fija en el mismo rango (ej. 192.168.0.5).")
    print(" 2. El comando 'ping' hacia el PLC funcione en tu terminal.")
    print(" 3. El PLC tenga activado 'Permitir acceso vía PUT/GET'.")

finally:
    # 4. Cerrar la conexión (Buena práctica)
    if plc.get_connected():
        plc.disconnect()
        print("🔌 Desconectado de forma segura.")