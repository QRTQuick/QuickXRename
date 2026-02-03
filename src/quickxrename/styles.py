STYLE_SHEET = """
* { font-family: 'Segoe UI', 'Inter', 'SF Pro Text', sans-serif; font-size: 12pt; }
QMainWindow { background: #0f1218; }
QWidget { color: #e8ecf3; }
QGroupBox { border: 1px solid #2a3140; border-radius: 10px; margin-top: 12px; padding: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #a7b0c0; }
QLineEdit, QComboBox, QTextEdit { background: #141926; border: 1px solid #2b3446; border-radius: 8px; padding: 6px 8px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #4b7bec; }
QCheckBox { spacing: 8px; }
QPushButton { background: #1f2432; border: 1px solid #2f3a50; border-radius: 8px; padding: 8px 14px; }
QPushButton:hover { background: #283146; }
QPushButton:pressed { background: #222b3f; }
QPushButton:disabled { color: #7e8798; background: #1a1f2c; border: 1px solid #222a3a; }
QTableWidget { background: #101522; border: 1px solid #2b3446; gridline-color: #1f2533; }
QHeaderView::section { background: #161b29; color: #a7b0c0; padding: 8px; border: 1px solid #232a3a; }
QTextEdit { min-height: 120px; }
QProgressBar { background: #141926; border: 1px solid #2b3446; border-radius: 8px; text-align: center; }
QProgressBar::chunk { background-color: #4b7bec; border-radius: 8px; }
"""
