# plc_client.py
"""
Driver bajo nivel hacia el PLC Siemens vía python-snap7.

Responsabilidad: conectar y leer/escribir bytes en Data Blocks.
NO decide cuándo abrir/cerrar celdas (eso es MotorSecuenciador en
monitor_247.py). Tampoco escribe la UI.

Estado actual: leer_temperatura está implementado; escribir_receta es un
esqueleto (pass) listo para completar cuando el mapa de DB esté definido.

Dependencia: python-snap7 + libsnap7 nativa en el sistema.
"""
import snap7
from snap7.util import set_real, get_real


class PLCDriver:
    """Cliente Snap7 delgado: un PLC = una instancia."""

    def __init__(self, ip, rack, slot):
        self.client = snap7.client.Client()
        self.ip = ip
        self.rack = rack
        self.slot = slot

    def conectar(self):
        """Abre la sesión TCP con el PLC. True si ok."""
        try:
            self.client.connect(self.ip, self.rack, self.slot)
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False

    def leer_temperatura(self, db_numero, offset):
        """
        Lee un REAL (float 4 bytes) desde DB `db_numero` en `offset`.
        Útil para sensores. Para monitoreo en DB SQL, estos valores irían
        a una tabla sensor_samples (aparte de apertura/cierre de celdas).
        """
        if self.client.get_connected():
            data = self.client.db_read(db_numero, offset, 4)
            return get_real(data, 0)
        return 0.0

    def escribir_receta(self, db_numero, datos):
        """
        TODO: mapear el dict de celdas / receta a bytes del DB_RECETA
        y hacer db_write. Hoy es intencional (pass) hasta fijar el layout.
        """
        pass
