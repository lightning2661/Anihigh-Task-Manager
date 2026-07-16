"""App entry point."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from main_window import AniHighTaskManager


def build_app_palette():
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 8, 18))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(226, 217, 243))
    palette.setColor(QPalette.ColorRole.Base, QColor(15, 12, 26))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(19, 15, 36))
    palette.setColor(QPalette.ColorRole.Text, QColor(226, 217, 243))
    palette.setColor(QPalette.ColorRole.Button, QColor(15, 12, 26))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(226, 217, 243))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(124, 58, 237))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    return palette


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(build_app_palette())

    window = AniHighTaskManager()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    