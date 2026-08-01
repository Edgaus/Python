import sys
import json
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, 
                             QProgressBar, QFileDialog, QMessageBox, QFrame,
                             QGridLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

# =========================================================================
# HOJA DE ESTILOS GENERAL (ALTO CONTRASTE)
# =========================================================================
MAIN_STYLE_SHEET = """
QMainWindow {
    background: #dbe9f6;
}
QWidget {
    color: #000000;
}
QLabel {
    font-size: 14px;
    color: #000000;
}
QGroupBox {
    background: white;
    border: 1px solid #a0a0a0;
    border-radius: 8px;
    margin-top: 15px;
    font-size: 15px;
    font-weight: bold;
    color: #0d2a52;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #0d2a52;
}
QProgressBar {
    border: 1px solid #7f8c8d;
    border-radius: 4px;
    text-align: center;
    color: #000000;
    font-weight: bold;
    background-color: #ecf0f1;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #3498db;
    border-radius: 3px;
}

/* ======================================================== */
/* COLOR DE TEXTO NEGRO FORZADO Y TAMAÑO PARA SPINBOXES     */
/* ======================================================== */
QDoubleSpinBox, QSpinBox, QDoubleSpinBox QLineEdit, QSpinBox QLineEdit {
    background-color: #ffffff;
    color: #000000 !important;
    border: 1px solid #a0a0a0;
    border-radius: 4px;
    padding: 2px 18px 2px 4px;
    font-size: 13px;
    font-weight: bold;
    min-width: 60px;
    min-height: 24px;
}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 15px;
    background-color: #e0e0e0;
    border-left: 1px solid #a0a0a0;
}
QDoubleSpinBox::up-button {
    border-bottom: 1px solid #a0a0a0;
    border-top-right-radius: 3px;
}
QDoubleSpinBox::down-button {
    border-bottom-right-radius: 3px;
}
QDoubleSpinBox::up-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #000000;
}
QDoubleSpinBox::down-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #000000;
}
"""

# =========================================================================
# WIDGET GRÁFICO DE LÍNEA DE TIEMPO / GANTT (GLOBAL)
# =========================================================================
class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.recipe_data = None
        self.global_time = 0.0
        self.total_recipe_time = 1.0
        
        self.element_colors = {
            "Ga": QColor(50, 120, 220),
            "Al": QColor(40, 170, 90),
            "In": QColor(255, 150, 40),
            "As": QColor(220, 50, 50),
            "N":  QColor(150, 50, 220)
        }

    def format_time_label(self, seconds):
        if self.total_recipe_time < 120:
            return f"{seconds:.1f}s"
        elif self.total_recipe_time < 7200:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

    def set_recipe_data(self, recipe_data, global_time):
        self.recipe_data = recipe_data
        self.global_time = global_time
        
        if self.recipe_data:
            self.total_recipe_time = sum(float(s.get("tiempo_total_crecimiento_sec", 0)) for s in self.recipe_data)
            self.total_recipe_time = max(1.0, self.total_recipe_time)
        else:
            self.total_recipe_time = 1.0
            
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
        if num_cells == 0:
            p.setPen(QPen(QColor("#7f8c8d")))
            p.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            p.drawText(QRectF(left, top, width, draw_h), Qt.AlignmentFlag.AlignCenter, 
                       "La receta no contiene celdas activas (Sólo sustrato)")
            return

        row_h = draw_h / num_cells
        font = QFont("Arial", 11, QFont.Weight.Bold)
        p.setFont(font)

        p.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))
        num_ticks = 5
        for i in range(num_ticks + 1):
            x_pos = left + (i / num_ticks) * width
            t_val = (i / num_ticks) * self.total_recipe_time
            p.drawLine(int(x_pos), top, int(x_pos), bottom)
            
            p.setPen(QPen(Qt.GlobalColor.black))
            p.setFont(QFont("Arial", 9))
            lbl_time = self.format_time_label(t_val)
            p.drawText(int(x_pos) - 20, bottom + 15, 40, 15, Qt.AlignmentFlag.AlignCenter, lbl_time)
            p.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))

        y_cursor = top
        for cell_name in all_cells:
            p.setPen(QPen(Qt.GlobalColor.black))
            p.setFont(font)
            p.drawText(15, int(y_cursor + row_h/2 + 5), f"Celda {cell_name}")

            color = self.element_colors.get(cell_name, QColor(100, 100, 100))
            bar_y = y_cursor + row_h * 0.3
            bar_h = row_h * 0.4

            current_start_t = 0.0
            
            for step in self.recipe_data:
                step_duration = float(step.get("tiempo_total_crecimiento_sec", 0))
                
                if step_duration > 0 and cell_name in step.get("parametros_celdas", {}):
                    el_params = step["parametros_celdas"][cell_name]
                    mode = el_params.get("mode", "Continuo")
                    
                    x_start = left + (current_start_t / self.total_recipe_time) * width
                    
                    if mode == "Continuo":
                        block_w = (step_duration / self.total_recipe_time) * width
                        p.fillRect(QRectF(x_start, bar_y, block_w, bar_h), color)
                        p.setPen(Qt.GlobalColor.black)
                        p.drawRect(QRectF(x_start, bar_y, block_w, bar_h))
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
                                t_curr += period

                current_start_t += step_duration

            p.setPen(QPen(QColor(200, 200, 200)))
            p.drawLine(left, int(y_cursor + row_h), right, int(y_cursor + row_h))
            y_cursor += row_h

        if self.total_recipe_time > 0:
            playhead_x = left + (min(self.global_time, self.total_recipe_time) / self.total_recipe_time) * width
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

        self.recipe_data = []
        self.current_step_index = 0
        self.current_step_time = 0.0
        self.is_running = False
        self.is_paused = False
        self.is_unlocked = False

        # Estado visual de las celdas para evitar redibujados continuos
        self.last_drawn_step_index = -1
        self.last_drawn_lock_state = None
        self.cell_widgets = {}

        self.process_timer = QTimer(self)
        self.process_timer.setInterval(100)
        self.process_timer.timeout.connect(self.on_process_tick)

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
            QFrame#Sidebar {
                background: #0d2a52;
                color: white;
            }
            QFrame#Sidebar QPushButton {
                background: transparent;
                border: none;
                text-align: left;
                padding: 12px;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            QFrame#Sidebar QPushButton:hover {
                background: #204a87;
                border-left: 4px solid #3498db;
            }
            QFrame#Sidebar QLabel {
                color: white;
            }
        """)

        sideLayout = QVBoxLayout(sidebar)
        sideLayout.setContentsMargins(15, 20, 15, 20)

        title = QLabel("MBE CONTROL")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 20px;")
        sideLayout.addWidget(title)

        for txt in ["Crecimiento", "Recetas", "Parámetros", "Historial", "Alarmas", "Configuración"]:
            btn = QPushButton(txt)
            sideLayout.addWidget(btn)

        sideLayout.addStretch()
        layout.addWidget(sidebar)

        # ---------------- Panel principal ----------------
        right_panel = QWidget()
        main_layout = QVBoxLayout(right_panel)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("Programa de crecimiento")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #0d2a52;")
        main_layout.addWidget(titulo)

        # Timeline
        self.timeline = TimelineWidget()
        main_layout.addWidget(self.timeline)

        # Botones de Acción
        botones = QHBoxLayout()
        
        btn_style_small = """
            QPushButton {
                background: white; border: 1px solid #7f8c8d; color: #333; 
                border-radius: 6px; padding: 10px 15px; font-weight: bold;
            }
            QPushButton:hover { background: #ecf0f1; }
        """
        self.btn_load = QPushButton("📁 Cargar receta JSON")
        self.btn_load.setStyleSheet(btn_style_small)
        self.btn_load.clicked.connect(self.select_recipe_file)

        self.btn_builder = QPushButton("🛠️ Crear receta (Builder)")
        self.btn_builder.setStyleSheet(btn_style_small)
        self.btn_builder.clicked.connect(self.launch_builder)

        self.btn_unlock = QPushButton("🔒 Bloqueado")
        self.btn_unlock.setStyleSheet("""
            QPushButton {
                background: #e74c3c; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        self.btn_unlock.clicked.connect(self.toggle_unlock_mode)

        botones.addWidget(self.btn_load)
        botones.addWidget(self.btn_builder)
        botones.addWidget(self.btn_unlock)
        botones.addStretch()

        # Botones Principales de Control
        btn_style_big = """
            QPushButton {
                color: white; font-size: 18px; font-weight: bold; border-radius: 15px; border: none;
            }
        """
        self.btn_start = QPushButton("▶ INICIAR")
        self.btn_start.setFixedSize(140, 55)
        self.btn_start.setStyleSheet(btn_style_big + "QPushButton { background: #27ae60; } QPushButton:hover { background: #2ecc71; }")
        self.btn_start.clicked.connect(self.start_growth)

        self.btn_pause = QPushButton("⏸ PAUSAR")
        self.btn_pause.setFixedSize(140, 55)
        self.btn_pause.setStyleSheet(btn_style_big + "QPushButton { background: #f39c12; } QPushButton:hover { background: #f1c40f; }")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.pause_growth)

        self.btn_stop = QPushButton("⏹ DETENER")
        self.btn_stop.setFixedSize(140, 55)
        self.btn_stop.setStyleSheet(btn_style_big + "QPushButton { background: #e53935; } QPushButton:hover { background: #ef5350; }")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_growth)

        botones.addWidget(self.btn_start)
        botones.addWidget(self.btn_pause)
        botones.addWidget(self.btn_stop)

        main_layout.addLayout(botones)

        # ---------------- Condiciones ----------------
        group = QGroupBox("Condiciones de la etapa")
        self.grid = QGridLayout(group)
        self.grid.setVerticalSpacing(15)
        self.grid.setHorizontalSpacing(20)

        self.lbl_material = QLabel("<b>Material:</b> Ninguno")
        self.lbl_step = QLabel("<b>Etapa:</b> - / -")
        self.lbl_time = QLabel("<b>Tiempo:</b> 0.0s / 0.0s")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(300)

        self.grid.addWidget(self.lbl_material, 0, 0)
        self.grid.addWidget(self.lbl_step, 0, 1)
        self.grid.addWidget(self.lbl_time, 0, 2)
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

    # =========================================================================
    # LÓGICA DE CONTROL Y RECETAS
    # =========================================================================
    def toggle_unlock_mode(self):
        self.is_unlocked = not self.is_unlocked
        if self.is_unlocked:
            self.btn_unlock.setText("🔓 Desbloqueado")
            self.btn_unlock.setStyleSheet("""
                QPushButton {
                    background: #27ae60; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none;
                }
                QPushButton:hover { background: #2ecc71; }
            """)
        else:
            self.btn_unlock.setText("🔒 Bloqueado")
            self.btn_unlock.setStyleSheet("""
                QPushButton {
                    background: #e74c3c; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none;
                }
                QPushButton:hover { background: #c0392b; }
            """)
        
        # Al cambiar el bloqueo forzamos a reconstruir la UI para mostrar u ocultar controles
        if self.recipe_data and self.current_step_index < len(self.recipe_data):
            self.refresh_cells_ui(self.recipe_data[self.current_step_index], force_rebuild=True)

    def select_recipe_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Cargar Receta MBE", "", "Archivos JSON (*.json)")
        if file_path:
            self.load_recipe_from_file(file_path)

    def load_recipe_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list) or len(data) == 0:
                QMessageBox.warning(self, "Advertencia", "El archivo no contiene una receta válida.")
                return

            self.recipe_data = data
            self.reset_process_to_first_valid_layer()
            QMessageBox.information(self, "Éxito", f"Receta '{os.path.basename(file_path)}' cargada correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo JSON:\n{e}")

    def reset_process_to_first_valid_layer(self):
        self.current_step_time = 0.0
        self.current_step_index = 0
        self.last_drawn_step_index = -1  # Forzar renderizado desde 0
        
        while self.current_step_index < len(self.recipe_data):
            step_time = float(self.recipe_data[self.current_step_index].get("tiempo_total_crecimiento_sec", 0))
            if step_time > 0.0:
                break
            self.current_step_index += 1
            
        if self.current_step_index >= len(self.recipe_data):
            self.current_step_index = 0
            
        self.update_step_display()

    def update_step_display(self):
        if not self.recipe_data or self.current_step_index >= len(self.recipe_data):
            self.lbl_material.setText("<b>Material:</b> Finalizado")
            self.lbl_step.setText("<b>Etapa:</b> - / -")
            self.lbl_time.setText("<b>Tiempo:</b> 0.0s / 0.0s")
            self.lbl_comment.setText("<b>Comentario:</b> <i>Proceso finalizado</i>")
            self.progress_bar.setValue(100)
            
            if self.recipe_data:
                total = sum(float(s.get("tiempo_total_crecimiento_sec", 0)) for s in self.recipe_data)
                self.timeline.set_recipe_data(self.recipe_data, total)
                
            self.refresh_cells_ui(None)
            return

        step = self.recipe_data[self.current_step_index]
        material = step.get("material", "Desconocido")
        total_time = float(step.get("tiempo_total_crecimiento_sec", 60.0))
        comentario = step.get("comentario", "")

        self.lbl_material.setText(f"<b>Material:</b> <font color='#0d2a52'>{material}</font>")
        self.lbl_step.setText(f"<b>Etapa:</b> {self.current_step_index + 1} de {len(self.recipe_data)}")
        self.lbl_time.setText(f"<b>Tiempo:</b> {self.current_step_time:.1f}s / {total_time:.1f}s")
        
        if comentario.strip():
            self.lbl_comment.setText(f"<b>Comentario:</b> <i>{comentario}</i>")
        else:
            self.lbl_comment.setText("<b>Comentario:</b> <i>Ninguno</i>")
        
        pct = int((self.current_step_time / total_time) * 100) if total_time > 0 else 100
        self.progress_bar.setValue(min(100, pct))
        
        global_time = 0.0
        for i in range(self.current_step_index):
            global_time += float(self.recipe_data[i].get("tiempo_total_crecimiento_sec", 0))
        global_time += self.current_step_time

        self.timeline.set_recipe_data(self.recipe_data, global_time)
        self.refresh_cells_ui(step)

    # -------------------------------------------------------------------------
    # MOTOR DE INTERFAZ OPTIMIZADO (No destruye widgets mientras el programa corre)
    # -------------------------------------------------------------------------
    def refresh_cells_ui(self, step, force_rebuild=False):
        if not step:
            while self.cells_layout.count():
                item = self.cells_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.cell_widgets.clear()
            return

        # FASE 1: CONSTRUCCIÓN (Sólo ocurre 1 vez por etapa o si cambia el modo de bloqueo)
        if force_rebuild or self.last_drawn_step_index != self.current_step_index or self.last_drawn_lock_state != self.is_unlocked:
            
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
                    
                    widget_refs = {
                        "frame": frame,
                        "status_lbl": lbl_status
                    }

                    if self.is_unlocked:
                        if mode == "Continuo":
                            # Botón de Toggle para modo continuo
                            btn_toggle = QPushButton()
                            btn_toggle.setStyleSheet("border: none;")
                            
                            def make_toggle(cell_params):
                                def toggle():
                                    current = cell_params.get("manual_is_open", True)
                                    cell_params["manual_is_open"] = not current
                                    # Forzar actualización visual inmediata
                                    self.refresh_cells_ui(self.recipe_data[self.current_step_index]) 
                                return toggle
                                
                            btn_toggle.clicked.connect(make_toggle(params))
                            widget_refs["toggle_btn"] = btn_toggle
                            flayout.addWidget(btn_toggle)

                        elif mode == "Ciclo":
                            # Controles de Tiempo interactivos para Ciclo
                            form_layout = QHBoxLayout()
                            form_layout.setContentsMargins(0, 0, 0, 0)
                            form_layout.setSpacing(4)
                            
                            spin_s = QDoubleSpinBox()
                            spin_s.setRange(0.0, 999.9)
                            spin_s.setDecimals(1)
                            spin_s.setValue(float(params.get("t_shift", 0.0)))
                            spin_s.setToolTip("Shift")
                            
                            spin_o = QDoubleSpinBox()
                            spin_o.setRange(0.0, 999.9)
                            spin_o.setDecimals(1)
                            spin_o.setValue(float(params.get("t_open", 5.0)))
                            spin_o.setToolTip("Open")
                            
                            spin_c = QDoubleSpinBox()
                            spin_c.setRange(0.0, 999.9)
                            spin_c.setDecimals(1)
                            spin_c.setValue(float(params.get("t_close", 5.0)))
                            spin_c.setToolTip("Close")

                            def make_callback(cell_key, param_key):
                                def on_val_changed(val):
                                    if self.recipe_data and self.current_step_index < len(self.recipe_data):
                                        self.recipe_data[self.current_step_index]["parametros_celdas"][cell_key][param_key] = float(val)
                                        self.timeline.update()
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
                        # Vista Bloqueada (Estática)
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
                
            self.last_drawn_step_index = self.current_step_index
            self.last_drawn_lock_state = self.is_unlocked


        # FASE 2: ACTUALIZACIÓN VISUAL (Ocurre cada 100ms para mantener vivo el monitor)
        cells = step.get("parametros_celdas", {})
        for el, params in cells.items():
            if el not in self.cell_widgets: continue
            
            mode = params.get("mode", "Continuo")
            is_open = True
            
            if mode == "Continuo":
                # Respetamos el flag de control manual insertado en tiempo real
                is_open = params.get("manual_is_open", True) 
            elif mode == "Ciclo":
                t_shift = float(params.get("t_shift", 0.0))
                t_open = float(params.get("t_open", 5.0))
                t_close = float(params.get("t_close", 5.0))
                period = t_shift + t_open + t_close
                if period > 0:
                    pos_in_cycle = self.current_step_time % period
                    is_open = (t_shift <= pos_in_cycle < (t_shift + t_open))
                else:
                    is_open = False

            state_str = "ABIERTA" if is_open else "CERRADA"
            color_str = "#27ae60" if is_open else "#e53935"
            
            self.cell_widgets[el]["status_lbl"].setText(state_str)
            self.cell_widgets[el]["status_lbl"].setStyleSheet(f"border: none; color: {color_str}; font-size: 16px; font-weight: bold;")
            self.cell_widgets[el]["frame"].setStyleSheet(f"background: white; border: 2px solid {color_str}; border-radius: 6px; padding: 5px;")
            
            # Si el botón toggle existe, actualizar su aspecto
            if "toggle_btn" in self.cell_widgets[el]:
                btn = self.cell_widgets[el]["toggle_btn"]
                if is_open:
                    btn.setText("🔴 Forzar Cierre")
                    btn.setStyleSheet("background-color: #e53935; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
                else:
                    btn.setText("🟢 Reabrir Celda")
                    btn.setStyleSheet("background-color: #27ae60; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")


    def start_growth(self):
        if not self.recipe_data:
            QMessageBox.warning(self, "Advertencia", "Por favor carga una receta JSON antes de iniciar.")
            return

        self.is_running = True
        self.is_paused = False
        self.process_timer.start()

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

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

        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("⏸ PAUSAR")
        self.btn_stop.setEnabled(False)

        self.reset_process_to_first_valid_layer()

    def on_process_tick(self):
        if not self.is_running or self.is_paused or not self.recipe_data:
            return

        step = self.recipe_data[self.current_step_index]
        total_time = float(step.get("tiempo_total_crecimiento_sec", 60.0))

        self.current_step_time += 0.1

        if self.current_step_time >= total_time:
            self.current_step_index += 1
            self.current_step_time = 0.0

            while self.current_step_index < len(self.recipe_data) and float(self.recipe_data[self.current_step_index].get("tiempo_total_crecimiento_sec", 0)) == 0.0:
                 self.current_step_index += 1

            if self.current_step_index >= len(self.recipe_data):
                self.process_timer.stop()
                self.is_running = False
                self.btn_start.setEnabled(True)
                self.btn_pause.setEnabled(False)
                self.btn_stop.setEnabled(False)
                self.update_step_display()
                QMessageBox.information(self, "¡Proceso Completado!", "¡Todas las capas han finalizado!")
                return

        self.update_step_display()

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