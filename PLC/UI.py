import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, 
                             QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QComboBox, QGroupBox, QFormLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen, QFont

# ==========================================
# MATERIAL DATABASE & ELEMENT MAPPING
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

# Define which elements are Group V to treat them differently in the UI
GROUP_V_ELEMENTS = ["As", "N"]

# ==========================================
# CUSTOM VISUAL MATERIAL ITEM
# ==========================================
class MaterialLayer(QGraphicsRectItem):
    def __init__(self, name, properties, y_pos):
        super().__init__(0, 0, 250, 30)
        self.name = name
        self.elements = properties["elements"]
        self.setBrush(QBrush(QColor(properties["color"])))
        self.default_pen = QPen(Qt.GlobalColor.black, 1)
        self.setPen(self.default_pen)
        
        # --- DYNAMIC LAYER PROPERTIES ---
        self.growth_time = 60.0 # Default 60s for the whole layer
        self.element_data = {}
        
        # Pre-populate dictionary with default values for each element
        for el in self.elements:
            if el in GROUP_V_ELEMENTS:
                self.element_data[el] = 5.0 # e.g., Flow/Overpressure default
            else:
                self.element_data[el] = 1.5 # e.g., Valve time/Temp default
        
        self.text = QGraphicsTextItem(name, self) 
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.text.setFont(font)
        text_rect = self.text.boundingRect()
        self.text.setPos((250 - text_rect.width()) / 2, (30 - text_rect.height()) / 2)
        
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable) 
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(50, y_pos)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.DashLine))
            else:
                self.setPen(self.default_pen)
        return super().itemChange(change, value)

# ==========================================
# MAIN VISUAL INTERFACE
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Heterostructure Recipe Builder")
        self.resize(1150, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ------------------------------------------
        # LEFT PANEL: VISUAL CANVAS & CONTROLS
        # ------------------------------------------
        left_panel = QVBoxLayout()
        self.scene = QGraphicsScene(0, 0, 350, 600)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints()) 
        left_panel.addWidget(QLabel("<b>Growth Chamber Canvas</b> (Drag to reorder)"))
        left_panel.addWidget(self.view)
        
        self.scene.selectionChanged.connect(self.on_layer_selected)
        self.current_drop_y = 500 

        controls_layout = QHBoxLayout()
        self.material_dropdown = QComboBox()
        
        self.material_dropdown.addItem("--- Base ---")
        self.material_dropdown.addItem("Silicon Substrate")
        self.material_dropdown.addItem("--- Arsenides (Binaries) ---")
        self.material_dropdown.addItems(["AlAs", "GaAs", "InAs"])
        self.material_dropdown.addItem("--- Arsenides (Ternaries) ---")
        self.material_dropdown.addItems(["InGaAs", "AlGaAs"])
        self.material_dropdown.addItem("--- Nitrides (Binaries) ---")
        self.material_dropdown.addItems(["AlN", "GaN", "InN"])
        self.material_dropdown.addItem("--- Nitrides (Ternaries) ---")
        self.material_dropdown.addItems(["AlGaN", "AlInN", "InGaN"])
        
        btn_add = QPushButton("Add Layer")
        btn_add.setStyleSheet("background-color: #f1c40f; font-weight: bold; padding: 5px 20px;")
        btn_add.clicked.connect(self.add_selected_layer)

        controls_layout.addWidget(self.material_dropdown)
        controls_layout.addWidget(btn_add)
        left_panel.addLayout(controls_layout)

        # ------------------------------------------
        # RIGHT PANEL: DYNAMIC PROPERTIES
        # ------------------------------------------
        right_panel = QVBoxLayout()
        
        self.props_group = QGroupBox("Dynamic Layer Properties")
        self.form_layout = QFormLayout()
        
        self.lbl_selected_mat = QLabel("<i>None selected</i>")
        self.form_layout.addRow("Material:", self.lbl_selected_mat)
        
        self.props_group.setLayout(self.form_layout)
        right_panel.addWidget(self.props_group)
        
        right_panel.addStretch()

        self.btn_compile = QPushButton("1. Compile Recipe")
        self.btn_compile.clicked.connect(self.compile_recipe)
        self.btn_execute = QPushButton("2. Print Final Array to Terminal")
        self.btn_execute.setEnabled(False) 
        self.btn_execute.clicked.connect(self.mock_execution)
        self.btn_clear = QPushButton("Clear Chamber")
        self.btn_clear.clicked.connect(self.clear_chamber)

        right_panel.addWidget(self.btn_compile)
        right_panel.addWidget(self.btn_execute)
        right_panel.addWidget(self.btn_clear)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 1)
        
        self.compiled_recipe = []
        self.dynamic_widgets = [] # Keep track of dynamically created input boxes

    # ==========================================
    # LOGIC & EVENTS
    # ==========================================
    def add_selected_layer(self):
        material_name = self.material_dropdown.currentText()
        if "---" in material_name: return 
            
        properties = MATERIAL_CATALOG.get(material_name, {"color":"#fff", "elements":[]}) 
        
        layer = MaterialLayer(material_name, properties, self.current_drop_y)
        self.scene.addItem(layer)
        self.current_drop_y -= 35 
        
        # Trigger selection immediately to force properties update
        self.scene.clearSelection()
        layer.setSelected(True)
        self.btn_execute.setEnabled(False) 

    def clear_properties_panel(self):
        # Remove everything except the very first row (Material Name label)
        while self.form_layout.rowCount() > 1:
            self.form_layout.removeRow(1)
        self.dynamic_widgets.clear()

    def on_layer_selected(self):
        selected_items = self.scene.selectedItems()
        self.clear_properties_panel()
        
        if not selected_items:
            self.lbl_selected_mat.setText("<i>None selected</i>")
            return
            
        item = selected_items[0]
        if isinstance(item, MaterialLayer):
            self.lbl_selected_mat.setText(f"<b>{item.name}</b>")
            
            # 1. Always add a general Growth Time input
            spin_growth = QDoubleSpinBox()
            spin_growth.setSuffix(" sec")
            spin_growth.setMaximum(10000.0)
            spin_growth.setValue(item.growth_time)
            spin_growth.valueChanged.connect(lambda val, i=item: self.update_growth_time(i, val))
            
            self.form_layout.addRow("Total Growth Time:", spin_growth)
            self.dynamic_widgets.append(spin_growth)

            # 2. Dynamically build element inputs based on the material's composition
            for el in item.elements:
                spin = QDoubleSpinBox()
                spin.setDecimals(2)
                spin.setMaximum(1000.0)
                
                # Check if it's Group V to assign different labels/units
                if el in GROUP_V_ELEMENTS:
                    label = f"🔥 {el} (Group V) Flow:"
                    spin.setSuffix(" sccm") # Example unit
                else:
                    label = f"⚙️ {el} (Group III) Valve Time:"
                    spin.setSuffix(" sec")
                    
                spin.setValue(item.element_data[el])
                
                # The lambda captures the current element 'el' and the item 'item'
                spin.valueChanged.connect(lambda val, e=el, i=item: self.update_element_data(i, e, val))
                
                self.form_layout.addRow(label, spin)
                self.dynamic_widgets.append(spin)

            # Force user focus to the first input box immediately after adding/selecting
            if self.dynamic_widgets:
                self.dynamic_widgets[0].setFocus()
                self.dynamic_widgets[0].selectAll()

    def update_growth_time(self, item, value):
        item.growth_time = value
        self.btn_execute.setEnabled(False) 

    def update_element_data(self, item, element, value):
        item.element_data[element] = value
        self.btn_execute.setEnabled(False)

    def compile_recipe(self):
        items = self.scene.items()
        rect_items = [item for item in items if isinstance(item, MaterialLayer)]
        if not rect_items: return

        sorted_items = sorted(rect_items, key=lambda item: item.pos().y(), reverse=True)
        self.compiled_recipe = []
        
        for index, item in enumerate(sorted_items):
            step_data = {
                "step": index + 1, 
                "material": item.name,
                "layer_growth_sec": item.growth_time,
                "element_parameters": item.element_data # Injects the dynamic dictionary!
            }
            self.compiled_recipe.append(step_data)
        
        self.btn_execute.setEnabled(True)
        print("Recipe compiled successfully.")

    def mock_execution(self):
        print("\n--- COMPILED JSON ARRAY READY FOR PLC ---")
        import json
        # Using json.dumps to print it beautifully in the terminal
        print(json.dumps(self.compiled_recipe, indent=4))
        print("-----------------------------------------\n")

    def clear_chamber(self):
        self.scene.clear()
        self.current_drop_y = 500
        self.btn_execute.setEnabled(False)
        self.clear_properties_panel()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())