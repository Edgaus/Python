# plc_worker.py
"""
Hilo Qt que sondea el PLC en segundo plano (sensores).

Corre aparte de la UI para no congelar botones/animaciones.
Emite señales PyQt:
  - datos_actualizados(float): nueva temperatura (u otro sensor)
  - error_conexion(str): falló el connect

Hoy NO está cableado al bucle de monitor_247.py (está comentado allí).
Cuando se reactive, este hilo alimenta lecturas periódicas; la apertura
de celdas sigue saliendo del MotorSecuenciador, no de aquí.
"""
from PyQt6.QtCore import QThread, pyqtSignal
from plc_client import PLCDriver
import config
import time


class MonitorPLCWorker(QThread):
    # "Megáfonos" hacia quien conecte estas señales (UI u otro consumidor)
    datos_actualizados = pyqtSignal(float)
    error_conexion = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.corriendo = True
        self.plc = PLCDriver(config.PLC_IP, config.RACK, config.SLOT)

    def run(self):
        """Bucle de muestreo. Vive en otro hilo: aquí SÍ se puede sleep."""
        if not self.plc.conectar():
            self.error_conexion.emit("Fallo al conectar con el PLC")
            return

        while self.corriendo:
            # Lectura de ejemplo: Real en DB_SENSORES offset 0
            temp = self.plc.leer_temperatura(config.DB_SENSORES, 0)
            self.datos_actualizados.emit(temp)
            time.sleep(config.TIEMPO_MUESTREO_MS / 1000.0)

    def detener(self):
        """Pide salida limpia del bucle (el hilo termina en el próximo ciclo)."""
        self.corriendo = False
