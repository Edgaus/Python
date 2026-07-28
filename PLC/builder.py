import sys
import json
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, 
                             QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QComboBox, QGroupBox, QFormLayout, 
                             QDoubleSpinBox, QRadioButton, QButtonGroup, QFrame,
                             QScrollArea, QDialog, QTextEdit, QStyledItemDelegate,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPainter
from PyQt6.QtWidgets import QStyle

MATERIAL_CATALOG = {
    "Silicon Substrate": {"color": "#bdc3c7", "elements": [], "display_name": "Sustrato (Silicio)"}, 
    "GaAs Substrate": {"color": "#95a5a6", "elements": [], "display_name": "Sustrato (GaAs)"}, 
    "Sapphire Substrate": {"color": "#7f8c8d", "elements": [], "display_name": "Sustrato (Zafiro)"},
    "AlAs": {"color": "#e74c3c", "elements": ["Al", "As"]}, 
    "GaAs": {"color": "#3498db", "elements": ["Ga", "As"]}, 
    "InAs": {"color": "#9b59b6", "elements": ["In", "As"]},              
    "InGaAs": {"color": "#1abc9c", "elements": ["In", "Ga", "As"]}, 
    "AlGaAs": {"color": "#f1c40f", "elements": ["Al", "Ga", "As"]},            
    "AlN": {"color": "#e67e22", "elements": ["Al", "N"]}, 
    "GaN": {"color": "#2ecc71", "elements": ["Ga", "N"]}, 
    "InN": {"color": "#34495e", "elements": ["In", "N"]},               
    "AlGaN": {"color": "#16a085", "elements": ["Al", "Ga", "N"]}, 
    "AlInN": {"color": "#27ae60", "elements": ["Al", "In", "N"]}, 
    "InGaN": {"color": "#8e44ad", "elements": ["In", "Ga", "N"]}              
}

SUBSTRATE_TYPES = ["Silicon Substrate", "GaAs Substrate", "Sapphire Substrate"]

class CommentDialog(QDialog):
    def __init__(self, current_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Comentario")
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Escribe las observaciones o notas de la capa:"))
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(current_text)
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_save.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px;")
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 6px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
    def get_comment(self):
        return self.text_edit.toPlainText()

class TimingDiagramWidget(QWidget):
    def __init__(self, element, t_shift, t_open, t_close, total_growth, parent=None):
        super().__init__(parent)
        self.element = element
        self.t_shift = t_shift
        self.t_open = t_open
        self.t_close = t_close
        self.total_growth = total_growth
        self.setMinimumHeight(170) 
        
    def update_values(self, t_shift, t_open, t_close, total_growth):
        self.t_shift = t_shift
        self.t_open = t_open
        self.t_close = t_close
        self.total_growth = total_growth
        self.update() 
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor("#222222") 
        blue_fill = QColor("#2980b9") 
        line_color = QColor("#7f8c8d") 
        text_color = QColor("#ecf0f1") 
        
        width = self.width()
        height = self.height()
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 8, 8)
        
        margin_left = 130  
        margin_right = 90
        draw_width = width - margin_left - margin_right
        
        period = self.t_shift + self.t_open + self.t_close
        if period <= 0: return
        
        shift_px = int((self.t_shift / period) * draw_width)
        open_px = int((self.t_open / period) * draw_width)
        close_px = int((self.t_close / period) * draw_width)
        
        rect_y = 55
        rect_h = 40
        
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 8, width, 20), Qt.AlignmentFlag.AlignCenter, self.element)
        
        painter.setPen(QPen(line_color, 1.5))
        if shift_px > 0:
            painter.drawLine(margin_left, rect_y + rect_h, margin_left + shift_px, rect_y + rect_h)
            painter.drawLine(margin_left + shift_px, rect_y + rect_h, margin_left + shift_px, rect_y)
        
        if open_px > 0:
            painter.setBrush(QBrush(blue_fill))
            painter.setPen(QPen(blue_fill.darker(150), 1))
            painter.drawRect(margin_left + shift_px, rect_y, open_px, rect_h)
            
        if close_px > 0:
            painter.setPen(QPen(line_color, 1.5))
            painter.drawLine(margin_left + shift_px + open_px, rect_y, margin_left + shift_px + open_px, rect_y + rect_h)
            painter.drawLine(margin_left + shift_px + open_px, rect_y + rect_h, margin_left + shift_px + open_px + close_px, rect_y + rect_h)
        
        painter.setPen(QPen(line_color, 1, Qt.PenStyle.DashLine))
        painter.drawLine(margin_left, rect_y - 15, margin_left, rect_y + rect_h + 25)
        painter.drawLine(margin_left + draw_width, rect_y - 15, margin_left + draw_width, rect_y + rect_h + 25)
        
        arrow_y = rect_y + rect_h + 15
        painter.setPen(QPen(line_color, 1.5))
        painter.drawLine(margin_left, arrow_y, margin_left + draw_width, arrow_y)
        painter.drawLine(margin_left, arrow_y, margin_left + 6, arrow_y - 4)
        painter.drawLine(margin_left, arrow_y, margin_left + 6, arrow_y + 4)
        painter.drawLine(margin_left + draw_width, arrow_y, margin_left + draw_width - 6, arrow_y - 4)
        painter.drawLine(margin_left + draw_width, arrow_y, margin_left + draw_width - 6, arrow_y + 4)
        
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("Arial", 9))
        
        t1 = self.t_shift
        t2 = self.t_shift + self.t_open
        
        y_text = rect_y - 8
        if self.t_shift > 0:
            painter.drawText(15, y_text, "Shift:")
            painter.drawText(15, y_text + 15, f"0.00s - {t1:.2f}s")
            y_text += 32
            
        painter.drawText(15, y_text, "Open:")
        painter.drawText(15, y_text + 15, f"{t1:.2f}s - {t2:.2f}s")
        y_text += 32
        
        painter.drawText(15, y_text, "Close:")
        painter.drawText(15, y_text + 15, f"{t2:.2f}s - {period:.2f}s")
        
        painter.drawText(QRectF(margin_left, arrow_y + 6, draw_width, 20), Qt.AlignmentFlag.AlignCenter, f"Total cycle: {period:.2f}s")
        
        cycles = self.total_growth / period if period > 0 else 0
        painter.drawText(width - margin_right + 15, rect_y + 15, "Cycles:")
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(width - margin_right + 15, rect_y + 35, f"{cycles:.1f}")

class MaterialLayer(QGraphicsRectItem):
    def __init__(self, name, properties, y_pos):
        super().__init__(0, 0, 310, 45)  
        self.name = name
        self.elements = properties["elements"]
        self.comment = "" 
        
        self.is_substrate = ("Substrate" in name or name in SUBSTRATE_TYPES)
        self.growth_time = 0.0 if self.is_substrate else 60.0 
        
        self.setBrush(QBrush(QColor(properties.get("color", "#bdc3c7"))))
        self.default_pen = QPen(Qt.GlobalColor.black, 2)
        self.setPen(self.default_pen)
        
        self.element_data = {}
        for el in self.elements:
            self.element_data[el] = {
                "mode": "Continuo",
                "t_shift": 0.0,      
                "t_open": 5.0,           
                "t_close": 5.0           
            }
        
        display_text = f"Sustrato ({name.replace(' Substrate', '')})" if self.is_substrate else name
        self.text = QGraphicsTextItem(display_text, self) 
        font = QFont("Arial", 11, QFont.Weight.Bold)
        self.text.setFont(font)
        
        self.comment_text = QGraphicsTextItem("", self)
        comment_font = QFont("Arial", 9)
        comment_font.setItalic(True)
        self.comment_text.setFont(comment_font)
        self.comment_text.setDefaultTextColor(QColor("#f39c12")) 
        
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable) 
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(25, y_pos)
        self.update_layout()

    def update_material(self, new_name, new_color):
        self.name = new_name
        self.setBrush(QBrush(QColor(new_color)))
        display_text = f"Sustrato ({new_name.replace(' Substrate', '')})"
        self.text.setPlainText(display_text)
        self.update_layout()

    def set_comment(self, comment):
        self.comment = comment
        if comment:
            self.comment_text.setPlainText(f"💬 {comment}")
        else:
            self.comment_text.setPlainText("")
        self.update_layout()

    def update_layout(self):
        base_height = 45
        self.setRect(0, 0, 310, base_height)
        text_rect = self.text.boundingRect()
        self.text.setPos((310 - text_rect.width()) / 2, (base_height - text_rect.height()) / 2)
        self.comment_text.setPos(320, 0)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.DashLine))
            else:
                self.setPen(self.default_pen)
        return super().itemChange(change, value)

class BuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diseñador de Recetas MBE (Builder)")
        self.resize(1250, 800)

        self.is_loading = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QVBoxLayout()
        self.scene = QGraphicsScene(0, 0, 550, 750) 
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints()) 
        left_panel.addWidget(QLabel("<b>Cámara de Crecimiento</b> (Haz clic en una capa)"))
        left_panel.addWidget(self.view)
        
        self.scene.selectionChanged.connect(self.on_layer_selected)
        self.current_drop_y = 650 

        controls_layout = QHBoxLayout()
        self.material_dropdown = QComboBox()
        
        class ComboBoxDelegate(QStyledItemDelegate):
            def paint(self, painter, option, index):
                text = index.data()
                if "---" in text:
                    option.state &= ~QStyle.StateFlag.State_Enabled
                super().paint(painter, option, index)

        self.material_dropdown.setItemDelegate(ComboBoxDelegate(self.material_dropdown))
        self.populate_dropdown()
        
        self.btn_add = QPushButton("Agregar Capa")
        self.btn_add.setStyleSheet("background-color: #f1c40f; color: black; font-weight: bold; padding: 6px 15px;")
        self.btn_add.clicked.connect(self.add_selected_layer)

        controls_layout.addWidget(self.material_dropdown)
        controls_layout.addWidget(self.btn_add)
        left_panel.addLayout(controls_layout)

        right_panel = QVBoxLayout()
        
        self.props_group = QGroupBox("Propiedades Dinámicas de la Capa")
        self.form_layout = QFormLayout()
        
        self.lbl_selected_mat = QLabel("<i>Ninguna capa seleccionada</i>")
        self.form_layout.addRow("Material:", self.lbl_selected_mat)
        self.props_group.setLayout(self.form_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) 
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame) 
        self.scroll_area.setWidget(self.props_group)
        
        right_panel.addWidget(self.scroll_area)
        
        self.btn_comment = QPushButton("💬 Agregar Comentario")
        self.btn_comment.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px;")
        self.btn_comment.setEnabled(False)
        self.btn_comment.clicked.connect(self.open_comment_dialog)
        right_panel.addWidget(self.btn_comment)
        
        self.btn_delete = QPushButton("🗑️ Eliminar Capa")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.delete_selected_layer)
        right_panel.addWidget(self.btn_delete)

        file_io_layout = QHBoxLayout()
        self.btn_save_recipe = QPushButton("💾 Guardar Receta")
        self.btn_save_recipe.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 6px;")
        self.btn_save_recipe.clicked.connect(self.save_recipe_file)
        
        self.btn_load_recipe = QPushButton("📂 Cargar Receta")
        self.btn_load_recipe.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; padding: 6px;")
        self.btn_load_recipe.clicked.connect(self.load_recipe_file)
        
        file_io_layout.addWidget(self.btn_save_recipe)
        file_io_layout.addWidget(self.btn_load_recipe)
        right_panel.addLayout(file_io_layout)

        # Botón "Cocinar"
        self.btn_cook = QPushButton("🍳 Cocinar")
        self.btn_cook.setStyleSheet("background-color: #d35400; color: white; font-weight: bold; padding: 10px; font-size: 12pt;")
        self.btn_cook.clicked.connect(self.cook_recipe)
        right_panel.addWidget(self.btn_cook)

        main_layout.addLayout(left_panel, 1) 
        main_layout.addLayout(right_panel, 1) 
        
        self.current_selected_layer = None
        self.active_diagrams = []
        self.btn_apply_sub = None

        self.glow_state = False
        self.active_glow_button = None 

        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.animate_glow)

        self.init_default_substrate()

    def start_glow(self, color_type):
        if self.is_loading: return
        self.active_glow_button = color_type
        self.glow_state = False
        self.glow_timer.start(500)

    def stop_glow(self):
        self.glow_timer.stop()
        self.active_glow_button = None
        if hasattr(self, 'btn_apply_sub') and self.btn_apply_sub is not None:
            try:
                self.btn_apply_sub.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 6px;")
            except RuntimeError:
                pass
        self.btn_add.setStyleSheet("background-color: #f1c40f; color: black; font-weight: bold; padding: 6px 15px;")

    def animate_glow(self):
        self.glow_state = not self.glow_state
        if self.active_glow_button == 'green' and hasattr(self, 'btn_apply_sub') and self.btn_apply_sub is not None:
            try:
                if self.glow_state:
                    self.btn_apply_sub.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px; border: 3px solid #ffffff;")
                else:
                    self.btn_apply_sub.setStyleSheet("background-color: #1e8449; color: white; font-weight: bold; padding: 6px; border: 3px solid #f39c12;")
            except RuntimeError:
                pass
        elif self.active_glow_button == 'yellow':
            if self.glow_state:
                self.btn_add.setStyleSheet("background-color: #f1c40f; color: black; font-weight: bold; padding: 6px 15px; border: 3px solid #ffffff;")
            else:
                self.btn_add.setStyleSheet("background-color: #b7950b; color: white; font-weight: bold; padding: 6px 15px; border: 3px solid #ffffff;")

    def populate_dropdown(self):
        self.material_dropdown.clear()
        has_substrate = any(isinstance(item, MaterialLayer) and item.is_substrate for item in self.scene.items())
        
        if not has_substrate:
            self.material_dropdown.addItem("--- Base ---")
            self.material_dropdown.addItem("Silicon Substrate")
            
        self.material_dropdown.addItem("--- Arsenuros (Binarios) ---")
        self.material_dropdown.addItems(["AlAs", "GaAs", "InAs"])
        self.material_dropdown.addItem("--- Arsenuros (Ternarios) ---")
        self.material_dropdown.addItems(["InGaAs", "AlGaAs"])

    def init_default_substrate(self):
        properties = MATERIAL_CATALOG.get("Silicon Substrate")
        layer = MaterialLayer("Silicon Substrate", properties, 650) 
        self.scene.addItem(layer)
        self.populate_dropdown()
        layer.setSelected(True)

    def add_selected_layer(self):
        if self.active_glow_button == 'yellow':
            self.stop_glow()

        material_name = self.material_dropdown.currentText()
        if "---" in material_name: 
            return 
            
        properties = MATERIAL_CATALOG.get(material_name, {"color":"#fff", "elements":[]}) 
        layer = MaterialLayer(material_name, properties, 0) 
        self.scene.addItem(layer)
        
        self.reorganize_layers()

        if layer.is_substrate:
            self.populate_dropdown()

        self.scene.clearSelection()
        layer.setSelected(True)

    def reorganize_layers(self):
        layers = [item for item in self.scene.items() if isinstance(item, MaterialLayer)]
        substrate_layers = [l for l in layers if l.is_substrate]
        active_layers = [l for l in layers if not l.is_substrate]
        
        current_y = 650
        for sub in substrate_layers:
            sub.setY(current_y)
            current_y -= 55 
            
        for layer in active_layers:
            layer.setY(current_y)
            current_y -= 55 
            
        self.current_drop_y = current_y

    def clear_properties_panel(self):
        self.btn_apply_sub = None
        while self.form_layout.rowCount() > 1:
            self.form_layout.removeRow(1)
        self.active_diagrams.clear()

    def open_comment_dialog(self):
        if not self.current_selected_layer: return
        dialog = CommentDialog(self.current_selected_layer.comment, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            comment_text = dialog.get_comment()
            self.current_selected_layer.set_comment(comment_text)

    def on_layer_selected(self):
        if self.is_loading: return

        self.props_group.setUpdatesEnabled(False) 
        selected_items = self.scene.selectedItems()
        self.clear_properties_panel()
        
        if not selected_items:
            self.lbl_selected_mat.setText("<i>Ninguna capa seleccionada</i>")
            self.btn_delete.setEnabled(False)
            self.btn_comment.setEnabled(False)
            self.current_selected_layer = None
            self.props_group.setUpdatesEnabled(True)
            return
            
        item = selected_items[0]
        if isinstance(item, MaterialLayer):
            self.current_selected_layer = item
            self.btn_delete.setEnabled(True)
            self.btn_comment.setEnabled(True) 
            
            if item.is_substrate:
                self.lbl_selected_mat.setText("<b>Sustrato Base</b>")
                
                self.substrate_combo = QComboBox()
                self.substrate_combo.addItems(SUBSTRATE_TYPES)
                
                index = self.substrate_combo.findText(item.name)
                if index >= 0:
                    self.substrate_combo.setCurrentIndex(index)
                
                self.form_layout.addRow("Tipo de Sustrato:", self.substrate_combo)
                
                self.btn_apply_sub = QPushButton("✓ Confirmar Tipo de Sustrato")
                self.btn_apply_sub.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 6px;")
                self.btn_apply_sub.clicked.connect(lambda: self.apply_substrate_change(item))
                self.form_layout.addRow(self.btn_apply_sub)
                
                self.start_glow('green')
                
            else:
                self.lbl_selected_mat.setText(f"<b>{item.name}</b>")
                
                spin_growth = QDoubleSpinBox()
                spin_growth.setSuffix(" sec")
                spin_growth.setMaximum(10000.0)
                spin_growth.setValue(item.growth_time)
                spin_growth.valueChanged.connect(lambda val, i=item: self.update_growth_time(i, val))
                self.form_layout.addRow("Tiempo Total Crecimiento:", spin_growth)

                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                self.form_layout.addRow(line)

                for el in item.elements:
                    element_box = QGroupBox(f"Celda: {el}")
                    elem_layout = QVBoxLayout()

                    mode_layout = QHBoxLayout()
                    rb_continuo = QRadioButton("Continuo")
                    rb_ciclo = QRadioButton("Ciclo")
                    
                    btn_group = QButtonGroup(element_box)
                    btn_group.addButton(rb_continuo)
                    btn_group.addButton(rb_ciclo)

                    current_mode = item.element_data[el]["mode"]
                    if current_mode == "Continuo":
                        rb_continuo.setChecked(True)
                    else:
                        rb_ciclo.setChecked(True)

                    mode_layout.addWidget(rb_continuo)
                    mode_layout.addWidget(rb_ciclo)
                    elem_layout.addLayout(mode_layout)

                    widget_ciclo = QWidget()
                    layout_ciclo = QVBoxLayout(widget_ciclo)
                    
                    inputs_layout = QFormLayout()
                    spin_tshift = QDoubleSpinBox()
                    spin_tshift.setSuffix(" sec")
                    spin_tshift.setValue(item.element_data[el]["t_shift"])
                    
                    spin_topen = QDoubleSpinBox()
                    spin_topen.setSuffix(" sec")
                    spin_topen.setValue(item.element_data[el]["t_open"])
                    
                    spin_tclose = QDoubleSpinBox()
                    spin_tclose.setSuffix(" sec")
                    spin_tclose.setValue(item.element_data[el]["t_close"])
                    
                    inputs_layout.addRow("T. Desplazamiento (Shift):", spin_tshift)
                    inputs_layout.addRow("T. Apertura (Open):", spin_topen)
                    inputs_layout.addRow("T. Cierre (Close):", spin_tclose)
                    layout_ciclo.addLayout(inputs_layout)
                    
                    t_shift = item.element_data[el]["t_shift"]
                    t_open = item.element_data[el]["t_open"]
                    t_close = item.element_data[el]["t_close"]
                    diagram = TimingDiagramWidget(el, t_shift, t_open, t_close, item.growth_time)
                    layout_ciclo.addWidget(diagram)
                    self.active_diagrams.append(diagram)
                    
                    spin_tshift.valueChanged.connect(lambda val, e=el, i=item, diag=diagram: self.update_cycle_shift(i, e, val, diag))
                    spin_topen.valueChanged.connect(lambda val, e=el, i=item, diag=diagram: self.update_cycle_open(i, e, val, diag))
                    spin_tclose.valueChanged.connect(lambda val, e=el, i=item, diag=diagram: self.update_cycle_close(i, e, val, diag))

                    elem_layout.addWidget(widget_ciclo)
                    widget_ciclo.setVisible(current_mode == "Ciclo")

                    rb_continuo.toggled.connect(lambda checked, e=el, i=item, w=widget_ciclo: (
                        self.update_mode(i, e, "Continuo") if checked else None,
                        w.setVisible(False) if checked else None
                    ))
                    rb_ciclo.toggled.connect(lambda checked, e=el, i=item, w=widget_ciclo: (
                        self.update_mode(i, e, "Ciclo") if checked else None,
                        w.setVisible(True) if checked else None
                    ))

                    element_box.setLayout(elem_layout)
                    self.form_layout.addRow(element_box)

        self.props_group.setUpdatesEnabled(True)

    def apply_substrate_change(self, item):
        self.stop_glow()
        new_name = self.substrate_combo.currentText()
        properties = MATERIAL_CATALOG.get(new_name, {"color": "#bdc3c7"})
        item.update_material(new_name, properties["color"])
        self.start_glow('yellow')

    def update_growth_time(self, item, value):
        item.growth_time = value
        for diag in self.active_diagrams:
            el = diag.element
            diag.update_values(item.element_data[el]["t_shift"], item.element_data[el]["t_open"], item.element_data[el]["t_close"], value)

    def update_mode(self, item, element, mode):
        item.element_data[element]["mode"] = mode

    def update_cycle_shift(self, item, element, value, diagram):
        item.element_data[element]["t_shift"] = value
        diagram.update_values(value, item.element_data[element]["t_open"], item.element_data[element]["t_close"], item.growth_time)

    def update_cycle_open(self, item, element, value, diagram):
        item.element_data[element]["t_open"] = value
        diagram.update_values(item.element_data[element]["t_shift"], value, item.element_data[element]["t_close"], item.growth_time)

    def update_cycle_close(self, item, element, value, diagram):
        item.element_data[element]["t_close"] = value
        diagram.update_values(item.element_data[element]["t_shift"], item.element_data[element]["t_open"], value, item.growth_time)

    def delete_selected_layer(self):
        if not self.current_selected_layer: return
        is_sub = self.current_selected_layer.is_substrate
        
        self.scene.removeItem(self.current_selected_layer)
        self.current_selected_layer = None
        self.clear_properties_panel()
        self.lbl_selected_mat.setText("<i>Ninguna capa seleccionada</i>")
        self.btn_delete.setEnabled(False)
        self.btn_comment.setEnabled(False)
        
        self.reorganize_layers()
        if is_sub:
            self.populate_dropdown()

    def compile_recipe(self):
        items = self.scene.items()
        rect_items = [item for item in items if isinstance(item, MaterialLayer)]
        if not rect_items: return []

        sorted_items = sorted(rect_items, key=lambda item: item.pos().y(), reverse=True)
        compiled_recipe = []
        for index, item in enumerate(sorted_items):
            clean_element_data = {}
            for el, data in item.element_data.items():
                if data["mode"] == "Continuo":
                    clean_element_data[el] = {"mode": "Continuo"}
                else:
                    clean_element_data[el] = data
            
            step_data = {
                "paso": index + 1, 
                "material": item.name,
                "comentario": item.comment, 
            }
            if not item.is_substrate:
                step_data["tiempo_total_crecimiento_sec"] = item.growth_time
                step_data["parametros_celdas"] = clean_element_data
            else:
                step_data["tiempo_total_crecimiento_sec"] = 0.0
                step_data["parametros_celdas"] = {}

            compiled_recipe.append(step_data)
        return compiled_recipe

    def cook_recipe(self):
        recipe_data = self.compile_recipe()
        if not recipe_data:
            QMessageBox.warning(self, "Advertencia", "No hay capas en la cámara para cocinar.")
            return

        json_filename = "receta_actual.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(recipe_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el archivo JSON:\n{e}")
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmación de Crecimiento")
        msg_box.setText("<b>¡Receta lista para ser procesada!</b><br><br>Presiona [Enter] o confirma para abrir el Monitor Principal con la Línea de Tiempo.")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        btn_yes = msg_box.addButton("Sí, Abrir Monitor", QMessageBox.ButtonRole.AcceptRole)
        btn_no = msg_box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(btn_yes)
        
        msg_box.exec()

        if msg_box.clickedButton() == btn_yes:
            # Lanza el programa principal (main.py) pasándole el archivo json
            try:
                subprocess.Popen([sys.executable, "main.py", json_filename])
                self.close() # Cierra la ventana del diseñador
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo iniciar main.py:\n{e}")

    def save_recipe_file(self):
        items = [item for item in self.scene.items() if isinstance(item, MaterialLayer)]
        if not items:
            QMessageBox.warning(self, "Advertencia", "No hay capas para guardar en la receta.")
            return

        sorted_items = sorted(items, key=lambda item: item.pos().y(), reverse=True)
        recipe_data = []

        for item in sorted_items:
            layer_info = {
                "name": item.name,
                "is_substrate": item.is_substrate,
                "growth_time": item.growth_time,
                "comment": item.comment,
                "element_data": item.element_data
            }
            recipe_data.append(layer_info)

        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Receta MBE", "", "Archivos JSON (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(recipe_data, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "Éxito", "Receta guardada correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{e}")

    def load_recipe_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Cargar Receta MBE", "", "Archivos JSON (*.json)")
        if file_path:
            try:
                self.is_loading = True
                self.stop_glow()

                with open(file_path, 'r', encoding='utf-8') as f:
                    recipe_data = json.load(f)

                self.scene.clearSelection()
                for item in list(self.scene.items()):
                    if isinstance(item, MaterialLayer):
                        self.scene.removeItem(item)

                self.clear_properties_panel()
                self.current_selected_layer = None
                self.btn_delete.setEnabled(False)
                self.btn_comment.setEnabled(False)

                current_y = 650
                for data in recipe_data:
                    name = data["name"]
                    properties = MATERIAL_CATALOG.get(name, {"color": "#bdc3c7", "elements": []})
                    
                    layer = MaterialLayer(name, properties, current_y)
                    layer.growth_time = data.get("growth_time", 60.0)
                    layer.set_comment(data.get("comment", ""))
                    layer.element_data = data.get("element_data", {})
                    
                    self.scene.addItem(layer)

                self.reorganize_layers()
                self.populate_dropdown()

                self.is_loading = False
                substrate_items = [item for item in self.scene.items() if isinstance(item, MaterialLayer) and item.is_substrate]
                if substrate_items:
                    substrate_items[0].setSelected(True)

                QMessageBox.information(self, "Éxito", "Receta cargada correctamente.")

            except Exception as e:
                self.is_loading = False
                QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BuilderWindow()
    window.show()
    sys.exit(app.exec())