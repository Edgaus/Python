# monitor_client.py
import json
import socket
import config


class MonitorCliente:
    """Cliente UDP para preguntar / ordenar al monitor 24/7.

    Cada UI abre su propio puerto efímero. El monitor responde al emisor,
    así main.py y visor_monitor.py pueden consultar a la vez.
    """

    def __init__(self, host=None, puerto=None):
        self.destino = (host or config.MONITOR_HOST, puerto or config.MONITOR_PUERTO)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((config.MONITOR_HOST, 0))
        self.sock.setblocking(False)

    def enviar(self, diccionario_comando):
        try:
            mensaje = json.dumps(diccionario_comando).encode("utf-8")
            self.sock.sendto(mensaje, self.destino)
            return True
        except Exception as e:
            print(f"Error enviando comando al Monitor: {e}")
            return False

    def pedir_estado(self):
        return self.enviar({"cmd": "get_status"})

    def recibir(self):
        """Devuelve el último paquete pendiente, o None si no hay respuesta."""
        ultimo = None
        try:
            while True:
                data, _ = self.sock.recvfrom(65535)
                ultimo = json.loads(data.decode("utf-8"))
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Error recibiendo datos del Monitor: {e}")
        return ultimo

    def cerrar(self):
        try:
            self.sock.close()
        except Exception:
            pass
