import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, 
                             QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QComboBox, QGroupBox, QFormLayout, 
                             QDoubleSpinBox, QRadioButton, QButtonGroup, QFrame,
                             QScrollArea, QInputDialog) # Añadido QInputDialog
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPainter

# ==========================================
# CATÁLOGO DE MATERIALES Y ELEMENTOS
# ==========================================
MATERIAL_CATALOG = {
    "Silicon Substrate": {"color": "#bdc3c7", "elements": []}, 
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

GROUP_V_ELEMENTS = ["As", "N"]

# ==========================================
# WIDGET VISUAL PARA EL DIAGRAMA DE CICLO
# ==========================================
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

# ==========================================
# CAPA VISUAL PERSONALIZADA
# ==========================================
class MaterialLayer(QGraphicsRectItem):
    def __init__(self, name, properties, y_pos):
        super().__init__(0, 0, 310, 45)  # Ancho ajustado para dar espacio al comentario
        self.name = name
        self.elements = properties["elements"]
        self.comment = "" # Atributo para almacenar el comentario
        
        self.setBrush(QBrush(QColor(properties["color"])))
        self.default_pen = QPen(Qt.GlobalColor.black, 2)
        self.setPen(self.default_pen)
        
        self.growth_time = 60.0 
        self.element_data = {}
        
        for el in self.elements:
            self.element_data[el] = {
                "mode": "Continuo",
                "t_shift": 0.0,      
                "t_open": 5.0,           
                "t_close": 5.0           
            }
        
        # Texto principal de la capa
        self.text = QGraphicsTextItem(name, self) 
        font = QFont("Arial", 11, QFont.Weight.Bold)
        self.text.setFont(font)
        text_rect = self.text.boundingRect()
        self.text.setPos((310 - text_rect.width()) / 2, (45 - text_rect.height()) / 2)
        
        # Etiqueta visual para el comentario (inicialmente vacía)
        self.comment_text = QGraphicsTextItem("", self)
        comment_font = QFont("Arial", 9)
        comment_font.setItalic(True) # Forma correcta en PyQt6 para la cursiva
        self.comment_text.setFont(comment_font)
        self.comment_text.setDefaultTextColor(QColor("#f39c12"))
        
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable) 
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(25, y_pos)

    def set_comment(self, comment):
        self.comment = comment
        if comment:
            self.comment_text.setPlainText(f"💬 {comment}")
        else:
            self.comment_text.setPlainText("")
        
        # Reajustar la posición para que aparezca exactamente a la derecha de la capa
        rect_width = self.rect().width()
        self.comment_text.setPos(rect_width + 10, (45 - self.comment_text.boundingRect().height()) / 2)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.DashLine))
            else:
                self.setPen(self.default_pen)
        return super().itemChange(change, value)

# ==========================================
# INTERFAZ GRÁFICA PRINCIPAL
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Heterostructure Recipe Builder - Celdas MBE")
        self.resize(1250, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ------------------------------------------
        # PANEL IZQUIERDO: Canvas (Cámara)
        # ------------------------------------------
        left_panel = QVBoxLayout()
        self.scene = QGraphicsScene(0, 0, 500, 750) # Espacio ampliado horizontalmente para comentarios
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints()) 
        left_panel.addWidget(QLabel("<b>Cámara de Crecimiento</b> (Haz clic en una capa)"))
        left_panel.addWidget(self.view)
        
        self.scene.selectionChanged.connect(self.on_layer_selected)
        self.current_drop_y = 650 

        controls_layout = QHBoxLayout()
        self.material_dropdown = QComboBox()
        self.material_dropdown.addItem("--- Base ---")
        self.material_dropdown.addItem("Silicon Substrate")
        self.material_dropdown.addItem("--- Arsenuros (Binarios) ---")
        self.material_dropdown.addItems(["AlAs", "GaAs", "InAs"])
        self.material_dropdown.addItem("--- Arsenuros (Ternarios) ---")
        self.material_dropdown.addItems(["InGaAs", "AlGaAs"])
        
        btn_add = QPushButton("Agregar Capa")
        btn_add.setStyleSheet("background-color: #f1c40f; color: black; font-weight: bold; padding: 6px 15px;")
        btn_add.clicked.connect(self.add_selected_layer)

        controls_layout.addWidget(self.material_dropdown)
        controls_layout.addWidget(btn_add)
        left_panel.addLayout(controls_layout)

        # ------------------------------------------
        # PANEL DERECHO: ScrollArea y Botones
        # ------------------------------------------
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
        
        # --- NUEVO BOTÓN: AGREGAR COMENTARIO ---
        self.btn_comment = QPushButton("💬 Agregar Comentario")
        self.btn_comment.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px;")
        self.btn_comment.setEnabled(False)
        self.btn_comment.clicked.connect(self.open_comment_dialog)
        right_panel.addWidget(self.btn_comment)
        
        # Botón existente para eliminar capa
        self.btn_delete = QPushButton("🗑️ Eliminar Capa")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.delete_selected_layer)
        right_panel.addWidget(self.btn_delete)

        self.btn_compile = QPushButton("1. Compilar Receta")
        self.btn_compile.clicked.connect(self.compile_recipe)
        self.btn_execute = QPushButton("2. Imprimir Array")
        self.btn_execute.setEnabled(False) 
        self.btn_execute.clicked.connect(self.mock_execution)

        right_panel.addWidget(self.btn_compile)
        right_panel.addWidget(self.btn_execute)

        main_layout.addLayout(left_panel, 1) 
        main_layout.addLayout(right_panel, 1) 
        
        self.compiled_recipe = []
        self.current_selected_layer = None
        self.active_diagrams = []

    # ==========================================
    # LÓGICA
    # ==========================================
    def add_selected_layer(self):
        material_name = self.material_dropdown.currentText()
        if "---" in material_name: return 
            
        properties = MATERIAL_CATALOG.get(material_name, {"color":"#fff", "elements":[]}) 
        layer = MaterialLayer(material_name, properties, self.current_drop_y)
        self.scene.addItem(layer)
        self.current_drop_y -= 50 
        
        self.scene.clearSelection()
        layer.setSelected(True)
        self.btn_execute.setEnabled(False) 

    def clear_properties_panel(self):
        while self.form_layout.rowCount() > 1:
            self.form_layout.removeRow(1)
        self.active_diagrams.clear()

    def open_comment_dialog(self):
        if not self.current_selected_layer: return
        
        current_text = self.current_selected_layer.comment
        text, ok = QInputDialog.getText(self, "Agregar Comentario", "Comentario para la capa:", text=current_text)
        if ok:
            self.current_selected_layer.set_comment(text)
            self.btn_execute.setEnabled(False)

    def on_layer_selected(self):
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
            self.btn_comment.setEnabled(True) # Habilitar botón de comentario
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

    def update_growth_time(self, item, value):
        item.growth_time = value
        self.btn_execute.setEnabled(False)
        for diag in self.active_diagrams:
            el = diag.element
            diag.update_values(item.element_data[el]["t_shift"], item.element_data[el]["t_open"], item.element_data[el]["t_close"], value)

    def update_mode(self, item, element, mode):
        item.element_data[element]["mode"] = mode
        self.btn_execute.setEnabled(False)

    def update_cycle_shift(self, item, element, value, diagram):
        item.element_data[element]["t_shift"] = value
        self.btn_execute.setEnabled(False)
        diagram.update_values(value, item.element_data[element]["t_open"], item.element_data[element]["t_close"], item.growth_time)

    def update_cycle_open(self, item, element, value, diagram):
        item.element_data[element]["t_open"] = value
        self.btn_execute.setEnabled(False)
        diagram.update_values(item.element_data[element]["t_shift"], value, item.element_data[element]["t_close"], item.growth_time)

    def update_cycle_close(self, item, element, value, diagram):
        item.element_data[element]["t_close"] = value
        self.btn_execute.setEnabled(False)
        diagram.update_values(item.element_data[element]["t_shift"], item.element_data[element]["t_open"], value, item.growth_time)

    def delete_selected_layer(self):
        if not self.current_selected_layer: return
        deleted_y = self.current_selected_layer.y()
        self.scene.removeItem(self.current_selected_layer)
        self.current_selected_layer = None
        self.clear_properties_panel()
        self.lbl_selected_mat.setText("<i>Ninguna capa seleccionada</i>")
        self.btn_delete.setEnabled(False)
        self.btn_comment.setEnabled(False)
        
        for item in self.scene.items():
            if isinstance(item, MaterialLayer):
                if item.y() < deleted_y:
                    item.setY(item.y() + 50)
        self.current_drop_y += 50

    def compile_recipe(self):
        items = self.scene.items()
        rect_items = [item for item in items if isinstance(item, MaterialLayer)]
        if not rect_items: return

        sorted_items = sorted(rect_items, key=lambda item: item.pos().y(), reverse=True)
        self.compiled_recipe = []
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
                "comentario": item.comment, # Se incluye el comentario en el JSON
                "tiempo_total_crecimiento_sec": item.growth_time,
                "parametros_celdas": clean_element_data 
            }
            self.compiled_recipe.append(step_data)
        self.btn_execute.setEnabled(True)

    def mock_execution(self):
        print(json.dumps(self.compiled_recipe, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())