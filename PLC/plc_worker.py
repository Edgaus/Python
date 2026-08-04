# plc_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
from plc_client import PLCDriver
import config
import time

class MonitorPLCWorker(QThread):
    # Definimos las "Señales" (Megáfonos) que enviarán datos a main.py
    datos_actualizados = pyqtSignal(float)
    error_conexion = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.corriendo = True
        self.plc = PLCDriver(config.PLC_IP, config.RACK, config.SLOT)

    def run(self):
        """Este método corre en un núcleo separado del procesador. No congela la UI."""
        if not self.plc.conectar():
            self.error_conexion.emit("Fallo al conectar con el PLC")
            return

        while self.corriendo:
            # Leemos del PLC usando nuestro driver
            temp = self.plc.leer_temperatura(config.DB_SENSORES, 0)
            
            # ¡EMITIMOS EL DATO A LA UI!
            self.datos_actualizados.emit(temp)
            
            # Aquí SÍ puedes usar sleep (o QThread.msleep) porque estás en un hilo 
            # secundario. Esto no detendrá tus animaciones ni botones en main.py.
            time.sleep(config.TIEMPO_MUESTREO_MS / 1000.0) 

    def detener(self):
        self.corriendo = False