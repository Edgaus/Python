import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, 
                             QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QListWidget, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen, QFont

# ==========================================
# MATERIAL DATABASE (Name to Color Mapping)
# ==========================================
MATERIAL_CATALOG = {
    "Silicon Substrate": "#bdc3c7", # Gray
    "AlAs": "#e74c3c",              # Red
    "GaAs": "#3498db",              # Blue
    "InAs": "#9b59b6",              # Purple
    "InGaAs": "#1abc9c",            # Teal
    "AlGaAs": "#f1c40f",            # Yellow
    "AlN": "#e67e22",               # Orange
    "GaN": "#2ecc71",               # Green
    "InN": "#34495e",               # Dark Blue
    "AlGaN": "#16a085",             # Dark Teal
    "AlInN": "#27ae60",             # Dark Green
    "InGaN": "#8e44ad"              # Dark Purple
}

# ==========================================
# CUSTOM VISUAL MATERIAL ITEM
# ==========================================
class MaterialLayer(QGraphicsRectItem):
    def __init__(self, name, color, y_pos):
        super().__init__(0, 0, 250, 30)
        self.name = name
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.GlobalColor.black))
        
        # --- ADD TEXT TO THE BLOCK ---
        self.text = QGraphicsTextItem(name, self) # 'self' makes it a child of the rectangle
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.text.setFont(font)
        
        # Center the text inside the rectangle
        text_rect = self.text.boundingRect()
        x_offset = (250 - text_rect.width()) / 2
        y_offset = (30 - text_rect.height()) / 2
        self.text.setPos(x_offset, y_offset)
        
        # Enable dragging
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(50, y_pos)

# ==========================================
# MAIN VISUAL INTERFACE
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Heterostructure Recipe Builder")
        self.resize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # -- LEFT PANEL: VISUAL CANVAS & CONTROLS --
        left_panel = QVBoxLayout()
        
        # 1. Canvas
        self.scene = QGraphicsScene(0, 0, 350, 600)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints()) 
        left_panel.addWidget(QLabel("<b>Growth Chamber Canvas</b> (Drag blocks to reorder)"))
        left_panel.addWidget(self.view)
        
        self.current_drop_y = 500 

        # 2. Material Dropdown and Add Button
        controls_layout = QHBoxLayout()
        
        self.material_dropdown = QComboBox()
        # Add categories and items to dropdown
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
        
        # Yellow Add Button
        btn_add = QPushButton("Add")
        btn_add.setStyleSheet("background-color: #f1c40f; font-weight: bold; padding: 5px 20px;")
        btn_add.clicked.connect(self.add_selected_layer)

        controls_layout.addWidget(self.material_dropdown)
        controls_layout.addWidget(btn_add)
        left_panel.addLayout(controls_layout)

        # -- RIGHT PANEL: COMPILER & EXECUTION --
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>PLC Recipe Log</b>"))
        
        self.log_window = QListWidget()
        right_panel.addWidget(self.log_window)

        self.btn_compile = QPushButton("1. Compile Recipe")
        self.btn_compile.clicked.connect(self.compile_recipe)

        self.btn_execute = QPushButton("2. Simulate Send to PLC")
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

    def add_selected_layer(self):
        material_name = self.material_dropdown.currentText()
        
        # Prevent adding the category separator lines
        if "---" in material_name:
            return 
            
        color = MATERIAL_CATALOG.get(material_name, "#ffffff") # Default to white if not found
        
        layer = MaterialLayer(material_name, color, self.current_drop_y)
        self.scene.addItem(layer)
        self.current_drop_y -= 35 # Stack upwards
        self.log_message(f"Added {material_name} block.")
        self.btn_execute.setEnabled(False) 

    def clear_chamber(self):
        self.scene.clear()
        self.current_drop_y = 500
        self.log_window.clear()
        self.btn_execute.setEnabled(False)

    def compile_recipe(self):
        items = self.scene.items()
        
        # Filter out text items (we only want to sort the rectangles)
        rect_items = [item for item in items if isinstance(item, MaterialLayer)]
        
        if not rect_items:
            self.log_message("Canvas is empty.")
            return

        sorted_items = sorted(rect_items, key=lambda item: item.pos().y(), reverse=True)
        self.compiled_recipe = []
        for index, item in enumerate(sorted_items):
            step_data = {"step": index + 1, "material": item.name}
            self.compiled_recipe.append(step_data)
        
        self.log_message("Compiled! Array created. Ready for execution.")
        self.btn_execute.setEnabled(True)

    def mock_execution(self):
        self.log_window.clear()
        self.log_message("--- SIMULATING PLC EXECUTION ---")
        for step in self.compiled_recipe:
            self.log_message(f"Step {step['step']}: Sending '{step['material']}' to PLC...")
        self.log_message("--- SIMULATION COMPLETE ---")

    def log_message(self, message):
        self.log_window.addItem(message)
        self.log_window.scrollToBottom()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())