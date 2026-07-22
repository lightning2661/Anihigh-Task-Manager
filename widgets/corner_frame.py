"""Corner brackets - the little L-shaped marks anime/mecha HUDs put on
every panel (targeting reticles, cockpit readouts, that sort of thing).

Easiest way to draw these without touching every panel's own paintEvent
was to do the same trick as the sakura overlay: one transparent widget
sitting on top of the whole window, told which rects to bracket, and it
just redraws them each frame in the parent's coordinate space.
"""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget

from theme import theme

ARM = 12   # length of each bracket leg, in px


class HudCornerMarks(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._targets = []

    def watch(self, *widgets):
        """Give it the panels it should draw brackets around."""
        self._targets = [w for w in widgets if w is not None]
        self.update()

    def paintEvent(self, _):
        if not self._targets:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme["accent"]), 2)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        painter.setPen(pen)

        for widget in self._targets:
            top_left = widget.mapTo(self.parentWidget(), QPoint(0, 0))
            rect = widget.rect().translated(top_left)
            self._bracket(painter, rect.left(), rect.top(), 1, 1)
            self._bracket(painter, rect.right(), rect.top(), -1, 1)
            self._bracket(painter, rect.left(), rect.bottom(), 1, -1)
            self._bracket(painter, rect.right(), rect.bottom(), -1, -1)
        painter.end()

    @staticmethod
    def _bracket(painter, x, y, dx, dy):
        # dx/dy just flip which way the two legs point for each corner
        painter.drawLine(x, y, x + ARM * dx, y)
        painter.drawLine(x, y, x, y + ARM * dy)

    def resizeEvent(self, e):
        self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(e)
