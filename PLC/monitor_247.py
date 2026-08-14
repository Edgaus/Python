"""
monitor_247.py — Cerebro 4 + Cerebro 5 (el proceso que no se apaga)

Cerebro 4 = MotorSecuenciador: con la receta cargada, en cada tick calcula
  qué celdas (Ga/Al/In/As/N) deben estar ABIERTAS o CERRADAS.
Cerebro 5 = iniciar_servidor(): bucle UDP 24/7 que
  - escucha comandos en 127.0.0.1:5000  (load / start / pause / stop / update_recipe)
  - publica estado en 127.0.0.1:5001
  - escribe historial/historial_*.csv  ← fuente para la DB de monitoreo
  - (opcional) manda órdenes al PLC Siemens vía Snap7

Cómo probar solo:
  cd PLC && ../.venv/bin/python monitor_247.py

Para tu amigo (DB): mira el bloque "Guardar CSV On-The-Fly" más abajo.
Ahí sale cada muestra de apertura/cierre; ese es el sitio natural para un INSERT.
"""
import socket
import json
import time
import os
import csv
import datetime

# =========================================================================
# PREPARACIÓN PARA EL PLC (hoy comentado: sin hardware / sin libsnap7)
# =========================================================================
# import config
# from plc_worker import MonitorPLCWorker

# =========================================================================
# CEREBRO 4 — Secuenciador de la receta (decide abrir/cerrar)
# =========================================================================
class MotorSecuenciador:
    def __init__(self):
        self.receta = []
        self.tiempo_global = 0.0
        self.tiempo_etapa_actual = 0.0
        self.indice_etapa = 0
        self.estado_anterior_celdas = {}
        self.proceso_terminado = False

    def cargar_receta(self, datos_json):
        self.receta = datos_json
        self.reiniciar()

    def reiniciar(self):
        self.tiempo_global = 0.0
        self.tiempo_etapa_actual = 0.0
        self.indice_etapa = 0
        self.estado_anterior_celdas = {}
        self.proceso_terminado = False
        self._saltar_etapas_vacias()

    def modificar_receta(self, receta_actualizada):
        self.receta = receta_actualizada

    def _saltar_etapas_vacias(self):
        while self.indice_etapa < len(self.receta):
            paso = self.receta[self.indice_etapa]
            t_total = float(paso.get("tiempo_total_crecimiento_sec", 0.0))
            if t_total > 0:
                break
            self.indice_etapa += 1
        
        if self.indice_etapa >= len(self.receta):
            self.proceso_terminado = True

    def procesar_tick(self, delta_t):
        if self.proceso_terminado or not self.receta:
            return {"terminado": True, "comandos_plc_nuevos": {}, "estado_luces_ui": {}}

        self.tiempo_global += delta_t
        self.tiempo_etapa_actual += delta_t

        paso_actual = self.receta[self.indice_etapa]
        duracion_paso = float(paso_actual.get("tiempo_total_crecimiento_sec", 0.0))

        if self.tiempo_etapa_actual >= duracion_paso:
            self.tiempo_etapa_actual = 0.0
            self.indice_etapa += 1
            self._saltar_etapas_vacias()
            
            if self.proceso_terminado:
                cambios = {celda: False for celda in self.estado_anterior_celdas if self.estado_anterior_celdas[celda]}
                self.estado_anterior_celdas = {}
                return {"terminado": True, "comandos_plc_nuevos": cambios, "estado_luces_ui": {}}
            
            paso_actual = self.receta[self.indice_etapa]

        estado_actual = self._calcular_estado_celdas(paso_actual, self.tiempo_etapa_actual)
        cambios_hardware = self._detectar_cambios(estado_actual)
        self.estado_anterior_celdas = estado_actual

        return {
            "terminado": False,
            "indice_etapa": self.indice_etapa,
            "tiempo_etapa_actual": self.tiempo_etapa_actual,
            "tiempo_global": self.tiempo_global,
            "estado_luces_ui": estado_actual,
            "comandos_plc_nuevos": cambios_hardware
        }

    def _calcular_estado_celdas(self, paso, t_etapa):
        estado = {}
        celdas = paso.get("parametros_celdas", {})
        for el, params in celdas.items():
            mode = params.get("mode", "Continuo")
            if mode == "Continuo":
                estado[el] = params.get("manual_is_open", True)
            elif mode == "Ciclo":
                t_shift = float(params.get("t_shift", 0.0))
                t_open = float(params.get("t_open", 5.0))
                t_close = float(params.get("t_close", 5.0))
                period = t_shift + t_open + t_close
                if period > 0:
                    pos = t_etapa % period
                    estado[el] = (t_shift <= pos < (t_shift + t_open))
                else:
                    estado[el] = False
        return estado

    def _detectar_cambios(self, estado_actual):
        cambios = {}
        for celda, esta_abierta in estado_actual.items():
            if self.estado_anterior_celdas.get(celda) != esta_abierta:
                cambios[celda] = esta_abierta
        for celda, estaba_abierta in self.estado_anterior_celdas.items():
            if celda not in estado_actual and estaba_abierta:
                cambios[celda] = False
        return cambios

    def obtener_estado_estatico(self):
        if self.proceso_terminado or not self.receta or self.indice_etapa >= len(self.receta):
            return {}
        return self._calcular_estado_celdas(self.receta[self.indice_etapa], self.tiempo_etapa_actual)

# =========================================================================
# CEREBRO 5 — Servidor UDP 24/7 (no se apaga)
# =========================================================================
def iniciar_servidor():
    print("Iniciando Monitor 24/7 (Backend SCADA)...")
    motor = MotorSecuenciador()
    # hilo_plc = MonitorPLCWorker() # Descomentar para Snap7 / sensores

    # Configuración de Sockets UDP (comunicaciones locales UI ↔ cerebro)
    PUERTO_ESCUCHA = 5000  # Donde recibe órdenes del UI
    PUERTO_HMI = 5001      # A donde envía el estado al UI
    
    sock_escucha = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_escucha.bind(('127.0.0.1', PUERTO_ESCUCHA))
    sock_escucha.setblocking(False) # No detener el programa esperando mensajes

    sock_envio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    is_running = False
    is_paused = False
    historial_csv_file = None
    csv_writer = None

    tiempo_anterior = time.time()
    
    print(f"✅ Monitor activo y controlando el PLC. Escuchando en puerto {PUERTO_ESCUCHA}")

    while True:
        tiempo_actual = time.time()
        delta_t = tiempo_actual - tiempo_anterior
        tiempo_anterior = tiempo_actual

        # 1. ESCUCHAR SI EL MAIN.PY MANDÓ ALGUNA ORDEN
        try:
            data, addr = sock_escucha.recvfrom(65535)
            mensaje = json.loads(data.decode('utf-8'))
            comando = mensaje.get("cmd")

            if comando == "load":
                motor.cargar_receta(mensaje.get("recipe", []))
                is_running = False
                is_paused = False
                print("📂 Nueva receta cargada en el motor.")
            elif comando == "start":
                is_running = True
                is_paused = False
                print("▶ Iniciar proceso ordenado por UI.")
                
                # Crear archivo de log
                if not os.path.exists("historial"): os.makedirs("historial")
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                # buffering=1 (line-buffered) so UI4 (historial_vivo.py) can tail rows in real time
                historial_csv_file = open(
                    os.path.join("historial", f"historial_{timestamp}.csv"),
                    'w', newline='', encoding='utf-8', buffering=1
                )
                campos = ["Tiempo_Global(s)", "Ga", "Al", "In", "As", "N"]
                csv_writer = csv.DictWriter(historial_csv_file, fieldnames=campos)
                csv_writer.writeheader()
                historial_csv_file.flush()

            elif comando == "pause":
                is_paused = not is_paused
                print("⏸ Pausa alternada.")
            elif comando == "stop":
                is_running = False
                is_paused = False
                motor.reiniciar()
                if historial_csv_file: historial_csv_file.close()
                print("⏹ Proceso detenido.")
            elif comando == "update_recipe":
                motor.modificar_receta(mensaje.get("recipe", []))
                print("🔄 ¡Modificación en tiempo real inyectada!")

        except BlockingIOError:
            pass # No hay mensajes nuevos, seguimos adelante
        except Exception as e:
            print(f"Error procesando comando de UI: {e}")

        # 2. CALCULAR MOTOR Y MANDAR AL PLC
        if is_running and not is_paused:
            resultados = motor.procesar_tick(delta_t)
            estado_luces = resultados.get("estado_luces_ui", {})
            
            # Comunicar al PLC los cambios (Hardware real)
            for celda, debe_abrir in resultados.get("comandos_plc_nuevos", {}).items():
                print(f"📡 PLC COMANDO -> Celda {celda}: {'ABIERTO' if debe_abrir else 'CERRADO'}")
                # hilo_plc.escribir_motor(celda, debe_abrir)
            
            # -----------------------------------------------------------------
            # HISTORIAL / MONITOREO
            # Cada fila = un instante: Tiempo_Global(s), Ga, Al, In, As, N
            # con valores ABIERTA|CERRADA. Flush para UI4 y futuros importers a DB.
            # Si montas una tabla SQL, este es el punto ideal para INSERT además
            # (o en lugar) del CSV. Ver README.md sección "base de datos".
            # -----------------------------------------------------------------
            if csv_writer and historial_csv_file:
                log_entry = {"Tiempo_Global(s)": round(resultados.get("tiempo_global", 0), 1)}
                for el in ["Ga", "Al", "In", "As", "N"]:
                    log_entry[el] = "ABIERTA" if estado_luces.get(el, False) else "CERRADA"
                csv_writer.writerow(log_entry)
                historial_csv_file.flush()

            if resultados["terminado"]:
                is_running = False
                if historial_csv_file: historial_csv_file.close()
                print("✅ Proceso completado con éxito.")
        else:
            # Si estamos detenidos o pausados, calculamos la "foto" actual estática
            estado_luces = motor.obtener_estado_estatico()
            resultados = {
                "terminado": motor.proceso_terminado,
                "indice_etapa": motor.indice_etapa,
                "tiempo_etapa_actual": motor.tiempo_etapa_actual,
                "tiempo_global": motor.tiempo_global,
                "estado_luces_ui": estado_luces
            }

        # 3. ENVIAR REPORTE AL MAIN.PY
        paquete_estado = {
            "is_running": is_running,
            "is_paused": is_paused,
            "receta_actual": motor.receta,
            "resultados_motor": resultados
        }
        try:
            sock_envio.sendto(json.dumps(paquete_estado).encode('utf-8'), ('127.0.0.1', PUERTO_HMI))
        except Exception as e:
            pass # Ignoramos si el main no está abierto

        time.sleep(0.05) # Ejecutar 20 veces por segundo

if __name__ == "__main__":
    iniciar_servidor()