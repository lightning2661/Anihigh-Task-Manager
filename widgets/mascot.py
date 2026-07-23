"""System-chan: the little animated avatar that reacts to system load."""

from PyQt6.QtCore import Qt, QPointF, QRect, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget, QMessageBox

from theme import theme


class SystemChanFaceCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(104)
        self.currentMood = "relaxed"
        self.uptimeInSeconds = 0
        self.isBlindedGlow = False
        self.eyesAreOpen = True
        self.blinkFrameCounter = 0

        animation_timer = QTimer(self)
        animation_timer.timeout.connect(self.blink_timer_tick)
        animation_timer.start(400)

    def mousePressEvent(self, event):
        # Click the avatar for a little easter egg + a reminder about the
        # "Hide OS Procs" checkbox, since people miss it.
        if event.button() == Qt.MouseButton.LeftButton:
            QMessageBox.information(
                self,
                "System-chan's Message",
                "System-chan: \"Kyaa! Please don't click my face so hard! (｡>﹏<｡)\"\n\n"
                "Tip: Checked 'Hide OS Procs' to keep table list clean of kernel threads!"
            )
        super().mousePressEvent(event)

    def change_mood_face(self, mood):
        if self.currentMood != mood:
            self.currentMood = mood
            self.update()

    def set_timer_uptime(self, uptime):
        if self.uptimeInSeconds != uptime:
            self.uptimeInSeconds = uptime
            self.update()

    def blink_timer_tick(self):
        self.isBlindedGlow = not self.isBlindedGlow
        self.blinkFrameCounter = (self.blinkFrameCounter + 1) % 8
        self.eyesAreOpen = (self.blinkFrameCounter != 7)
        if self.currentMood == "critical" or not self.eyesAreOpen:
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        mood_states = {
            "relaxed": (QColor(theme["panel"]), QColor(theme["accent"]), "relaxed"),
            "working": (QColor(theme["panel"]), QColor(theme["accent3"]), "working"),
            "critical": (QColor(theme["panel"]), QColor(theme["red"]), "critical"),
        }
        bg, eye_theme_color, state_key = mood_states[self.currentMood]
        state_messages = {
            "relaxed": "All systems nominal  🌸",
            "working": "Processing at capacity ⚡",
            "critical": "SYSTEM OVERLOAD!! 🔥",
        }

        if self.currentMood == "critical" and self.isBlindedGlow:
            p.setPen(QPen(QColor(eye_theme_color.red(), eye_theme_color.green(), eye_theme_color.blue(), 45), 6))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(0, 0, w, h, 13, 13)

        p.setBrush(bg)
        p.setPen(QPen(QColor(theme["border"]), 1))
        p.drawRoundedRect(1, 1, w - 2, h - 2, 12, 12)

        cx, cy, av_r = 46, 56, 34

        glow_alpha = 60 if self.currentMood != "critical" else (90 if self.isBlindedGlow else 30)
        for radius_offset, opacity in ((av_r + 8, 20), (av_r + 4, 40), (av_r, glow_alpha)):
            ring_color = QColor(eye_theme_color.red(), eye_theme_color.green(), eye_theme_color.blue(), opacity)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(ring_color, 1.5))
            p.drawEllipse(QPointF(cx, cy), radius_offset, radius_offset)

        face_gradient = QRadialGradient(cx - 8, cy - 8, av_r * 1.2)
        face_gradient.setColorAt(0, QColor(theme["panel3"]))
        face_gradient.setColorAt(1, QColor(theme["panel"]))
        p.setBrush(QBrush(face_gradient))
        p.setPen(QPen(eye_theme_color, 1.5))
        p.drawEllipse(QPointF(cx, cy), av_r, av_r)

        # Hair - spiky triangular chunks instead of a soft cap, plus the
        # single stray strand (ahoge) anime characters always have sticking
        # straight up. Way more "character", less "rounded blob avatar".
        hair_color = QColor(eye_theme_color.red(), eye_theme_color.green(), eye_theme_color.blue(), 150)
        p.setBrush(hair_color)
        p.setPen(Qt.PenStyle.NoPen)

        spike_tips = [
            (-av_r + 2, -av_r + 6, -av_r + 14, -av_r - 10),
            (-av_r + 16, -av_r + 2, -av_r + 22, -av_r - 16),
            (-4, -av_r + 2, 2, -av_r - 20),
            (av_r - 22, -av_r + 2, av_r - 16, -av_r - 16),
            (av_r - 14, -av_r + 6, av_r - 2, -av_r - 10),
        ]
        for base1_x, base1_y, tip_x, tip_y in spike_tips:
            spike = QPainterPath()
            spike.moveTo(cx + base1_x, cy + base1_y)
            spike.lineTo(cx + tip_x, cy + tip_y)
            spike.lineTo(cx + base1_x + 10, cy + base1_y + 2)
            spike.closeSubpath()
            p.drawPath(spike)

        # the ahoge - just one thin curved strand poking up off-center
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(hair_color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        ahoge = QPainterPath()
        ahoge.moveTo(cx - 6, cy - av_r + 6)
        ahoge.quadTo(cx - 2, cy - av_r - 18, cx + 6, cy - av_r - 26)
        p.drawPath(ahoge)

        # Face elements
        eye_y = cy - 4
        for x_offset in (-11, 11):
            target_x = cx + x_offset
            if self.eyesAreOpen:
                p.setBrush(QColor(240, 235, 255))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(target_x, eye_y), 7, 7)

                iris_grad = QRadialGradient(target_x - 1, eye_y - 1, 6)
                iris_grad.setColorAt(0, eye_theme_color.lighter(130))
                iris_grad.setColorAt(1, eye_theme_color.darker(120))
                p.setBrush(QBrush(iris_grad))
                p.drawEllipse(QPointF(target_x, eye_y), 5, 5)

                p.setBrush(QColor(10, 5, 20))
                p.drawEllipse(QPointF(target_x, eye_y), 2.5, 2.5)

                p.setBrush(QColor(255, 255, 255, 200))
                p.drawEllipse(QPointF(target_x + 2, eye_y - 2), 1.3, 1.3)
            else:
                p.setPen(QPen(eye_theme_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(int(target_x - 5), int(eye_y), int(target_x + 5), int(eye_y))

        p.setBrush(QColor(eye_theme_color.red(), eye_theme_color.green(), eye_theme_color.blue(), 100))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, eye_y + 8), 1.5, 1.5)

        smile_factors = {"relaxed": 0.4, "working": 0.15, "critical": -0.2}
        curve_depth = smile_factors[state_key]
        p.setPen(QPen(eye_theme_color.lighter(110), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        mouth_path = QPainterPath()
        mx, my = cx, eye_y + 15
        mouth_path.moveTo(mx - 8, my)
        mouth_path.cubicTo(mx - 4, my + curve_depth * 18, mx + 4, my + curve_depth * 18, mx + 8, my)
        p.drawPath(mouth_path)

        blush_color = QColor(255, 150, 160, 50) if state_key != "critical" else QColor(255, 80, 80, 60)
        p.setBrush(blush_color)
        p.setPen(Qt.PenStyle.NoPen)
        for bx in (cx - 15, cx + 10):
            p.drawEllipse(QPointF(bx + 2, eye_y + 10), 6, 4)

        for side in (-1, 1):
            ear_coord_x = cx + side * (av_r - 2)
            p.setBrush(QColor(theme["panel3"]))
            p.setPen(QPen(eye_theme_color, 1))
            p.drawEllipse(QPointF(ear_coord_x, cy - 10), 7, 10)

        tx = cx + av_r + 14
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.setPen(QColor(theme["text"]))
        p.drawText(QRect(tx, 6, w - tx - 6, 22), Qt.AlignmentFlag.AlignVCenter, "System-chan")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(eye_theme_color)
        p.drawText(QRect(tx, 28, w - tx - 6, 20), Qt.AlignmentFlag.AlignVCenter, state_messages[state_key])

        hours, remainder = divmod(self.uptimeInSeconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        p.setFont(QFont("Consolas", 7))
        p.setPen(QColor(theme["muted"]))
        p.drawText(QRect(tx, 50, w - tx - 6, 18), Qt.AlignmentFlag.AlignVCenter, f"uptime  {hours:02d}:{minutes:02d}:{seconds:02d}")
        p.end()
