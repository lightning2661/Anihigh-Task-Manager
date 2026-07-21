"""Small metric card (icon + label + value) used for CPU/RAM/Disk/etc."""

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget

from theme import theme


class AniStatBadge(QWidget):
    def __init__(self, emoji_icon, label_text, badge_color, parent=None):
        super().__init__(parent)
        self.setFixedSize(135, 54)
        self.emojiIcon = emoji_icon
        self.badgeLabel = label_text
        self.badgeValue = "—"
        self.badgeAccentColor = QColor(badge_color)

    def updateBadgeColor(self, hex_code):
        self.badgeAccentColor = QColor(hex_code)
        self.update()

    def updateBadgeValue(self, value):
        if self.badgeValue != value:
            self.badgeValue = value
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Same clipped-corner shape as the big panels, just scaled down -
        # notch out of the top-right instead of rounding every corner.
        notch = 9
        outline = QPainterPath()
        outline.moveTo(1, 1)
        outline.lineTo(w - 1 - notch, 1)
        outline.lineTo(w - 1, 1 + notch)
        outline.lineTo(w - 1, h - 1)
        outline.lineTo(1, h - 1)
        outline.closeSubpath()

        p.setBrush(QColor(theme["panel2"]))
        p.setPen(QPen(self.badgeAccentColor.darker(220), 1))
        p.drawPath(outline)

        p.setBrush(self.badgeAccentColor)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, 0, 3, h - 1)

        p.setFont(QFont("Segoe UI Emoji", 13))
        p.setPen(self.badgeAccentColor)
        p.drawText(QRect(9, 3, 26, 26), Qt.AlignmentFlag.AlignCenter, self.emojiIcon)

        p.setFont(QFont("Segoe UI", 7))
        p.setPen(QColor(theme["muted"]))
        p.drawText(QRect(8, 32, w - 14, 18), Qt.AlignmentFlag.AlignVCenter, self.badgeLabel)

        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        p.setPen(QColor(theme["text"]))
        p.drawText(QRect(37, 3, w - 44, 26), Qt.AlignmentFlag.AlignVCenter, self.badgeValue)
        p.end()
