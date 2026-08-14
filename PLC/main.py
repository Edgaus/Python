"""
main.py — HMI del operador (hoy mezcla UI2 + UI3 en una sola ventana)

UI2 = TimelineWidget: línea de tiempo del PLAN (receta JSON).
UI3 = panel inferior + botones: luces abiertas/cerradas "ahora",
      INICIAR / PAUSAR / DETENER, desbloqueo para editar en vivo.

Estado actual: "Modo Visual" — los sockets UDP hacia monitor_247.py están
comentados, así que puedes cargar una receta y ver la gráfica sin el cerebro.
Cuando se rehabiliten, enviar_comando() hablará con 127.0.0.1:5000 y
escuchar_backend() leerá el estado en :5001.

Lanzar:  cd PLC && ../.venv/bin/python main.py
Desde el menú lateral también se abren builder.py (UI1) e historial_vivo.py (UI4).
"""
import sys
import json
import subprocess
import os
import copy
import time
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QGroupBox, 
                             QProgressBar, QFileDialog, QMessageBox, QFrame,
                             QGridLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from styles import MAIN_STYLE_SHEET
from monitor_client import MonitorCliente
import config

# =========================================================================
# UI2 — WIDGET: línea de tiempo del PLAN (receta), no del CSV
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
            "Al": QColor(40, 170, 90),
            "Ga": QColor(50, 120, 220),
            "In": QColor(255, 150, 40),
            "N":  QColor(150, 50, 220),
            "As": QColor(220, 50, 50),
            "Si": QColor(90, 90, 90),
            "Be": QColor(180, 140, 40),
            "Mn": QColor(140, 80, 40),
            "Mg": QColor(80, 180, 180),
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
                       "Modo Visual: Cargue una receta para simular la gráfica...")
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
            p.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
            p.drawLine(int(playhead_x), top - 10, int(playhead_x), bottom + 10)
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.drawText(int(playhead_x) - 20, top - 15, "Ahora")

# =========================================================================
# UI2 + UI3 — Ventana principal (cliente del monitor SCADA)
# =========================================================================
class MainWindow(QMainWindow):
    def __init__(self, recipe_path=None):
        super().__init__()
        self.setWindowTitle("MBE Control - Cliente del Monitor 24/7")
        self.resize(1350, 800)
        self.setStyleSheet(MAIN_STYLE_SHEET)

        self.recipe_data = []
        self.temp_step_data = None 
        
        self.is_unlocked = False
        self.last_drawn_step_index = -1
        self.last_drawn_lock_state = None
        self.cell_widgets = {}
        self.monitor_online = False
        self.ultimo_contacto = time.time()
        self.fin_ya_notificado = False

        self.cliente = MonitorCliente()
        self.network_timer = QTimer(self)
        self.network_timer.setInterval(100)
        self.network_timer.timeout.connect(self.consultar_monitor)
        self.network_timer.start()

        self.buildUI()
        self.cliente.pedir_estado()

        if recipe_path and os.path.exists(recipe_path):
            self.load_recipe_from_file(recipe_path)

    def enviar_comando(self, diccionario_comando):
        if not self.cliente.enviar(diccionario_comando):
            print("No se pudo enviar el comando al Monitor 24/7.")

    def consultar_monitor(self):
        estado = self.cliente.recibir()
        if estado:
            self.monitor_online = True
            self.ultimo_contacto = time.time()
            self.procesar_estado_red(estado)
        elif time.time() - self.ultimo_contacto > config.TIMEOUT_UI_S:
            if self.monitor_online:
                self.monitor_online = False
                self.lbl_conexion.setText("Monitor 24/7 no responde. Ejecuta monitor_247.py")
                self.lbl_conexion.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.cliente.pedir_estado()

    def procesar_estado_red(self, estado):
        modo = "simulación" if estado.get("modo_simulacion") else "PLC"
        self.lbl_conexion.setText(f"Monitor en línea ({modo})")
        self.lbl_conexion.setStyleSheet("color: #27ae60; font-weight: bold;")

        if not self.is_unlocked:
            receta = estado.get("receta_actual") or []
            if receta:
                self.recipe_data = receta

        resultados = estado.get("resultados_motor", {})
        is_running = estado.get("is_running", False)
        is_paused = estado.get("is_paused", False)

        celdas = estado.get("celdas") or {}
        if celdas:
            resultados = dict(resultados)
            resultados["estado_luces_ui"] = {
                nombre: bool(info.get("abierta", False)) for nombre, info in celdas.items()
            }

        if is_running:
            self.fin_ya_notificado = False
            self.btn_start.setVisible(False)
            self.btn_pause.setVisible(True)
            self.btn_stop.setVisible(True)
            self.btn_pause.setText("▶ REANUDAR" if is_paused else "⏸ PAUSAR")
        else:
            self.btn_start.setVisible(True)
            self.btn_pause.setVisible(False)
            self.btn_stop.setVisible(False)

        if resultados.get("terminado", False) and not is_running and self.recipe_data and not self.fin_ya_notificado:
            if float(resultados.get("tiempo_global", 0)) > 0:
                self.fin_ya_notificado = True
                QMessageBox.information(self, "Proceso Completado", "El Monitor 24/7 reporta que el proceso ha finalizado.")

        self.update_step_display(resultados)

    def abrir_explorador(self, carpeta_nombre):
        ruta = os.path.abspath(carpeta_nombre)
        if not os.path.exists(ruta):
            try: os.makedirs(ruta)
            except Exception as e: QMessageBox.warning(self, "Error", str(e)); return
        try:
            if platform.system() == "Windows": os.startfile(ruta)
            elif platform.system() == "Darwin": subprocess.Popen(["open", ruta])
            else: subprocess.Popen(["xdg-open", ruta])
        except Exception as e: QMessageBox.warning(self, "Error", str(e))

    def buildUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

# ---------------- Sidebar ----------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame#Sidebar { background: #0d2a52; color: white; }
            QFrame#Sidebar QPushButton { background: transparent; border: none; text-align: left; padding: 12px 15px; color: white; font-size: 15px; font-weight: bold; }
            QFrame#Sidebar QPushButton:hover { background: #204a87; border-left: 4px solid #3498db; }
            QFrame#Sidebar QLabel { color: white; }
        """)

        sideLayout = QVBoxLayout(sidebar)
        sideLayout.setContentsMargins(15, 20, 15, 20)
        sideLayout.setSpacing(5) # Mantiene todos los elementos compactos y juntos
        
        title = QLabel("MBE CONTROL")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 15px; text-align: center;")
        sideLayout.addWidget(title)

        # Opciones generales del menú lateral juntas
        self.sidebar_btns = {}
        
        # Agregamos solo las que realmente utilizas (incluyendo Recetas e Historial con sus carpetas)
        menu_items = [
            ("🕒 Historial (carpeta)", lambda: self.abrir_explorador("historial")),
            ("📈 Historial vivo (UI4)", self.launch_historial_vivo),
            ("📁 Cargar receta JSON", self.select_recipe_file),
            ("🛠️ Crear receta (Builder)", self.launch_builder),
            ("👁 Visor de celdas", self.launch_visor),
        ]

        for txt, callback in menu_items:
            btn = QPushButton(txt)
            # Damos un toque de color diferenciado a las acciones de archivos si lo deseas
            if "Cargar" in txt:
                btn.setStyleSheet("color: #f1c40f; text-align: left; padding: 12px 15px; font-size: 15px; font-weight: bold;")
            elif "Crear" in txt:
                btn.setStyleSheet("color: #3498db; text-align: left; padding: 12px 15px; font-size: 15px; font-weight: bold;")
            elif "UI4" in txt:
                btn.setStyleSheet("color: #2ecc71; text-align: left; padding: 12px 15px; font-size: 15px; font-weight: bold;")
                
            if callback:
                btn.clicked.connect(callback)
            sideLayout.addWidget(btn)
            self.sidebar_btns[txt] = btn

        sideLayout.addStretch()
        layout.addWidget(sidebar)
        

        

        # ---------------- Panel principal ----------------
        right_panel = QWidget()
        main_layout = QVBoxLayout(right_panel)
        main_layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Programa de crecimiento (cliente del Monitor)")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #0d2a52;")
        main_layout.addWidget(titulo)

        self.lbl_conexion = QLabel("Buscando Monitor 24/7...")
        self.lbl_conexion.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        main_layout.addWidget(self.lbl_conexion)

        self.timeline = TimelineWidget()
        main_layout.addWidget(self.timeline)

        botones = QHBoxLayout()
        self.btn_unlock = QPushButton("🔒 Bloqueado")
        self.btn_unlock.setStyleSheet("QPushButton { background: #e74c3c; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; } QPushButton:hover { background: #c0392b; }")
        self.btn_unlock.clicked.connect(self.toggle_unlock_mode)

        self.btn_confirm = QPushButton("✔️ Confirmar Cambios en Vivo")
        self.btn_confirm.setStyleSheet("QPushButton { background: #3498db; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; } QPushButton:hover { background: #2980b9; }")
        self.btn_confirm.setVisible(False)
        self.btn_confirm.clicked.connect(self.apply_pending_changes)

        botones.addWidget(self.btn_unlock)
        botones.addWidget(self.btn_confirm)
        botones.addStretch()

        btn_style_big = "QPushButton { color: white; font-size: 18px; font-weight: bold; border-radius: 15px; border: none; }"
        
        self.btn_start = QPushButton("▶ INICIAR")
        self.btn_start.setFixedSize(140, 55)
        self.btn_start.setStyleSheet(btn_style_big + "QPushButton { background: #27ae60; } QPushButton:hover { background: #2ecc71; }")
        self.btn_start.clicked.connect(lambda: self.enviar_comando({"cmd": "start"}))

        self.btn_pause = QPushButton("⏸ PAUSAR")
        self.btn_pause.setFixedSize(140, 55)
        self.btn_pause.setStyleSheet(btn_style_big + "QPushButton { background: #f39c12; } QPushButton:hover { background: #f1c40f; }")
        self.btn_pause.setVisible(False)  
        self.btn_pause.clicked.connect(lambda: self.enviar_comando({"cmd": "pause"}))

        self.btn_stop = QPushButton("⏹ DETENER")
        self.btn_stop.setFixedSize(140, 55)
        self.btn_stop.setStyleSheet(btn_style_big + "QPushButton { background: #e53935; } QPushButton:hover { background: #ef5350; }")
        self.btn_stop.setVisible(False) 
        self.btn_stop.clicked.connect(lambda: self.enviar_comando({"cmd": "stop"}))

        botones.addWidget(self.btn_start)
        botones.addWidget(self.btn_pause)
        botones.addWidget(self.btn_stop)
        main_layout.addLayout(botones)

        group = QGroupBox("Condiciones de la etapa dictadas por el Monitor")
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
        growth_time = float(step.get("tiempo_total_crecimiento_sec", step.get("growth_time", 60.0)))
        comment = step.get("comentario", step.get("comment", ""))
        raw_cells = step.get("parametros_celdas") or step.get("element_data") or {}
        
        normalized_cells = {}
        for el, p in raw_cells.items():
            normalized_cells[el] = {
                "mode": p.get("mode", "Continuo"),
                "t_shift": float(p.get("t_shift", 0.0)),
                "t_open": float(p.get("t_open", 5.0)),
                "t_close": float(p.get("t_close", 5.0)),
                "manual_is_open": p.get("manual_is_open", True)
            }
        return {"material": material, "tiempo_total_crecimiento_sec": growth_time, 
                "comentario": comment, "parametros_celdas": normalized_cells}

    def toggle_unlock_mode(self):
        self.is_unlocked = not self.is_unlocked
        if self.is_unlocked:
            self.btn_unlock.setText("🔓 Modo Edición Remota")
            self.btn_unlock.setStyleSheet("QPushButton { background: #27ae60; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; }")
            self.btn_confirm.setVisible(True)
            self.lbl_time_total_static.setVisible(False)
            self.spin_total_step_time.setVisible(True)
        else:
            self.temp_step_data = None
            self.btn_unlock.setText("🔒 Bloqueado")
            self.btn_unlock.setStyleSheet("QPushButton { background: #e74c3c; color: white; border-radius: 6px; padding: 10px 15px; font-weight: bold; border: none; }")
            self.btn_confirm.setVisible(False)
            self.lbl_time_total_static.setVisible(True)
            self.spin_total_step_time.setVisible(False)
        self.last_drawn_step_index = -1 # Forzar redibujo

    def on_step_total_time_changed(self, new_val):
        if self.temp_step_data: self.temp_step_data["tiempo_total_crecimiento_sec"] = float(new_val)

    def apply_pending_changes(self):
        if self.is_unlocked and self.temp_step_data and self.recipe_data:
            idx = self.last_drawn_step_index
            if 0 <= idx < len(self.recipe_data):
                self.recipe_data[idx] = copy.deepcopy(self.temp_step_data)
                self.enviar_comando({"cmd": "update_recipe", "recipe": self.recipe_data})
                QMessageBox.information(self, "Monitor", "Cambios enviados al Monitor 24/7.")

    def select_recipe_file(self):
        ruta = os.path.abspath("recetas")
        if not os.path.exists(ruta): os.makedirs(ruta)
        file_path, _ = QFileDialog.getOpenFileName(self, "Cargar Receta MBE", ruta, "Archivos JSON (*.json)")
        if file_path: self.load_recipe_from_file(file_path)

    def load_recipe_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: raw_data = json.load(f)
            self.recipe_data = [self.normalize_step(s) for s in raw_data]
            
            self.enviar_comando({"cmd": "load", "recipe": self.recipe_data})
            
            # --- AGREGADO PARA PRUEBAS VISUALES ---
            # Forzamos la gráfica a pintar la receta que cargamos, ya que el servidor no está corriendo para responder.
            total = sum(float(s.get("tiempo_total_crecimiento_sec", 0)) for s in self.recipe_data)
            self.timeline.set_recipe_data(self.recipe_data, total)
            self.refresh_cells_ui(self.recipe_data[0] if self.recipe_data else None, {}, 0)
            
            QMessageBox.information(self, "Receta", f"Receta '{os.path.basename(file_path)}' enviada al Monitor 24/7.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo JSON:\n{e}")

    def update_step_display(self, resultados_backend):
        terminado = resultados_backend.get("terminado", True)
        indice_backend = resultados_backend.get("indice_etapa", 0)
        tiempo_actual = resultados_backend.get("tiempo_etapa_actual", 0.0)
        global_time = resultados_backend.get("tiempo_global", 0.0)
        estado_luces = resultados_backend.get("estado_luces_ui", {})

        if not self.recipe_data or terminado:
            self.lbl_material.setText("<b>Material:</b> Finalizado o Inactivo")
            self.lbl_step.setText("<b>Etapa:</b> - / -")
            self.lbl_time_cur.setText("<b>Tiempo:</b> 0.0s / ")
            self.progress_bar.setValue(100)
            if self.recipe_data:
                total = sum(float(s.get("tiempo_total_crecimiento_sec", 0)) for s in self.recipe_data)
                self.timeline.set_recipe_data(self.recipe_data, total)
            self.refresh_cells_ui(None, estado_luces, -2)
            return

        if indice_backend < len(self.recipe_data):
            step = self.recipe_data[indice_backend]
            material = step.get("material", "Desconocido")
            total_time = float(step.get("tiempo_total_crecimiento_sec", 60.0))
            comentario = step.get("comentario", "")

            if self.is_unlocked and (self.temp_step_data is None or self.last_drawn_step_index != indice_backend):
                self.temp_step_data = copy.deepcopy(step)

            self.lbl_material.setText(f"<b>Material:</b> <font color='#0d2a52'>{material}</font>")
            self.lbl_step.setText(f"<b>Etapa:</b> {indice_backend + 1} de {len(self.recipe_data)}")
            self.lbl_time_cur.setText(f"<b>Tiempo:</b> {tiempo_actual:.1f}s / ")
            self.lbl_time_total_static.setText(f"{total_time:.1f}s")

            if not self.is_unlocked:
                self.spin_total_step_time.blockSignals(True)
                self.spin_total_step_time.setValue(total_time)
                self.spin_total_step_time.blockSignals(False)
            
            self.lbl_comment.setText(f"<b>Comentario:</b> <i>{comentario}</i>" if comentario.strip() else "<b>Comentario:</b> <i>Ninguno</i>")
            
            pct = int((tiempo_actual / total_time) * 100) if total_time > 0 else 100
            self.progress_bar.setValue(min(100, pct))
            
            self.timeline.set_recipe_data(self.recipe_data, global_time)
            self.refresh_cells_ui(step, estado_luces, indice_backend)

    def refresh_cells_ui(self, step, active_states, current_index):
        if not step:
            if active_states:
                step = {
                    "parametros_celdas": {
                        el: {"mode": "Continuo"} for el in config.CELDAS
                    }
                }
            else:
                while self.cells_layout.count():
                    item = self.cells_layout.takeAt(0)
                    if item.widget(): item.widget().deleteLater()
                self.cell_widgets.clear()
                self.timeline.set_active_cells({})
                return

        if self.last_drawn_step_index != current_index or self.last_drawn_lock_state != self.is_unlocked:
            while self.cells_layout.count():
                item = self.cells_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.cell_widgets.clear()
            
            cells = step.get("parametros_celdas", {})
            if not cells:
                lbl = QLabel("<i>Sin celdas activas (Sustrato / Standby)</i>")
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
                                        self.temp_step_data["parametros_celdas"][cell_key]["manual_is_open"] = not self.temp_step_data["parametros_celdas"][cell_key].get("manual_is_open", True)
                                        # Reflejo temporal del botón
                                        btn = self.cell_widgets[cell_key]["toggle_btn"]
                                        if self.temp_step_data["parametros_celdas"][cell_key]["manual_is_open"]:
                                            btn.setText("🔴 Pendiente: Cerrar")
                                        else: btn.setText("🟢 Pendiente: Abrir")
                                return toggle
                            btn_toggle.clicked.connect(make_toggle(el))
                            widget_refs["toggle_btn"] = btn_toggle
                            flayout.addWidget(btn_toggle)
                        elif mode == "Ciclo":
                            form_layout = QHBoxLayout()
                            form_layout.setContentsMargins(0,0,0,0)
                            spin_s, spin_o, spin_c = QDoubleSpinBox(), QDoubleSpinBox(), QDoubleSpinBox()
                            for sp in (spin_s, spin_o, spin_c): sp.setRange(0.0, 999.9); sp.setDecimals(1)
                            spin_s.setValue(float(params.get("t_shift", 0.0)))
                            spin_o.setValue(float(params.get("t_open", 5.0)))
                            spin_c.setValue(float(params.get("t_close", 5.0)))

                            def make_callback(cell_key, param_key):
                                return lambda val: self.temp_step_data["parametros_celdas"][cell_key].update({param_key: float(val)}) if self.temp_step_data else None

                            spin_s.valueChanged.connect(make_callback(el, "t_shift"))
                            spin_o.valueChanged.connect(make_callback(el, "t_open"))
                            spin_c.valueChanged.connect(make_callback(el, "t_close"))

                            form_layout.addWidget(QLabel("S:")); form_layout.addWidget(spin_s)
                            form_layout.addWidget(QLabel("O:")); form_layout.addWidget(spin_o)
                            form_layout.addWidget(QLabel("C:")); form_layout.addWidget(spin_c)
                            flayout.addLayout(form_layout)
                    else:
                        if mode == "Ciclo":
                            lbl_times = QLabel(f"<span style='color: #7f8c8d; font-size: 11px;'>S: {params.get('t_shift',0.0):.1f}s | O: {params.get('t_open',5.0):.1f}s | C: {params.get('t_close',5.0):.1f}s</span>")
                            lbl_times.setStyleSheet("border: none;")
                            lbl_times.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            flayout.addWidget(lbl_times)
                            
                    self.cells_layout.addWidget(frame)
                    self.cell_widgets[el] = widget_refs
                self.cells_layout.addStretch()
                
            self.last_drawn_step_index = current_index
            self.last_drawn_lock_state = self.is_unlocked

        for el, params in step.get("parametros_celdas", {}).items():
            if el not in self.cell_widgets: continue
            
            is_open = active_states.get(el, False)
            color_str = "#27ae60" if is_open else "#e53935"
            
            self.cell_widgets[el]["status_lbl"].setText("ABIERTA" if is_open else "CERRADA")
            self.cell_widgets[el]["status_lbl"].setStyleSheet(f"border: none; color: {color_str}; font-size: 16px; font-weight: bold;")
            self.cell_widgets[el]["frame"].setStyleSheet(f"background: white; border: 2px solid {color_str}; border-radius: 6px; padding: 5px;")
            
            if "toggle_btn" in self.cell_widgets[el]:
                btn = self.cell_widgets[el]["toggle_btn"]
                intent_is_open = self.temp_step_data["parametros_celdas"][el].get("manual_is_open", True) if self.temp_step_data else is_open
                if "Pendiente" not in btn.text():
                    btn.setText("🔴 Preparar Cierre" if intent_is_open else "🟢 Preparar Apertura")
                    btn.setStyleSheet(f"background-color: {'#e53935' if intent_is_open else '#27ae60'}; color: white; border: none; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")

        self.timeline.set_active_cells(active_states)

    def launch_builder(self):
        try: subprocess.Popen([sys.executable, "builder.py"])
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo abrir builder.py:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    recipe_arg = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(recipe_arg)
    window.show()
    sys.exit(app.exec())