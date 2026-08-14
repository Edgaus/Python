import socket
import json
import time
import os
import csv
import datetime

import config
from plc_client import PLCDriver


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


class VigilanteCeldas:
    """Vigila apertura/cierre real de celdas, aunque no haya UI ni receta activa."""

    def __init__(self, plc):
        self.plc = plc
        self.estado_real = {celda: False for celda in config.CELDAS}
        self.estado_deseado = {celda: False for celda in config.CELDAS}
        self.lectura_ok = False

    def actualizar_deseado(self, estado_parcial):
        for celda in config.CELDAS:
            self.estado_deseado[celda] = bool(estado_parcial.get(celda, False))

    def aplicar_comandos(self, cambios):
        for celda, debe_abrir in cambios.items():
            etiqueta = "ABIERTO" if debe_abrir else "CERRADO"
            print(f"📡 PLC COMANDO -> Celda {celda}: {etiqueta}")
            self.plc.escribir_celda(celda, debe_abrir)
            self.estado_deseado[celda] = bool(debe_abrir)

    def cerrar_todas(self):
        abiertas = {celda: False for celda, abierta in self.estado_real.items() if abierta}
        abiertas.update({celda: False for celda, abierta in self.estado_deseado.items() if abierta})
        if abiertas:
            self.aplicar_comandos(abiertas)
        self.actualizar_deseado({})

    def leer_hardware(self):
        leido = self.plc.leer_estado_celdas()
        if leido is None:
            self.lectura_ok = False
            return
        self.lectura_ok = True
        for celda in config.CELDAS:
            if celda in leido:
                self.estado_real[celda] = bool(leido[celda])

    def snapshot(self):
        return {
            celda: {
                "abierta": self.estado_real[celda],
                "deseada": self.estado_deseado[celda],
                "coincide": self.estado_real[celda] == self.estado_deseado[celda],
            }
            for celda in config.CELDAS
        }

    def luces_ui(self):
        return {celda: self.estado_real[celda] for celda in config.CELDAS}


class MonitorServidor:
    def __init__(self):
        self.motor = MotorSecuenciador()
        self.plc = PLCDriver(config.PLC_IP, config.RACK, config.SLOT)
        self.vigilante = VigilanteCeldas(self.plc)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind((config.MONITOR_HOST, config.MONITOR_PUERTO))
        except OSError as e:
            raise OSError(
                f"No se pudo abrir {config.MONITOR_HOST}:{config.MONITOR_PUERTO}. "
                f"Cambia MONITOR_PUERTO en config.py si el puerto está ocupado o reservado por Windows. ({e})"
            ) from e
        self.sock.setblocking(False)

        self.is_running = False
        self.is_paused = False
        self.historial_csv_file = None
        self.csv_writer = None
        self.resultados = self._resultados_idle()
        self._ultimo_muestreo = 0.0

    def _resultados_idle(self):
        return {
            "terminado": self.motor.proceso_terminado,
            "indice_etapa": self.motor.indice_etapa,
            "tiempo_etapa_actual": self.motor.tiempo_etapa_actual,
            "tiempo_global": self.motor.tiempo_global,
            "estado_luces_ui": {},
            "comandos_plc_nuevos": {},
        }

    def paquete_estado(self):
        resultados = dict(self.resultados)
        resultados["estado_luces_ui"] = self.vigilante.luces_ui()
        return {
            "type": "status",
            "plc_conectado": self.plc.esta_conectado() and self.vigilante.lectura_ok,
            "modo_simulacion": self.plc.simular,
            "error_plc": self.plc.ultimo_error,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "receta_actual": self.motor.receta,
            "resultados_motor": resultados,
            "celdas": self.vigilante.snapshot(),
            "receta_en_plc": self.plc.receta_enviada,
            "timestamp": time.time(),
        }

    def responder(self, addr):
        try:
            self.sock.sendto(json.dumps(self.paquete_estado()).encode("utf-8"), addr)
        except Exception:
            pass

    def _cerrar_csv(self):
        if self.historial_csv_file:
            try:
                self.historial_csv_file.close()
            except Exception:
                pass
            self.historial_csv_file = None
            self.csv_writer = None

    def _abrir_csv(self):
        self._cerrar_csv()
        if not os.path.exists("historial"):
            os.makedirs("historial")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = os.path.join("historial", f"historial_{timestamp}.csv")
        self.historial_csv_file = open(ruta, "w", newline="", encoding="utf-8")
        campos = ["Tiempo_Global(s)"] + list(config.CELDAS)
        self.csv_writer = csv.DictWriter(self.historial_csv_file, fieldnames=campos)
        self.csv_writer.writeheader()

    def procesar_comando(self, mensaje, addr):
        comando = mensaje.get("cmd")

        if comando == "get_status":
            self.responder(addr)
            return

        if comando == "load":
            receta = mensaje.get("recipe", [])
            self.motor.cargar_receta(receta)
            self.is_running = False
            self.is_paused = False
            self.plc.escribir_receta(receta)
            print("📂 Receta cargada en el motor y enviada al PLC (DB dummy).")
        elif comando == "start":
            if self.motor.receta:
                self.plc.escribir_receta(self.motor.receta)
            self.plc.pulso_control(config.CTRL_START)
            self.plc.escribir_pause(False)
            self.is_running = True
            self.is_paused = False
            print("▶ Start: receta en PLC + bandera Start. El PLC ejecuta los tiempos.")
            self._abrir_csv()
        elif comando == "pause":
            self.is_paused = not self.is_paused
            self.plc.escribir_pause(self.is_paused)
            print("⏸ Pausa alternada (bandera Pause al PLC).")
        elif comando == "stop":
            self.plc.pulso_control(config.CTRL_STOP)
            if self.plc.simular:
                self.vigilante.cerrar_todas()
            self.is_running = False
            self.is_paused = False
            self.motor.reiniciar()
            self._cerrar_csv()
            print("⏹ Stop enviado al PLC. En simulación se cierran celdas locales.")
        elif comando == "update_recipe":
            receta = mensaje.get("recipe", [])
            self.motor.modificar_receta(receta)
            self.plc.escribir_receta(receta)
            self.plc.pulso_control(config.CTRL_RECIPE_UPDATED)
            print("🔄 Receta actualizada en Python y reescrita en el PLC.")
        else:
            print(f"Comando desconocido: {comando}")

        self.responder(addr)

    def drenar_comandos(self):
        try:
            while True:
                data, addr = self.sock.recvfrom(65535)
                try:
                    mensaje = json.loads(data.decode("utf-8"))
                    self.procesar_comando(mensaje, addr)
                except Exception as e:
                    print(f"Error procesando comando de UI: {e}")
        except BlockingIOError:
            pass

    def _muestrear_plc_si_toca(self, ahora):
        periodo = config.TIEMPO_MUESTREO_MS / 1000.0
        if ahora - self._ultimo_muestreo < periodo:
            return
        self._ultimo_muestreo = ahora
        self.vigilante.leer_hardware()
        progreso = self.plc.leer_progreso_receta()
        if progreso and not self.plc.simular:
            self.resultados["tiempo_global"] = progreso.get("tiempo_global", self.resultados.get("tiempo_global", 0))
            self.resultados["tiempo_etapa_actual"] = progreso.get("tiempo_etapa", self.resultados.get("tiempo_etapa_actual", 0))
            self.resultados["indice_etapa"] = progreso.get("etapa_activa", self.resultados.get("indice_etapa", 0))

    def tick_proceso(self, delta_t, ahora):
        if self.is_running and not self.is_paused:
            self.resultados = self.motor.procesar_tick(delta_t)
            self.vigilante.actualizar_deseado(self.resultados.get("estado_luces_ui", {}))
            # Híbrido: en simulación Python mueve las celdas; en PLC real solo se supervisa.
            if self.plc.simular:
                self.vigilante.aplicar_comandos(self.resultados.get("comandos_plc_nuevos", {}))

            if self.csv_writer:
                log_entry = {"Tiempo_Global(s)": round(self.resultados.get("tiempo_global", 0), 1)}
                for el in config.CELDAS:
                    log_entry[el] = "ABIERTA" if self.vigilante.estado_real.get(el, False) else "CERRADA"
                self.csv_writer.writerow(log_entry)

            if self.resultados.get("terminado"):
                self.plc.pulso_control(config.CTRL_STOP)
                if self.plc.simular:
                    self.vigilante.cerrar_todas()
                self.is_running = False
                self._cerrar_csv()
                print("✅ Proceso completado con éxito.")
        else:
            estado_deseado = self.motor.obtener_estado_estatico() if self.is_paused else {}
            if not self.is_running:
                estado_deseado = {}
            self.vigilante.actualizar_deseado(estado_deseado)
            self.resultados = {
                "terminado": self.motor.proceso_terminado,
                "indice_etapa": self.motor.indice_etapa,
                "tiempo_etapa_actual": self.motor.tiempo_etapa_actual,
                "tiempo_global": self.motor.tiempo_global,
                "estado_luces_ui": estado_deseado,
                "comandos_plc_nuevos": {},
            }

        self._muestrear_plc_si_toca(ahora)

    def run(self):
        print("Iniciando Monitor 24/7 (híbrido: receta al PLC, supervisión en Python)...")
        if not self.plc.conectar():
            print("⚠ Sin PLC: el monitor sigue activo y responde consultas.")
        self.vigilante.leer_hardware()
        self._ultimo_muestreo = time.time()
        print(f"✅ Monitor escuchando en {config.MONITOR_HOST}:{config.MONITOR_PUERTO}")
        print(f"   Celdas dummy: {', '.join(config.CELDAS)}")
        print(f"   Snap7 cada {config.TIEMPO_MUESTREO_MS} ms (1 lectura de {config.CELDAS_BYTES} bytes).")
        print("   Las UIs preguntan con cmd=get_status.")

        tiempo_anterior = time.time()
        try:
            while True:
                ahora = time.time()
                delta_t = ahora - tiempo_anterior
                tiempo_anterior = ahora

                self.drenar_comandos()
                self.tick_proceso(delta_t, ahora)
                time.sleep(config.CICLO_MONITOR_S)
        except KeyboardInterrupt:
            print("\nMonitor detenido por teclado.")
        finally:
            self.vigilante.cerrar_todas()
            self._cerrar_csv()
            self.sock.close()


def iniciar_servidor():
    MonitorServidor().run()


if __name__ == "__main__":
    iniciar_servidor()
