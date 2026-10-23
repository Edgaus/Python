# plc_client.py
import struct
import config

try:
    import snap7
    from snap7.util import get_real, get_bool, set_bool, set_real, set_int, get_int
    SNAP7_DISPONIBLE = True
except ImportError:
    snap7 = None
    SNAP7_DISPONIBLE = False

    def set_real(buf, offset, value):
        buf[offset:offset + 4] = struct.pack(">f", float(value))

    def get_real(buf, offset):
        return struct.unpack(">f", bytes(buf[offset:offset + 4]))[0]

    def set_int(buf, offset, value):
        buf[offset:offset + 2] = struct.pack(">h", int(value))

    def get_int(buf, offset):
        return struct.unpack(">h", bytes(buf[offset:offset + 2]))[0]

    def get_bool(buf, byte_index, bit_index):
        return bool((buf[byte_index] >> bit_index) & 1)

    def set_bool(buf, byte_index, bit_index, value):
        if value:
            buf[byte_index] = buf[byte_index] | (1 << bit_index)
        else:
            buf[byte_index] = buf[byte_index] & ~(1 << bit_index)


def empaquetar_receta(receta):
    """Serializa el JSON de receta al layout dummy de DB_RECETA."""
    data = bytearray(config.RECETA_BYTES)
    etapas = list(receta or [])[: config.MAX_ETAPAS]
    set_int(data, 0, len(etapas))
    set_int(data, 2, 1)

    for i, paso in enumerate(etapas):
        base = config.RECETA_HEADER_BYTES + i * config.ETAPA_BYTES
        set_real(data, base, float(paso.get("tiempo_total_crecimiento_sec", 0.0)))
        set_int(data, base + 4, int(paso.get("paso", i + 1)))
        celdas = paso.get("parametros_celdas") or {}
        for j, nombre in enumerate(config.CELDAS):
            cbase = base + config.CELDA_DATOS_OFFSET + j * config.CELDA_EN_ETAPA_BYTES
            params = celdas.get(nombre)
            if not params:
                set_int(data, cbase, config.MODE_OFF)
                continue
            mode = params.get("mode", "Continuo")
            if mode == "Ciclo":
                set_int(data, cbase, config.MODE_CICLO)
            else:
                set_int(data, cbase, config.MODE_CONTINUO)
            set_int(data, cbase + 2, 1 if params.get("manual_is_open", True) else 0)
            set_real(data, cbase + 4, float(params.get("t_shift", 0.0)))
            set_real(data, cbase + 8, float(params.get("t_open", 5.0)))
            set_real(data, cbase + 12, float(params.get("t_close", 5.0)))
    return data


class PLCDriver:
    """Híbrido: receta + banderas al PLC; celdas se leen en bloque a baja frecuencia."""

    def __init__(self, ip, rack, slot, simular=None):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.simular = config.SIMULAR_PLC if simular is None else simular
        self.client = None
        self._estado_sim = {celda: False for celda in config.CELDAS}
        self._receta_sim = []
        self._control_sim = 0
        self.ultimo_error = None
        self.receta_enviada = False

        if not self.simular and SNAP7_DISPONIBLE:
            self.client = snap7.client.Client()

    def conectar(self):
        if self.simular:
            print("PLC en modo simulación híbrida: receta en memoria, sin Snap7.")
            return True
        if not SNAP7_DISPONIBLE:
            self.ultimo_error = "python-snap7 no está instalado"
            print(self.ultimo_error)
            return False
        try:
            self.client.connect(self.ip, self.rack, self.slot)
            self.ultimo_error = None
            return True
        except Exception as e:
            self.ultimo_error = str(e)
            print(f"Error conectando: {e}")
            return False

    def esta_conectado(self):
        if self.simular:
            return True
        if not self.client:
            return False
        try:
            return bool(self.client.get_connected())
        except Exception:
            return False

    def leer_temperatura(self, db_numero, offset):
        if self.simular:
            return 0.0
        if self.esta_conectado():
            data = self.client.db_read(db_numero, offset, 4)
            return get_real(data, 0)
        return 0.0

    def leer_estado_celdas(self):
        """Una sola lectura de 2 bytes para las 9 celdas."""
        if self.simular:
            return dict(self._estado_sim)
        if not self.esta_conectado():
            return None
        try:
            data = self.client.db_read(config.DB_CELDAS, 0, config.CELDAS_BYTES)
            estado = {}
            for celda, mapa in config.MAPA_CELDAS.items():
                estado[celda] = bool(get_bool(data, mapa["byte"], mapa["bit"]))
            self.ultimo_error = None
            return estado
        except Exception as e:
            self.ultimo_error = str(e)
            return None

    def escribir_celda(self, celda, abierta):
        """Solo simulación / cierre de emergencia. En híbrido real el PLC mueve las celdas."""
        abierta = bool(abierta)
        if celda not in config.CELDAS:
            return False
        if self.simular:
            self._estado_sim[celda] = abierta
            return True
        if not self.esta_conectado():
            return False
        try:
            mapa = config.MAPA_CELDAS[celda]
            data = bytearray(self.client.db_read(mapa["db"], 0, config.CELDAS_BYTES))
            set_bool(data, mapa["byte"], mapa["bit"], abierta)
            self.client.db_write(mapa["db"], 0, data)
            return True
        except Exception as e:
            self.ultimo_error = str(e)
            print(f"Error escribiendo celda {celda}: {e}")
            return False

    def escribir_receta(self, receta):
        payload = empaquetar_receta(receta)
        if self.simular:
            self._receta_sim = list(receta or [])
            self.receta_enviada = True
            print(f"Receta dummy enviada al PLC simulado ({len(self._receta_sim)} etapas, {len(payload)} bytes).")
            return True
        if not self.esta_conectado():
            return False
        try:
            self.client.db_write(config.DB_RECETA, 0, payload)
            self.receta_enviada = True
            self.ultimo_error = None
            print(f"Receta escrita en DB{config.DB_RECETA} ({len(payload)} bytes).")
            return True
        except Exception as e:
            self.ultimo_error = str(e)
            print(f"Error escribiendo receta: {e}")
            return False

    def pulso_control(self, bit):
        """Pone un bit de control y lo deja en 1 (el PLC puede limpiar pulsos)."""
        return self._escribir_control_bit(bit, True)

    def escribir_pause(self, pausado):
        return self._escribir_control_bit(config.CTRL_PAUSE, bool(pausado))

    def _escribir_control_bit(self, bit, valor):
        if self.simular:
            if valor:
                self._control_sim |= 1 << bit
            else:
                self._control_sim &= ~(1 << bit)
            return True
        if not self.esta_conectado():
            return False
        try:
            data = bytearray(self.client.db_read(config.DB_CONTROL, config.CTRL_BYTE, 1))
            set_bool(data, 0, bit, valor)
            self.client.db_write(config.DB_CONTROL, config.CTRL_BYTE, data)
            return True
        except Exception as e:
            self.ultimo_error = str(e)
            print(f"Error escribiendo control: {e}")
            return False

    def leer_control(self):
        if self.simular:
            return {
                "running": bool(self._control_sim & (1 << config.CTRL_RUNNING)),
                "paused": bool(self._control_sim & (1 << config.CTRL_PAUSED)),
                "terminado": bool(self._control_sim & (1 << config.CTRL_TERMINADO)),
            }
        if not self.esta_conectado():
            return None
        try:
            data = self.client.db_read(config.DB_CONTROL, config.CTRL_BYTE, 1)
            return {
                "running": bool(get_bool(data, 0, config.CTRL_RUNNING)),
                "paused": bool(get_bool(data, 0, config.CTRL_PAUSED)),
                "terminado": bool(get_bool(data, 0, config.CTRL_TERMINADO)),
            }
        except Exception as e:
            self.ultimo_error = str(e)
            return None

    def leer_progreso_receta(self):
        """Lee tiempos/etapa que el PLC escribe en el header de DB_RECETA."""
        if self.simular:
            return None
        if not self.esta_conectado():
            return None
        try:
            data = self.client.db_read(config.DB_RECETA, 0, config.RECETA_HEADER_BYTES)
            return {
                "num_etapas": get_int(data, 0),
                "tiempo_global": get_real(data, 4),
                "tiempo_etapa": get_real(data, 8),
                "etapa_activa": get_int(data, 12),
            }
        except Exception as e:
            self.ultimo_error = str(e)
            return None
