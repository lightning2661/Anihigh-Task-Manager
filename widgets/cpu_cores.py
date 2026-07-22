"""Per-core load bars shown at the top of the dashboard."""

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import QWidget

from theme import theme


class CpuCoreLoadVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.corePercentages = []
        self.setMinimumHeight(60)

    def drawCoreLoads(self, cores):
        if cores != self.corePercentages:
            self.corePercentages = list(cores)
            self.update()

    def paintEvent(self, _):
        if not self.corePercentages:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        core_count = len(self.corePercentages)
        if core_count == 0:
            p.end()
            return

        bar_w = max(8, (w - (core_count - 1) * 3) // core_count)
        total_w = core_count * bar_w + (core_count - 1) * 3
        starting_x = (w - total_w) // 2

        acc = QColor(theme["accent"])
        acc2 = QColor(theme["accent2"])
        yel = QColor(theme["yellow"])
        red = QColor(theme["red"])

        for idx, percent in enumerate(self.corePercentages):
            x_coord = starting_x + idx * (bar_w + 3)
            p.setBrush(QColor(theme["panel2"]))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x_coord, 4, bar_w, h - 20, 3, 3)

            bar_height = max(2, int((h - 20) * percent / 100))
            if percent > 85:
                fill_color = red
            elif percent > 60:
                fill_color = yel
            else:
                ratio = idx / max(core_count - 1, 1)
                r = int(acc.red() * (1 - ratio) + acc2.red() * ratio)
                g = int(acc.green() * (1 - ratio) + acc2.green() * ratio)
                b = int(acc.blue() * (1 - ratio) + acc2.blue() * ratio)
                fill_color = QColor(r, g, b)

            p.setBrush(fill_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x_coord, 4 + ((h - 20) - bar_height), bar_w, bar_height, 3, 3)

            p.setPen(QColor(theme["muted"]))
            p.setFont(QFont("Consolas", 6))
            p.drawText(QRect(x_coord, h - 14, bar_w, 12), Qt.AlignmentFlag.AlignCenter, f"{int(percent)}")
        p.end()
