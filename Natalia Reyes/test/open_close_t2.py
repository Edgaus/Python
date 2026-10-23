"""
    CODIGO PRUEBA 1: APERTURA Y CIERRA DE PUERTAS
    Controlador para interactuar directamente con el PLC
    Archivos usados:
    plc_client.py -> Comunicacion Snap7 pura
    config.py -> Constantes de configuracion del proyecto
"""

import time
from plc_client import PLCDriver
import config

class PLCController:
    def __init__(self, ip=None, rack=None, slot=None, simular=False):
        # Tomamos los valores de config.py si no se pasan en el contructor (operador cortocircuito)
        self.ip = ip or config.PLC_IP
        self.rack = rack or config.RACK
        self.slot = slot or config.SLOT
        
        # Declaramos las celdas disponibles del
        self.cells = ["Ga", "Al", "In", "As", "N"]
        
        # Inicializamos la comunicación del PLC (de plc_client.py)
        self.plc = PLCDriver(self.ip, self.rack, self.slot, simular=simular)
        
        # Estado local de la terminal
        self.cell_states = {cell: False for cell in self.cells}
    
    # Metodo para establecer conexion con el PLC
    def connect(self):
        print(f"Intentando conectar al PLC: {self.ip} (Rack: {self.rack}, Slot: {self.slot})...")
        if self.plc.conectar():
            print("Conexión exitosa")
            # Forzamos leer el estado real del PLC al iniciar
            self.readCellsState()
            return True
        else:
            print(f"Error en la conexión: {self.plc.ultimo_error}")
            return False
        
    # Metodo que se encarga de leer los bloques de celdas con el PLC
    def readCellsState(self):
        state = self.plc.leer_estado_celdas()
        if state is not None:
            for cell in self.cells:
                if cell in state:
                    self.cell_states[cell] = state[cell]
                    
    # Metodo que escribira estados de la celda
    def writeCellsState(self, cell_name, is_open):
        if cell_name not in self.cells:
            print(f"Error: La celda '{cell_name}' no existe.")
            return False

        # Escribimos directo al DB de Snap7
        success = self.plc.escribir_celda(cell_name, is_open)
        
        if success:
            self.cell_states[cell_name] = is_open
            status = "ABIERTA" if is_open else "CERRADA"
            print(f"[Snap7 Success] Celda {cell_name} forzada a {status}")
            return True
        else:
            print(f"[Snap7 Error] Error escribiendo celda {cell_name}: {self.plc.ultimo_error}")
            return False
    
    # Metodo que cierra todas las celdas
    def close_all(self):
        print("\nCerrando todas las compuertas")
        for cell in self.cells:
            if self.cell_states[cell]:
                self.writeCellsState(cell, False)
                
# En caso de que estemos ejecutamos este archivo como principal
if __name__ == "__main__":
    # IMPORTANTE: Cambia a simular=False si tienes el PLC conectado en la misma red
    controller = PLCController(simular=True)
    
    if controller.connect():
        while True:
            print("  CONTROLADOR PLC  ")
            
            for idx, cell in enumerate(controller.cells):
                state_str = "ABIERTA" if controller.cell_states[cell] else "CERRADA"
                print(f"{idx + 1}. {cell} - Status: [{state_str}]")
            
            print("-" * 50)
            print("R. Refrescar estado desde el PLC")
            print("0. Cerrar todas las compuertas y Salir")
            print("=" * 50)

            option = input("Selecciona el número de compuerta a alternar (o 0 para salir): ").strip().upper()

            if option == '0':
                controller.close_all()
                print("Desconectando y saliendo...")
                break
            elif option == 'R':
                print("Sincronizando con hardware...")
                controller.readCellsState()
                continue
            
            try:
                option_int = int(option)
                if 1 <= option_int <= len(controller.cells):
                    selected_cell = controller.cells[option_int - 1]
                    new_state = not controller.cell_states[selected_cell]
                    controller.writeCellsState(selected_cell, new_state)
                else:
                    print("\n[!] Opción inválida. Intenta de nuevo.")
            except ValueError:
                print("\n[!] Por favor, ingresa un número o comando válido.")
    else:
        print("No se pudo iniciar el panel de control.")