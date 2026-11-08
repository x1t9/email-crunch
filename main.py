"""
Email Crunch v0.1-alpha
Cross-platform bulk document email extractor.
"""

import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    # High-DPI support (cross-platform)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Email Crunch")
    app.setOrganizationName("EmailCrunch")
    app.setApplicationVersion("0.1-alpha")

    # macOS: use native menu bar
    if sys.platform == "darwin":
        app.setAttribute(Qt.AA_DontShowIconsInMenus, False)

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
