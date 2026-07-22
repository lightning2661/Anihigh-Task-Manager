"""Gradient-filled progress bar used for the CPU/RAM/DISK summary row."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QFont
from PyQt6.QtWidgets import QWidget

from theme import theme


class NeonProgressBar(QWidget):
    def __init__(self, color1, color2, label_text="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.currentPercent = 0.0
        self.gradientColorStart = QColor(color1)
        self.gradientColorEnd = QColor(color2)
        self.barLabel = label_text

    def updateProgressValue(self, val):
        constrained_val = max(0.0, min(100.0, val))
        if abs(constrained_val - self.currentPercent) > 0.05:
            self.currentPercent = constrained_val
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        radius = 4

        p.setBrush(QColor(theme["panel2"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 2, w, h - 4, radius, radius)

        fill_width = max(0, int((w - 4) * self.currentPercent / 100))
        if fill_width > 0:
            gradient = QLinearGradient(0, 0, fill_width, 0)
            gradient.setColorAt(0, self.gradientColorStart)
            gradient.setColorAt(1, self.gradientColorEnd)
            p.setBrush(QBrush(gradient))
            p.drawRoundedRect(2, 4, fill_width, h - 8, radius - 1, radius - 1)

        p.setPen(QColor(theme["text"]))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.drawText(10, 0, 60, h, Qt.AlignmentFlag.AlignVCenter, self.barLabel)

        p.setPen(self.gradientColorEnd)
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        p.drawText(0, 0, w - 8, h, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, f"{self.currentPercent:.1f}%")
        p.end()
