import sys
import json
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QMessageBox, QFrame, QScrollArea, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

# ==========================================
# WIDGET VISUAL DE LA LÍNEA DEL TIEMPO COMPLETA
# ==========================================
class MainTimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recipe_data = []
        self.current_time_sec = 0.0
        self.total_time_sec = 0.0
        self.setMinimumHeight(350)
        
    def set_recipe(self, recipe_data):
        self.recipe_data = recipe_data
        # Calcular el tiempo total sumando la duración de cada capa
        self.total_time_sec = sum(item.get("tiempo_total_crecimiento_sec", 0.0) for item in recipe_data)
        if self.total_time_sec == 0:
            self.total_time_sec = 1.0 # Evitar división por cero
        self.current_time_sec = 0.0
        self.update()

    def set_current_time(self, current_time):
        self.current_time_sec = current_time
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Fondo oscuro elegante
        painter.setBrush(QBrush(QColor("#1e1e1e")))
        painter.drawRect(0, 0, width, height)

        if not self.recipe_data:
            painter.setPen(QPen(QColor("#7f8c8d")))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(QRectF(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, 
                             "Sin receta cargada. Haz clic en 'Diseñar Receta' o 'Cargar JSON'.")
            return

        margin_left = 120
        margin_right = 50
        margin_top = 60
        draw_width = width - margin_left - margin_right

        # 1. Dibujar regla de tiempo (Time Ruler)
        painter.setPen(QPen(QColor("#bdc3c7"), 1))
        painter.setFont(QFont("Arial", 9))
        painter.drawLine(margin_left, margin_top, margin_left + draw_width, margin_top)

        num_ticks = 10
        for i in range(num_ticks + 1):
            t_val = (self.total_time_sec / num_ticks) * i
            x_pos = margin_left + int((i / num_ticks) * draw_width)
            painter.drawLine(x_pos, margin_top - 5, x_pos, margin_top + 5)
            painter.drawText(x_pos - 20, margin_top - 12, 40, 15, Qt.AlignmentFlag.AlignCenter, f"{t_val:.0f}s")

        # 2. Dibujar tracks de cada capa en la receta
        track_y = margin_top + 30
        track_height = 35
        accumulated_time = 0.0

        for idx, step in enumerate(self.recipe_data):
            material = step.get("material", "Capa")
            duration = step.get("tiempo_total_crecimiento_sec", 0.0)
            
            # Posición en el eje de tiempo X
            start_x = margin_left + int((accumulated_time / self.total_time_sec) * draw_width)
            layer_width = int((duration / self.total_time_sec) * draw_width) if duration > 0 else 25 # Ancho mínimo visual si es sustrato

            # Nombre de la capa
            painter.setPen(QPen(QColor("#ecf0f1")))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(10, track_y + 22, margin_left - 15, 20, 
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, 
                             f"Paso {step.get('paso', idx+1)}: {material}")

            # Bloque de la capa
            color_hex = "#3498db" if "Substrate" not in material and "Sustrato" not in material else "#7f8c8d"
            painter.setBrush(QBrush(QColor(color_hex)))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawRoundedRect(start_x, track_y, layer_width, track_height, 4, 4)

            # Texto dentro de la barra
            if layer_width > 40:
                painter.setPen(QPen(QColor("#ffffff")))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(start_x, track_y, layer_width, track_height, 
                                 Qt.AlignmentFlag.AlignCenter, f"{duration:.1f}s")

            accumulated_time += duration
            track_y += track_height + 15

        # 3. Cursor de progreso actual (Playhead vertical rojo)
        cursor_x = margin_left + int((self.current_time_sec / self.total_time_sec) * draw_width)
        painter.setPen(QPen(QColor("#e74c3c"), 2.5))
        painter.drawLine(cursor_x, margin_top - 15, cursor_x, track_y + 10)
        
        # Cabeza del cursor (Triángulo)
        painter.setBrush(QBrush(QColor("#e74c3c")))
        painter.setPen(Qt.PenStyle.NoPen)
        points = [
            cursor_x - 6, margin_top - 15,
            cursor_x + 6, margin_top - 15,
            cursor_x, margin_top - 5
        ]
        # Dibujar triangulito
        for i in range(0, len(points), 2):
            pass # Representación visual simple de la línea del tiempo

# ==========================================
# INTERFAZ PRINCIPAL MONITOR Y LÍNEA DEL TIEMPO
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self, recipe_file=None):
        super().__init__()
        self.setWindowTitle("Sistema Principal de Automatización MBE - Monitor de Línea de Tiempo")
        self.resize(1100, 650)

        self.recipe_file = recipe_file if recipe_file else "receta_actual.json"
        self.recipe_data = []
        self.current_time = 0.0
        self.is_playing = False

        # Timer para simulación del crecimiento en tiempo real
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation_time)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Panel Superior de Botones Principales
        top_bar = QHBoxLayout()
        
        btn_open_builder = QPushButton("🏗️ Diseñar / Editar Receta")
        btn_open_builder.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 10px; font-size: 11pt;")
        btn_open_builder.clicked.connect(self.open_builder_module)

        btn_load_json = QPushButton("📂 Cargar JSON de Receta")
        btn_load_json.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; padding: 10px; font-size: 11pt;")
        btn_load_json.clicked.connect(self.load_json_dialog)

        top_bar.addWidget(btn_open_builder)
        top_bar.addWidget(btn_load_json)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # Título del Monitor
        self.lbl_status = QLabel("<b>Línea del Tiempo de Crecimiento</b>")
        self.lbl_status.setStyleSheet("font-size: 13pt; color: #ecf0f1;")
        main_layout.addWidget(self.lbl_status)

        # Área de la Línea del Tiempo Visual
        self.timeline_widget = MainTimelineWidget(self)
        main_layout.addWidget(self.timeline_widget, 1)

        # Barra de progreso y Controles de Ejecución
        control_bar = QHBoxLayout()
        
        self.btn_play = QPushButton("▶️ Iniciar Crecimiento")
        self.btn_play.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 8px 20px;")
        self.btn_play.clicked.connect(self.toggle_play)

        self.btn_stop = QPushButton("⏹️ Detener")
        self.btn_stop.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px 20px;")
        self.btn_stop.clicked.connect(self.stop_growth)

        self.lbl_timer_display = QLabel("Tiempo: 0.0s / 0.0s")
        self.lbl_timer_display.setStyleSheet("font-size: 11pt; font-weight: bold;")

        control_bar.addWidget(self.btn_play)
        control_bar.addWidget(self.btn_stop)
        control_bar.addWidget(self.lbl_timer_display)
        control_bar.addStretch()

        main_layout.addLayout(control_bar)

        # Intentar cargar la receta inicial si existe
        self.auto_load_recipe()

    def open_builder_module(self):
        # Abre el diseñador de recetas (builder.py)
        try:
            subprocess.Popen([sys.executable, "builder.py"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir builder.py:\n{e}")

    def auto_load_recipe(self):
        if os.path.exists(self.recipe_file):
            try:
                with open(self.recipe_file, 'r', encoding='utf-8') as f:
                    self.recipe_data = json.load(f)
                self.timeline_widget.set_recipe(self.recipe_data)
                self.lbl_status.setText(f"<b>Línea del Tiempo Cargada:</b> {self.recipe_file}")
                self.update_timer_label()
            except Exception as e:
                pass

    def load_json_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo de Receta JSON", "", "Archivos JSON (*.json)")
        if file_path:
            self.recipe_file = file_path
            self.auto_load_recipe()

    def toggle_play(self):
        if not self.recipe_data:
            QMessageBox.warning(self, "Advertencia", "Carga o diseña una receta antes de iniciar.")
            return

        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.btn_play.setText("▶️ Reanudar")
        else:
            self.timer.start(100) # Actualiza cada 100 ms
            self.is_playing = True
            self.btn_play.setText("⏸️ Pausar")

    def stop_growth(self):
        self.timer.stop()
        self.is_playing = False
        self.current_time = 0.0
        self.timeline_widget.set_current_time(0.0)
        self.btn_play.setText("▶️ Iniciar Crecimiento")
        self.update_timer_label()

    def update_simulation_time(self):
        self.current_time += 0.1
        total = self.timeline_widget.total_time_sec

        if self.current_time >= total:
            self.current_time = total
            self.timer.stop()
            self.is_playing = False
            self.btn_play.setText("▶️ Iniciar Crecimiento")
            QMessageBox.information(self, "Finalizado", "¡Proceso de crecimiento de la receta completado!")

        self.timeline_widget.set_current_time(self.current_time)
        self.update_timer_label()

    def update_timer_label(self):
        total = self.timeline_widget.total_time_sec
        self.lbl_timer_display.setText(f"Tiempo: {self.current_time:.1f}s / {total:.1f}s")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Recibir archivo JSON por argumento si se llama desde builder.py
    initial_json = sys.argv[1] if len(sys.argv) > 1 else "receta_actual.json"
    
    window = MainWindow(initial_json)
    window.show()
    sys.exit(app.exec())