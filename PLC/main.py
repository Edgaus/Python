import sys
import json
import subprocess
import os
import copy
import csv
import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, 
                             QProgressBar, QFileDialog, QMessageBox, QFrame,
                             QGridLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

# =========================================================================
# PREPARACIÓN PARA EL PLC (Descomentar cuando tengas los archivos listos)
# ==========================================
# import config
# from plc_worker import MonitorPLCWorker

# =========================================================================
# HOJA DE ESTILOS GENERAL
# =========================================================================
MAIN_STYLE_SHEET = """
QMainWindow { background: #dbe9f6; }
QWidget { color: #000000; }
QLabel { font-size: 14px; color: #000000; }
QGroupBox {
    background: white; border: 1px solid #a0a0a0; border-radius: 8px;
    margin-top: 15px; font-size: 15px; font-weight: bold; color: #0d2a52;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #0d2a52; }
QProgressBar {
    border: 1px solid #7f8c8d; border-radius: 4px; text-align: center;
    color: #000000; font-weight: bold; background-color: #ecf0f1; height: 18px;
}
QProgressBar::chunk { background-color: #3498db; border-radius: 3px; }
QMessageBox, QDialog { background-color: #ffffff !important; }
QMessageBox QLabel, QDialog QLabel { color: #000000 !important; font-size: 14px; font-weight: normal; }
QMessageBox QPushButton {
    background-color: #0d2a52; color: #ffffff !important; border: none;
    border-radius: 5px; padding: 6px 16px; font-size: 13px; font-weight: bold; min-width: 70px;
}
QMessageBox QPushButton:hover { background-color: #204a87; }
QDoubleSpinBox, QSpinBox, QDoubleSpinBox QLineEdit, QSpinBox QLineEdit {
    background-color: #ffffff; color: #000000 !important; border: 1px solid #a0a0a0;
    border-radius: 4px; padding: 2px 18px 2px 4px; font-size: 13px; font-weight: bold;
    min-width: 65px; min-height: 24px;
}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 15px; background-color: #e0e0e0; border-left: 1px solid #a0a0a0; }
QDoubleSpinBox::up-button { border-bottom: 1px solid #a0a0a0; border-top-right-radius: 3px; }
QDoubleSpinBox::down-button { border-bottom-right-radius: 3px; }
QDoubleSpinBox::up-arrow { width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 4px solid #000000; }
QDoubleSpinBox::down-arrow { width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid #000000; }
"""


# =========================================================================
# EL MOTOR SECUENCIADOR 
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
        """Permite cambiar los parámetros al vuelo desde la UI"""
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
        """Avanza el tiempo, calcula los ciclos y detecta cambios para el PLC"""
        if self.proceso_terminado or not self.receta:
            return {"terminado": True}

        self.tiempo_global += delta_t
        self.tiempo_etapa_actual += delta_t

        paso_actual = self.receta[self.indice_etapa]
        duracion_paso = float(paso_actual.get("tiempo_total_crecimiento_sec", 0.0))

        # Verificar si brincamos a la siguiente capa
        if self.tiempo_etapa_actual >= duracion_paso:
            self.tiempo_etapa_actual = 0.0
            self.indice_etapa += 1
            self._saltar_etapas_vacias()
            
            if self.proceso_terminado:
                # Si se acabó, mandar orden de apagar TODO al PLC
                cambios = {celda: False for celda in self.estado_anterior_celdas if self.estado_anterior_celdas[celda]}
                self.estado_anterior_celdas = {}
                return {"terminado": True, "comandos_plc_nuevos": cambios, "estado_luces_ui": {}}
            
            paso_actual = self.receta[self.indice_etapa]

        # 1. Calcular cómo deberían estar las celdas en este milisegundo exacto
        estado_actual = self._calcular_estado_celdas(paso_actual, self.tiempo_etapa_actual)
        
        # 2. Detectar si hubo algún cambio físico respecto al ciclo anterior
        cambios_hardware = self._detectar_cambios(estado_actual)
        
        # 3. Guardar el historial para el próximo ciclo
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
        # Celdas que cambiaron su estado actual (ej. de Abierto a Cerrado)
        for celda, esta_abierta in estado_actual.items():
            if self.estado_anterior_celdas.get(celda) != esta_abierta:
                cambios[celda] = esta_abierta
                
        # Celdas que desaparecieron en esta nueva etapa (se apagaron)
        for celda, estaba_abierta in self.estado_anterior_celdas.items():
            if celda not in estado_actual and estaba_abierta:
                cambios[celda] = False
        return cambios

    def obtener_estado_estatico(self):
        """Solo para UI: devuelve la foto de las celdas estando en Pausa o Stop"""
        if self.proceso_terminado or not self.receta or self.indice_etapa >= len(self.receta):
            return {}
        return self._calcular_estado_celdas(self.receta[self.indice_etapa], self.tiempo_etapa_actual)







# =========================================================================
# WIDGET GRÁFICO DE LÍNEA DE TIEMPO 
# =========================================================================
class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.recipe_data = None
        self.global_time = 0.0
        self.total_recipe_time = 1.0
        
        self.active_cells = {}
        
        self.element_colors = {
            "Ga": QColor(50, 120, 220),
            "Al": QColor(40, 170, 90),
            "In": QColor(255, 150, 40),
            "As": QColor(220, 50, 50),
            "N":  QColor(150, 50, 220)
        }

    def format_time_label(self, seconds):
        if self.total_recipe_time < 120: return f"{seconds:.1f}s"
        elif self.total_recipe_time < 7200: return f"{seconds/60:.1f}m"
        else: return f"{seconds/3600:.1f}h"

    def set_recipe_data(self, recipe_data, global_time):
        self.recipe_data = recipe_data
        self.global_time = global_time
        if self.recipe_data:
            self.total_recipe_time = max(1.0, sum(float(s.get("tiempo_total_crecimiento_sec", 0)) for s in self.recipe_data))
        else:
            self.total_recipe_time = 1.0
        self.update()

    def set_active_cells(self, active_dict):
        self.active_cells = active_dict
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        p.fillRect(rect, QColor(245, 245, 245))

        left = 90
        right = rect.width() - 40
        top = 40
        bottom = rect.height() - 40
        width = right - left
        draw_h = bottom - top

        p.setPen(QPen(Qt.GlobalColor.black, 2))
        p.drawRect(left, top, width, draw_h)

        if not self.recipe_data:
            p.setPen(QPen(QColor("#7f8c8d")))
            p.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            p.drawText(QRectF(left, top, width, draw_h), Qt.AlignmentFlag.AlignCenter, 
                       "Cargue una receta para visualizar la secuencia completa")
            return

        all_cells = set()
        for step in self.recipe_data:
            for cell in step.get("parametros_celdas", {}):
                all_cells.add(cell)
        all_cells = sorted(list(all_cells))

        num_cells = len(all_cells)
        if num_cells == 0: return

        row_h = draw_h / num_cells
        font = QFont("Arial", 11, QFont.Weight.Bold)
        p.setFont(font)

        # Rejilla de tiempo
        p.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))
        num_ticks = 5
        for i in range(num_ticks + 1):
            x_pos = left + (i / num_ticks) * width
            t_val = (i / num_ticks) * self.total_recipe_time
            p.drawLine(int(x_pos), top, int(x_pos), bottom)
            p.setPen(QPen(Qt.GlobalColor.black))
            p.setFont(QFont("Arial", 9))
            p.drawText(int(x_pos) - 20, bottom + 15, 40, 15, Qt.AlignmentFlag.AlignCenter, self.format_time_label(t_val))
            p.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))

        playhead_x = left + (min(self.global_time, self.total_recipe_time) / self.total_recipe_time) * width

        y_cursor = top
        for cell_name in all_cells:
            is_active_now = self.active_cells.get(cell_name, False)
            
            if is_active_now:
                p.setPen(QPen(QColor("#27ae60")))
                p.setFont(QFont("Arial", 11, QFont.Weight.ExtraBold))
                p.drawText(15, int(y_cursor + row_h/2 + 5), f"▶ {cell_name} (ON)")
            else:
                p.setPen(QPen(Qt.GlobalColor.black))
                p.setFont(font)
                p.drawText(15, int(y_cursor + row_h/2 + 5), f"Celda {cell_name}")

            color = self.element_colors.get(cell_name, QColor(100, 100, 100))
            bar_y = y_cursor + row_h * 0.3
            bar_h = row_h * 0.4

            def draw_trail_glow(start_x, end_x):
                if playhead_x > start_x:
                    glow_end = min(end_x, playhead_x)
                    glow_color = QColor(color)
                    glow_color.setAlpha(90)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(glow_color))
                    p.drawRect(QRectF(start_x, y_cursor + 2, glow_end - start_x, row_h - 4))

            current_start_t = 0.0
            
            for step in self.recipe_data:
                step_duration = float(step.get("tiempo_total_crecimiento_sec", 0))
                
                if step_duration > 0 and cell_name in step.get("parametros_celdas", {}):
                    el_params = step["parametros_celdas"][cell_name]
                    mode = el_params.get("mode", "Continuo")
                    
                    x_start = left + (current_start_t / self.total_recipe_time) * width
                    
                    if mode == "Continuo":
                        block_w = (step_duration / self.total_recipe_time) * width
                        x_end = x_start + block_w
                        p.fillRect(QRectF(x_start, bar_y, block_w, bar_h), color)
                        p.setPen(Qt.GlobalColor.black)
                        p.drawRect(QRectF(x_start, bar_y, block_w, bar_h))
                        draw_trail_glow(x_start, x_end)
                    else:
                        block_w = (step_duration / self.total_recipe_time) * width
                        p.fillRect(QRectF(x_start, bar_y, block_w, bar_h), QColor(220, 220, 220))
                        
                        t_shift = float(el_params.get("t_shift", 0.0))
                        t_open = float(el_params.get("t_open", 5.0))
                        t_close = float(el_params.get("t_close", 5.0))
                        period = t_shift + t_open + t_close
                        
                        if period > 0:
                            t_curr = 0.0
                            while t_curr < step_duration:
                                open_start = t_curr + t_shift
                                open_end = min(open_start + t_open, step_duration)
                                if open_start < step_duration:
                                    x1 = left + ((current_start_t + open_start) / self.total_recipe_time) * width
                                    x2 = left + ((current_start_t + open_end) / self.total_recipe_time) * width
                                    p.fillRect(QRectF(x1, bar_y, max(1.0, x2 - x1), bar_h), color)
                                    p.setPen(Qt.GlobalColor.black)
                                    p.drawRect(QRectF(x1, bar_y, max(1.0, x2 - x1), bar_h))
                                    draw_trail_glow(x1, x2)
                                t_curr += period

                current_start_t += step_duration

            if self.total_recipe_time > 0 and is_active_now:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(color))
                p.drawEllipse(QRectF(playhead_x - 6, bar_y + bar_h/2 - 6, 12, 12))

            p.setPen(QPen(QColor(200, 200, 200)))
            p.drawLine(left, int(y_cursor + row_h), right, int(y_cursor + row_h))
            y_cursor += row_h

        if self.total_recipe_time > 0:
            p.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
            p.drawLine(int(playhead_x), top - 10, int(playhead_x), bottom + 10)
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.drawText(int(playhead_x) - 20, top - 15, "Ahora")



# =========================================================================
# VENTANA PRINCIPAL
# =========================================================================
class MainWindow(QMainWindow):
    def __init__(self, recipe_path=None):
        super().__init__()
        self.setWindowTitle("MBE Control - Monitor")
        self.resize(1350, 800)
        self.setStyleSheet(MAIN_STYLE_SHEET)

        # Inicializamos el Motor Secuenciador (El Cerebro)
        self.motor = MotorSecuenciador()
        self.recipe_data = []
        self.temp_step_data = None 
        
        self.is_running = False
        self.is_paused = False
        self.is_unlocked = False

        self.last_drawn_step_index = -1
        self.last_drawn_lock_state = None
        self.cell_widgets = {}
        self.history_log = []

        self.process_timer = QTimer(self)
        self.process_timer.setInterval(100)
        self.process_timer.timeout.connect(self.on_process_tick)

        # self.hilo_plc = MonitorPLCWorker() # Descomentar cuando tengas PLC

        self.buildUI()
        if recipe_path and os.path.exists(recipe_path):
            self.load_recipe_from_file(recipe_path)

    def buildUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # ---------------- Sidebar ----------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame#Sidebar { background: #0d2a52; color: white; }
            QFrame#Sidebar QPushButton { background: transparent; border: none; text-align: left; padding: 12px; color: white; font-size: 15px; font-weight: bold; }
            QFrame#Sidebar QPushButton:hover { background: #204a87; border-left: 4px solid #3498db; }
            QFrame#Sidebar QLabel { color: white; }
        """)

        sideLayout = QVBoxLayout(sidebar)
        sideLayout.setContentsMargins(15, 20, 15, 20)
        title = QLabel("MBE CONTROL")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 20px;")
        sideLayout.addWidget(title)


        for txt in ["Cocinar 🛠️", "Recetas 📁", "Historial 📁"]:
            btn = QPushButton(txt)
            sideLayout.addWidget(btn)

        sideLayout.addStretch()
        layout.addWidget(sidebar)

        # ---------------- Panel principal ----------------
        right_panel = QWidget()
        main_layout = QVBoxLayout(right_panel)
        main_layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Programa de crecimiento")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #0d2a52;")
        main_layout.addWidget(titulo)

        self.timeline = TimelineWidget()
        main_layout.addWidget(self.timeline)

        botones = QHBoxLayout()


        self.btn_unlock = QPushButton("🔒 Bloqueado")
        self.btn_unlock.setStyleSheet("""
            QPushButton { background: #e74c3c; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; }
            QPushButton:hover { background: #c0392b; }
        """)
        self.btn_unlock.clicked.connect(self.toggle_unlock_mode)

        self.btn_confirm = QPushButton("✔️ Confirmar Cambios")
        self.btn_confirm.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; }
            QPushButton:hover { background: #2980b9; }
        """)
        self.btn_confirm.setVisible(False)
        self.btn_confirm.clicked.connect(self.apply_pending_changes)

        botones.addWidget(self.btn_load)
        botones.addWidget(self.btn_builder)
        botones.addWidget(self.btn_unlock)
        botones.addWidget(self.btn_confirm)
        botones.addStretch()

        btn_style_big = "QPushButton { color: white; font-size: 18px; font-weight: bold; border-radius: 15px; border: none; }"
        
        self.btn_start = QPushButton("▶ INICIAR")
        self.btn_start.setFixedSize(140, 55)
        self.btn_start.setStyleSheet(btn_style_big + "QPushButton { background: #27ae60; } QPushButton:hover { background: #2ecc71; }")
        self.btn_start.clicked.connect(self.start_growth)

        self.btn_pause = QPushButton("⏸ PAUSAR")
        self.btn_pause.setFixedSize(140, 55)
        self.btn_pause.setStyleSheet(btn_style_big + "QPushButton { background: #f39c12; } QPushButton:hover { background: #f1c40f; }")
        self.btn_pause.setVisible(False)  
        self.btn_pause.clicked.connect(self.pause_growth)

        self.btn_stop = QPushButton("⏹ DETENER")
        self.btn_stop.setFixedSize(140, 55)
        self.btn_stop.setStyleSheet(btn_style_big + "QPushButton { background: #e53935; } QPushButton:hover { background: #ef5350; }")
        self.btn_stop.setVisible(False) 
        self.btn_stop.clicked.connect(self.stop_growth)

        botones.addWidget(self.btn_start)
        botones.addWidget(self.btn_pause)
        botones.addWidget(self.btn_stop)
        main_layout.addLayout(botones)

        group = QGroupBox("Condiciones de la etapa")
        self.grid = QGridLayout(group)
        self.grid.setVerticalSpacing(15)
        self.grid.setHorizontalSpacing(20)

        self.lbl_material = QLabel("<b>Material:</b> Ninguno")
        self.lbl_step = QLabel("<b>Etapa:</b> - / -")
        
        self.time_container = QWidget()
        self.time_layout = QHBoxLayout(self.time_container)
        self.time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_layout.setSpacing(4)

        self.lbl_time_cur = QLabel("<b>Tiempo:</b> 0.0s / ")
        self.lbl_time_total_static = QLabel("0.0s")
        self.spin_total_step_time = QDoubleSpinBox()
        self.spin_total_step_time.setRange(1.0, 99999.0)
        self.spin_total_step_time.setDecimals(1)
        self.spin_total_step_time.setSuffix("s")
        self.spin_total_step_time.setVisible(False)
        self.spin_total_step_time.valueChanged.connect(self.on_step_total_time_changed)

        self.time_layout.addWidget(self.lbl_time_cur)
        self.time_layout.addWidget(self.lbl_time_total_static)
        self.time_layout.addWidget(self.spin_total_step_time)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(300)

        self.grid.addWidget(self.lbl_material, 0, 0)
        self.grid.addWidget(self.lbl_step, 0, 1)
        self.grid.addWidget(self.time_container, 0, 2)
        self.grid.addWidget(self.progress_bar, 0, 3)

        self.lbl_comment = QLabel("<b>Comentario:</b> <i>Ninguno</i>")
        self.lbl_comment.setStyleSheet("color: #0d2a52; font-size: 14px; font-style: italic;")
        self.grid.addWidget(self.lbl_comment, 1, 0, 1, 4)

        self.cells_widget = QWidget()
        self.cells_layout = QHBoxLayout(self.cells_widget)
        self.cells_layout.setContentsMargins(0, 0, 0, 0)
        self.grid.addWidget(self.cells_widget, 2, 0, 1, 4)

        main_layout.addWidget(group)
        layout.addWidget(right_panel)

    def normalize_step(self, step):
        material = step.get("material") or step.get("name") or "Desconocido"
        if "tiempo_total_crecimiento_sec" in step:
            growth_time = float(step["tiempo_total_crecimiento_sec"])
        elif "growth_time" in step:
            growth_time = float(step["growth_time"])
        else:
            growth_time = 0.0 if ("Substrate" in material or step.get("is_substrate", False)) else 60.0
            
        comment = step.get("comentario", step.get("comment", ""))
        raw_cells = step.get("parametros_celdas") or step.get("element_data") or {}
        
        normalized_cells = {}
        for el, p in raw_cells.items():
            mode = p.get("mode", "Continuo")
            normalized_cells[el] = {
                "mode": mode,
                "t_shift": float(p.get("t_shift", 0.0)),
                "t_open": float(p.get("t_open", 5.0)),
                "t_close": float(p.get("t_close", 5.0)),
                "manual_is_open": p.get("manual_is_open", True)
            }
            
        return {
            "material": material,
            "tiempo_total_crecimiento_sec": growth_time,
            "comentario": comment,
            "parametros_celdas": normalized_cells
        }

    def toggle_unlock_mode(self):
        self.is_unlocked = not self.is_unlocked
        if self.is_unlocked:
            if self.recipe_data and not self.motor.proceso_terminado:
                self.temp_step_data = copy.deepcopy(self.recipe_data[self.motor.indice_etapa])
            else:
                self.temp_step_data = None

            self.btn_unlock.setText("🔓 Modo Edición")
            self.btn_unlock.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; } QPushButton:hover { background: #2ecc71; }")
            self.btn_confirm.setVisible(True)
            self.lbl_time_total_static.setVisible(False)
            self.spin_total_step_time.setVisible(True)
        else:
            self.temp_step_data = None
            self.btn_unlock.setText("🔒 Bloqueado")
            self.btn_unlock.setStyleSheet("QPushButton { background: #e74c3c; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; } QPushButton:hover { background: #c0392b; }")
            self.btn_confirm.setVisible(False)
            self.lbl_time_total_static.setVisible(True)
            self.spin_total_step_time.setVisible(False)
        
        self.update_step_display()

    def on_step_total_time_changed(self, new_val):
        if self.temp_step_data:
            self.temp_step_data["tiempo_total_crecimiento_sec"] = float(new_val)

    def apply_pending_changes(self):
        if self.is_unlocked and self.temp_step_data and self.recipe_data:
            # 1. Inyectamos los cambios a la receta oficial
            self.recipe_data[self.motor.indice_etapa] = copy.deepcopy(self.temp_step_data)
            
            # 2. Le avisamos al Motor Secuenciador para que se recálcule
            self.motor.modificar_receta(self.recipe_data)
            
            # 3. Refrescamos todo visualmente
            self.last_drawn_step_index = -1 # Forzamos redibujo de celdas
            self.update_step_display()
            QMessageBox.information(self, "Éxito", "Los cambios han sido inyectados en el Motor Secuenciador.")

    def select_recipe_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Cargar Receta MBE", "", "Archivos JSON (*.json)")
        if file_path:
            self.load_recipe_from_file(file_path)

    def load_recipe_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            if not isinstance(raw_data, list) or len(raw_data) == 0:
                QMessageBox.warning(self, "Advertencia", "El archivo no contiene una receta válida.")
                return

            self.recipe_data = [self.normalize_step(s) for s in raw_data]
            
            # Enviamos la receta al Cerebro (Motor)
            self.motor.cargar_receta(self.recipe_data)
            self.last_drawn_step_index = -1
            
            self.update_step_display()
            QMessageBox.information(self, "Éxito", f"Receta '{os.path.basename(file_path)}' cargada correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo JSON:\n{e}")

    def update_step_display(self, estado_luces_ui=None):
        if not self.recipe_data or self.motor.proceso_terminado:
            self.lbl_material.setText("<b>Material:</b> Finalizado")
            self.lbl_step.setText("<b>Etapa:</b> - / -")
            self.lbl_time_cur.setText("<b>Tiempo:</b> 0.0s / ")
            self.lbl_time_total_static.setText("0.0s")
            self.lbl_comment.setText("<b>Comentario:</b> <i>Proceso finalizado</i>")
            self.progress_bar.setValue(100)
            
            if self.recipe_data:
                total = sum(float(s.get("tiempo_total_crecimiento_sec", 0)) for s in self.recipe_data)
                self.timeline.set_recipe_data(self.recipe_data, total)
                
            self.refresh_cells_ui(None)
            return

        step = self.recipe_data[self.motor.indice_etapa]
        material = step.get("material", "Desconocido")
        total_time = float(step.get("tiempo_total_crecimiento_sec", 60.0))
        comentario = step.get("comentario", "")

        if self.is_unlocked and (self.temp_step_data is None or self.last_drawn_step_index != self.motor.indice_etapa):
            self.temp_step_data = copy.deepcopy(step)

        self.lbl_material.setText(f"<b>Material:</b> <font color='#0d2a52'>{material}</font>")
        self.lbl_step.setText(f"<b>Etapa:</b> {self.motor.indice_etapa + 1} de {len(self.recipe_data)}")
        self.lbl_time_cur.setText(f"<b>Tiempo:</b> {self.motor.tiempo_etapa_actual:.1f}s / ")
        self.lbl_time_total_static.setText(f"{total_time:.1f}s")

        if not self.is_unlocked:
            self.spin_total_step_time.blockSignals(True)
            self.spin_total_step_time.setValue(total_time)
            self.spin_total_step_time.blockSignals(False)
        
        if comentario.strip():
            self.lbl_comment.setText(f"<b>Comentario:</b> <i>{comentario}</i>")
        else:
            self.lbl_comment.setText("<b>Comentario:</b> <i>Ninguno</i>")
        
        pct = int((self.motor.tiempo_etapa_actual / total_time) * 100) if total_time > 0 else 100
        self.progress_bar.setValue(min(100, pct))
        
        self.timeline.set_recipe_data(self.recipe_data, self.motor.tiempo_global)
        
        # Si la UI lo pide estático (sin correr), calculamos una foto
        if estado_luces_ui is None:
            estado_luces_ui = self.motor.obtener_estado_estatico()
            
        self.refresh_cells_ui(step, estado_luces_ui)

    def refresh_cells_ui(self, step, active_states=None):
        if active_states is None: active_states = {}

        if not step:
            while self.cells_layout.count():
                item = self.cells_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.cell_widgets.clear()
            self.timeline.set_active_cells({}) 
            return

        if self.last_drawn_step_index != self.motor.indice_etapa or self.last_drawn_lock_state != self.is_unlocked:
            while self.cells_layout.count():
                item = self.cells_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.cell_widgets.clear()
            
            cells = step.get("parametros_celdas", {})
            if not cells:
                lbl = QLabel("<i>Sin celdas activas (Sustrato / Standby)</i>")
                lbl.setStyleSheet("color: #7f8c8d;")
                self.cells_layout.addWidget(lbl)
                self.cells_layout.addStretch()
            else:
                for el, params in cells.items():
                    mode = params.get("mode", "Continuo")
                    
                    frame = QFrame()
                    flayout = QVBoxLayout(frame)
                    flayout.setContentsMargins(10, 5, 10, 5)
                    
                    lbl_title = QLabel(f"<b>Celda {el}</b> ({mode})")
                    lbl_title.setStyleSheet("border: none; font-size: 13px;")
                    
                    lbl_status = QLabel("---")
                    lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    flayout.addWidget(lbl_title)
                    flayout.addWidget(lbl_status)
                    
                    widget_refs = {"frame": frame, "status_lbl": lbl_status}

                    if self.is_unlocked:
                        if mode == "Continuo":
                            btn_toggle = QPushButton()
                            btn_toggle.setStyleSheet("border: none;")
                            
                            def make_toggle(cell_key):
                                def toggle():
                                    if self.temp_step_data:
                                        current = self.temp_step_data["parametros_celdas"][cell_key].get("manual_is_open", True)
                                        self.temp_step_data["parametros_celdas"][cell_key]["manual_is_open"] = not current
                                        btn = self.cell_widgets[cell_key]["toggle_btn"]
                                        if self.temp_step_data["parametros_celdas"][cell_key]["manual_is_open"]:
                                            btn.setText("🔴 Pendiente: Cerrar")
                                        else:
                                            btn.setText("🟢 Pendiente: Abrir")
                                        btn.setStyleSheet("background-color: #f39c12; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
                                return toggle
                                
                            btn_toggle.clicked.connect(make_toggle(el))
                            widget_refs["toggle_btn"] = btn_toggle
                            flayout.addWidget(btn_toggle)

                        elif mode == "Ciclo":
                            form_layout = QHBoxLayout()
                            form_layout.setContentsMargins(0, 0, 0, 0)
                            form_layout.setSpacing(4)
                            
                            spin_s = QDoubleSpinBox()
                            spin_s.setRange(0.0, 999.9)
                            spin_s.setDecimals(1)
                            spin_s.setValue(float(params.get("t_shift", 0.0)))
                            
                            spin_o = QDoubleSpinBox()
                            spin_o.setRange(0.0, 999.9)
                            spin_o.setDecimals(1)
                            spin_o.setValue(float(params.get("t_open", 5.0)))
                            
                            spin_c = QDoubleSpinBox()
                            spin_c.setRange(0.0, 999.9)
                            spin_c.setDecimals(1)
                            spin_c.setValue(float(params.get("t_close", 5.0)))

                            def make_callback(cell_key, param_key):
                                def on_val_changed(val):
                                    if self.temp_step_data:
                                        self.temp_step_data["parametros_celdas"][cell_key][param_key] = float(val)
                                return on_val_changed

                            spin_s.valueChanged.connect(make_callback(el, "t_shift"))
                            spin_o.valueChanged.connect(make_callback(el, "t_open"))
                            spin_c.valueChanged.connect(make_callback(el, "t_close"))

                            form_layout.addWidget(QLabel("S:"))
                            form_layout.addWidget(spin_s)
                            form_layout.addWidget(QLabel("O:"))
                            form_layout.addWidget(spin_o)
                            form_layout.addWidget(QLabel("C:"))
                            form_layout.addWidget(spin_c)
                            
                            flayout.addLayout(form_layout)
                    else:
                        if mode == "Ciclo":
                            t_shift = float(params.get("t_shift", 0.0))
                            t_open = float(params.get("t_open", 5.0))
                            t_close = float(params.get("t_close", 5.0))
                            lbl_times = QLabel(f"<span style='color: #7f8c8d; font-size: 11px;'>S: {t_shift:.1f}s | O: {t_open:.1f}s | C: {t_close:.1f}s</span>")
                            lbl_times.setStyleSheet("border: none;")
                            lbl_times.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            flayout.addWidget(lbl_times)
                            
                    self.cells_layout.addWidget(frame)
                    self.cell_widgets[el] = widget_refs

                self.cells_layout.addStretch()
                
            self.last_drawn_step_index = self.motor.indice_etapa
            self.last_drawn_lock_state = self.is_unlocked

        # Actualizamos la UI basada en la matemática que resolvió el Motor
        cells = step.get("parametros_celdas", {})
        for el, params in cells.items():
            if el not in self.cell_widgets: continue
            
            is_open = active_states.get(el, False)

            state_str = "ABIERTA" if is_open else "CERRADA"
            color_str = "#27ae60" if is_open else "#e53935"
            
            self.cell_widgets[el]["status_lbl"].setText(state_str)
            self.cell_widgets[el]["status_lbl"].setStyleSheet(f"border: none; color: {color_str}; font-size: 16px; font-weight: bold;")
            self.cell_widgets[el]["frame"].setStyleSheet(f"background: white; border: 2px solid {color_str}; border-radius: 6px; padding: 5px;")
            
            if "toggle_btn" in self.cell_widgets[el]:
                btn = self.cell_widgets[el]["toggle_btn"]
                intent_is_open = self.temp_step_data["parametros_celdas"][el].get("manual_is_open", True) if self.temp_step_data else is_open
                if "Pendiente" not in btn.text():
                    if intent_is_open:
                        btn.setText("🔴 Preparar Cierre")
                        btn.setStyleSheet("background-color: #e53935; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
                    else:
                        btn.setText("🟢 Preparar Apertura")
                        btn.setStyleSheet("background-color: #27ae60; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")

        self.timeline.set_active_cells(active_states)

    def start_growth(self):
        if not self.recipe_data:
            QMessageBox.warning(self, "Advertencia", "Por favor carga una receta JSON antes de iniciar.")
            return
        
        self.history_log = []
        self.is_running = True
        self.is_paused = False
        self.process_timer.start()
        
        # self.hilo_plc.start() # Descomentar para conectar a hardware

        self.btn_start.setVisible(False)
        self.btn_pause.setVisible(True)
        self.btn_stop.setVisible(True)
        self.btn_pause.setText("⏸ PAUSAR")

    def pause_growth(self):
        if self.is_paused:
            self.is_paused = False
            self.process_timer.start()
            self.btn_pause.setText("⏸ PAUSAR")
        else:
            self.is_paused = True
            self.process_timer.stop()
            self.btn_pause.setText("▶ REANUDAR")

    def stop_growth(self):
        self.process_timer.stop()
        self.is_running = False
        self.is_paused = False
        
        # self.hilo_plc.detener() # Descomentar para detener hardware

        self.btn_start.setVisible(True)
        self.btn_pause.setVisible(False)
        self.btn_stop.setVisible(False)
        self.btn_pause.setText("⏸ PAUSAR")

        self.exportar_historial_csv()
        self.motor.reiniciar()
        self.update_step_display()

    # =========================================================================
    # BUCLE PRINCIPAL 
    # =========================================================================
    def on_process_tick(self):
        if not self.is_running or self.is_paused: return

        # 1. El motor avanza 0.1s y hace toda la matemática pesada
        resultados = self.motor.procesar_tick(0.1)

        # 2. Si el motor dice que terminamos la receta, detenemos todo
        if resultados["terminado"]:
            self.stop_growth()
            # Si hay comandos para apagar las celdas al terminar:
            comandos_finales = resultados.get("comandos_plc_nuevos", {})
            for celda, debe_abrir in comandos_finales.items():
                print(f"📡 COMANDO PLC -> Celda {celda}: CERRADO (Fin de receta)")
            QMessageBox.information(self, "¡Proceso Completado!", "¡Todas las capas han finalizado! Se guardó un archivo CSV con el historial.")
            return

        # 3. Mandamos las órdenes detectadas por el Motor al PLC
        for celda, debe_abrir in resultados["comandos_plc_nuevos"].items():
            estado_txt = "ABIERTO" if debe_abrir else "CERRADO"
            print(f"📡 COMANDO PLC -> Celda {celda}: {estado_txt}")
            # self.hilo_plc.escribir_motor(celda, debe_abrir) # <- Tu conexión real a Snap7

        # 4. Guardado en Historial Log
        estado_ui = resultados["estado_luces_ui"]
        log_entry = {"Tiempo_Global(s)": round(resultados["tiempo_global"], 1)}
        for el in ["Ga", "Al", "In", "As", "N"]:
            log_entry[el] = "ABIERTA" if estado_ui.get(el, False) else "CERRADA"
        
        if not self.history_log or self.history_log[-1]["Tiempo_Global(s)"] != log_entry["Tiempo_Global(s)"]:
            self.history_log.append(log_entry)

        # 5. Actualizamos la pantalla con los nuevos resultados visuales
        self.update_step_display(estado_ui)

    def exportar_historial_csv(self):
        if not self.history_log: return
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"historial_crecimiento_{timestamp}.csv"
            keys = self.history_log[0].keys()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.history_log)
        except Exception as e:
            print(f"Error al guardar CSV: {e}")

    def launch_builder(self):
        try:
            subprocess.Popen([sys.executable, "builder.py"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir builder.py:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    recipe_arg = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(recipe_arg)
    window.show()
    sys.exit(app.exec())