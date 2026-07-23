"""Sakura petals drifting down over the window. Purely cosmetic - a
transparent widget stacked on top of everything else."""

import random

from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtWidgets import QWidget

from theme import theme


class PetalFallingOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        parent_w = parent.width() or 1280
        parent_h = parent.height() or 780
        self.fallingPetals = [self.makeNewPetal(random.randint(0, parent_w), random.randint(0, parent_h))
                               for _ in range(14)]

        physics_timer = QTimer(self)
        physics_timer.timeout.connect(self.petalPhysicsLoop)
        physics_timer.start(45)

    def makeNewPetal(self, x=None, y=None):
        parent_w = self.parent().width() or 1280
        sakura_color = theme["sakura"]
        return {
            "x": x if x is not None else random.randint(0, parent_w),
            "y": y if y is not None else -20,
            "s": random.uniform(5, 10),
            "sp": random.uniform(0.5, 1.4),
            "dr": random.uniform(-0.3, 0.3),
            "a": random.uniform(0, 360),
            "spin": random.uniform(-1.1, 1.1),
            "al": random.randint(40, 100),
            "r": sakura_color[0],
            "g": sakura_color[1],
            "b": sakura_color[2]
        }

    def syncPetalTheme(self):
        sakura_color = theme["sakura"]
        for petal in self.fallingPetals:
            petal["r"] = sakura_color[0]
            petal["g"] = sakura_color[1]
            petal["b"] = sakura_color[2]

    def petalPhysicsLoop(self):
        parent_h = self.parent().height() or 780
        parent_w = self.parent().width() or 1280
        for petal in self.fallingPetals:
            petal["y"] += petal["sp"]
            petal["x"] += petal["dr"]
            petal["a"] += petal["spin"]
            if petal["y"] > parent_h + 20:
                new_petal = self.makeNewPetal()
                petal.update(new_petal)
                petal["y"] = -20
                petal["x"] = random.randint(0, parent_w)
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for petal in self.fallingPetals:
            painter.save()
            painter.translate(petal["x"], petal["y"])
            painter.rotate(petal["a"])
            painter.setBrush(QBrush(QColor(petal["r"], petal["g"], petal["b"], petal["al"])))
            painter.setPen(Qt.PenStyle.NoPen)
            size = petal["s"]
            for idx in range(4):
                painter.save()
                painter.rotate(idx * 90)
                painter.drawEllipse(QRectF(0, -size * .18, size * .5, size * .4))
                painter.restore()
            painter.restore()
        painter.end()

    def resizeEvent(self, e):
        self.setGeometry(self.parent().rect())
        super().resizeEvent(e)
