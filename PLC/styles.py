# styles.py

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