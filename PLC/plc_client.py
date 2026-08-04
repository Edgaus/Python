# plc_client.py
import snap7
from snap7.util import set_real, get_real

class PLCDriver:
    def __init__(self, ip, rack, slot):
        self.client = snap7.client.Client()
        self.ip = ip
        self.rack = rack
        self.slot = slot

    def conectar(self):
        try:
            self.client.connect(self.ip, self.rack, self.slot)
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False

    def leer_temperatura(self, db_numero, offset):
        # Lógica cruda de Snap7 para leer un Real (Float)
        if self.client.get_connected():
            data = self.client.db_read(db_numero, offset, 4)
            return get_real(data, 0)
        return 0.0
    
    def escribir_receta(self, db_numero, datos):
        # Lógica para enviar tu receta cocinada al PLC
        pass