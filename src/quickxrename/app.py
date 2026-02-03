import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QSplashScreen

from .styles import STYLE_SHEET
from .ui import MainWindow


def _build_splash_pixmap() -> QPixmap:
    """
    Create a simple, clean placeholder logo for the splash screen.
    This avoids external assets and keeps it cross-platform.
    """
    width, height = 520, 280
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#0f1218"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Logo placeholder (rounded rectangle)
    painter.setBrush(QColor("#1f2432"))
    painter.setPen(QColor("#2b3446"))
    painter.drawRoundedRect(30, 30, 120, 120, 18, 18)

    # "QX" letters
    painter.setPen(QColor("#4b7bec"))
    font = QFont("Segoe UI", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(30, 30, 120, 120, Qt.AlignCenter, "QX")

    # App name
    painter.setPen(QColor("#e8ecf3"))
    font = QFont("Segoe UI", 20, QFont.Bold)
    painter.setFont(font)
    painter.drawText(170, 60, 320, 40, Qt.AlignLeft | Qt.AlignVCenter, "QuickXRename")

    # Subtitle
    painter.setPen(QColor("#a7b0c0"))
    font = QFont("Segoe UI", 11)
    painter.setFont(font)
    painter.drawText(170, 100, 320, 30, Qt.AlignLeft | Qt.AlignVCenter, "Developer-friendly batch renamer")

    painter.end()
    return pixmap


def run() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)

    # Create and show splash screen
    splash = QSplashScreen(_build_splash_pixmap())
    splash.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    splash.showMessage(
        "Loading QuickXRename...",
        Qt.AlignBottom | Qt.AlignHCenter,
        QColor("#a7b0c0"),
    )
    splash.show()
    app.processEvents()

    # Initialize main window (heavy work goes here if needed)
    window = MainWindow()

    # Close splash AFTER main window is ready to show
    def show_main():
        window.show()
        splash.finish(window)

    # Use a short timer to ensure UI is responsive
    QTimer.singleShot(200, show_main)

    sys.exit(app.exec())
