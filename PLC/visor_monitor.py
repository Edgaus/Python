import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import config
from monitor_client import MonitorCliente
from styles import MAIN_STYLE_SHEET


CELL_COLORS = {
    "Al": "#28aa5a",
    "Ga": "#3278dc",
    "In": "#ff9628",
    "N": "#9632dc",
    "As": "#dc3232",
    "Si": "#5a5a5a",
    "Be": "#b48c28",
    "Mn": "#8c5028",
    "Mg": "#50b4b4",
}


class VisorMonitorWindow(QMainWindow):
    """UI de solo lectura: pregunta a monitor_247 y pinta el estado de celdas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Celdas — Monitor 24/7")
        self.resize(980, 620)
        self.setStyleSheet(MAIN_STYLE_SHEET)

        self.cliente = MonitorCliente()
        self.monitor_online = False
        self.ultimo_contacto = time.time()
        self.cell_cards = {}

        self._build_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._tick_red)
        self.timer.start()
        self.cliente.pedir_estado()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Estado de celdas (fuente: monitor_247)")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #0d2a52;")
        layout.addWidget(titulo)

        self.lbl_conexion = QLabel("Buscando monitor 24/7...")
        self.lbl_conexion.setStyleSheet("font-size: 14px; font-weight: bold; color: #7f8c8d;")
        layout.addWidget(self.lbl_conexion)

        self.lbl_proceso = QLabel("Proceso: —")
        layout.addWidget(self.lbl_proceso)

        group = QGroupBox("Apertura / cierre en tiempo real")
        grid = QGridLayout(group)
        grid.setSpacing(12)

        for i, celda in enumerate(config.CELDAS):
            card = QFrame()
            card.setMinimumSize(130, 140)
            v = QVBoxLayout(card)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)

            color = CELL_COLORS.get(celda, "#7f8c8d")
            lbl_name = QLabel(f"Celda {celda}")
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_name.setStyleSheet(f"border: none; font-size: 16px; font-weight: bold; color: {color};")

            lbl_estado = QLabel("—")
            lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_estado.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            lbl_estado.setStyleSheet("border: none;")

            lbl_deseo = QLabel("deseada: —")
            lbl_deseo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_deseo.setStyleSheet("border: none; color: #7f8c8d; font-size: 12px;")

            v.addWidget(lbl_name)
            v.addWidget(lbl_estado)
            v.addWidget(lbl_deseo)

            grid.addWidget(card, i // 3, i % 3)
            self.cell_cards[celda] = {
                "frame": card,
                "estado": lbl_estado,
                "deseo": lbl_deseo,
            }

        layout.addWidget(group)

        self.lbl_detalle = QLabel("Etapa: —    Tiempo: —")
        self.lbl_detalle.setStyleSheet("color: #0d2a52; font-size: 14px;")
        layout.addWidget(self.lbl_detalle)
        layout.addStretch()

    def _tick_red(self):
        estado = self.cliente.recibir()
        if estado and estado.get("type") == "status":
            self.monitor_online = True
            self.ultimo_contacto = time.time()
            self._pintar(estado)
        elif time.time() - self.ultimo_contacto > config.TIMEOUT_UI_S:
            self.monitor_online = False
            self.lbl_conexion.setText("Monitor 24/7 no responde. Ejecuta monitor_247.py")
            self.lbl_conexion.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")

        self.cliente.pedir_estado()

    def _pintar(self, estado):
        modo = "simulación" if estado.get("modo_simulacion") else "PLC real"
        plc_ok = "conectado" if estado.get("plc_conectado") else "sin lectura"
        receta_plc = "receta en PLC" if estado.get("receta_en_plc") else "sin receta en PLC"
        self.lbl_conexion.setText(f"Monitor en línea · {modo} · {plc_ok} · {receta_plc}")
        self.lbl_conexion.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")

        if estado.get("is_running"):
            texto = "Proceso: PAUSADO" if estado.get("is_paused") else "Proceso: EN MARCHA"
        else:
            texto = "Proceso: DETENIDO"
        self.lbl_proceso.setText(texto)

        receta = estado.get("receta_actual") or []
        res = estado.get("resultados_motor") or {}
        idx = res.get("indice_etapa", 0)
        material = "—"
        if receta and 0 <= idx < len(receta) and not res.get("terminado", True):
            material = receta[idx].get("material", "—")

        t_etapa = float(res.get("tiempo_etapa_actual", 0.0))
        t_global = float(res.get("tiempo_global", 0.0))
        etapa_txt = f"{idx + 1} / {len(receta)}" if receta else "—"
        self.lbl_detalle.setText(
            f"Material: {material}    Etapa: {etapa_txt}    "
            f"Tiempo etapa: {t_etapa:.1f}s    Global: {t_global:.1f}s"
        )

        celdas = estado.get("celdas") or {}
        for nombre, widgets in self.cell_cards.items():
            info = celdas.get(nombre, {})
            abierta = bool(info.get("abierta", False))
            deseada = bool(info.get("deseada", False))
            coincide = info.get("coincide", abierta == deseada)

            color = "#27ae60" if abierta else "#e53935"
            widgets["estado"].setText("ABIERTA" if abierta else "CERRADA")
            widgets["estado"].setStyleSheet(f"border: none; color: {color}; font-size: 18px; font-weight: bold;")
            widgets["deseo"].setText(f"deseada: {'ABIERTA' if deseada else 'CERRADA'}")
            borde = color if coincide else "#f39c12"
            widgets["frame"].setStyleSheet(
                f"background: white; border: 3px solid {borde}; border-radius: 8px; padding: 8px;"
            )

    def closeEvent(self, event):
        self.timer.stop()
        self.cliente.cerrar()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VisorMonitorWindow()
    window.show()
    sys.exit(app.exec())
