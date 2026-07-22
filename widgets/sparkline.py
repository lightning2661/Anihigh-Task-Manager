"""Real-time timeline graph (CPU history, network speed, etc.)."""

from PyQt6.QtCore import Qt, QPointF, QRect
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPainterPath, QPolygonF, QLinearGradient,
)
from PyQt6.QtWidgets import QWidget

from theme import theme


class GlowSparklineWidget(QWidget):
    def __init__(self, label_text, line_color, alt_line_color=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(88)
        self.labelTitle = label_text
        self.primaryCol = QColor(line_color)
        self.altCol = QColor(alt_line_color) if alt_line_color else None

        self.historyBuffer = [0.0] * 60
        self.altHistoryBuffer = [0.0] * 60
        self._latest = 0.0
        self._latest2 = 0.0
        self.altLabelTitle = ""
        self.unitSuffix = "%"

    def setUnitSuffix(self, unit):
        self.unitSuffix = unit

    def setAltLabel(self, label):
        self.altLabelTitle = label

    def refreshChartData(self, data1, data2=None):
        self.historyBuffer = list(data1)
        self._latest = data1[-1]
        if data2 is not None:
            self.altHistoryBuffer = list(data2)
            self._latest2 = data2[-1]
        self.update()

    def draw_custom_wave(self, painter, history, color, pad_l, pad_r, pad_t, graph_h, graph_w, count, alpha=255):
        # Maps index values directly to widget client-coordinates
        def px(index): return pad_l + graph_w * index / (count - 1)
        def py(value): return pad_t + graph_h - graph_h * max(0.0, min(100.0, value)) / 100.0

        # Fill background poly with a gradient that fades at the bottom
        gradient_polygon = QPolygonF()
        gradient_polygon.append(QPointF(px(0), pad_t + graph_h))
        for idx, val in enumerate(history):
            gradient_polygon.append(QPointF(px(idx), py(val)))
        gradient_polygon.append(QPointF(px(count - 1), pad_t + graph_h))

        fill_grad = QLinearGradient(0, pad_t, 0, pad_t + graph_h)
        fill_grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), int(55 * alpha / 255)))
        fill_grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 3))

        painter.setBrush(QBrush(fill_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(gradient_polygon)

        # Plot actual line path
        line_path = QPainterPath()
        line_path.moveTo(px(0), py(history[0]))
        for idx in range(1, count):
            line_path.lineTo(px(idx), py(history[idx]))

        stroke_color = QColor(color)
        stroke_color.setAlpha(alpha)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(stroke_color, 1.5, Qt.PenStyle.SolidLine,
                             Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(line_path)

        # Live dot at last item
        endpoint_color = QColor(color)
        endpoint_color.setAlpha(alpha)
        painter.setBrush(endpoint_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(px(count - 1), py(history[-1])), 3, 3)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        widget_w, widget_h = self.width(), self.height()

        L_PAD, R_PAD, T_PAD, B_PAD = 6, 8, 16, 6
        graph_w = widget_w - L_PAD - R_PAD
        graph_h = widget_h - T_PAD - B_PAD
        history_len = len(self.historyBuffer)

        p.setBrush(QColor(theme["panel2"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, widget_w, widget_h, 8, 8)

        # Dotted lines behind the graphs (25, 50, 75 pct indicators)
        grid_pen = QPen(QColor(theme["border"]), 1, Qt.PenStyle.DotLine)
        p.setPen(grid_pen)
        for percent in (25, 50, 75):
            y_coord = T_PAD + graph_h - int(graph_h * percent / 100)
            p.drawLine(L_PAD, y_coord, widget_w - R_PAD, y_coord)

        if history_len < 2:
            p.end()
            return

        latest_value = self._latest
        current_stroke = (QColor(theme["red"]) if latest_value > 85
                           else QColor(theme["yellow"]) if latest_value > 60
                           else self.primaryCol)

        self.draw_custom_wave(p, self.historyBuffer, current_stroke, L_PAD, R_PAD, T_PAD, graph_h, graph_w, history_len)

        # Optional RX/Upload line drawing
        if self.altCol and any(val > 0 for val in self.altHistoryBuffer):
            self.draw_custom_wave(p, self.altHistoryBuffer, self.altCol, L_PAD, R_PAD, T_PAD, graph_h, graph_w, history_len, 180)

        # Labels
        p.setPen(QColor(self.primaryCol.red(), self.primaryCol.green(), self.primaryCol.blue(), 160))
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.drawText(QRect(L_PAD, 1, 80, 14), Qt.AlignmentFlag.AlignLeft, self.labelTitle)

        if self.altLabelTitle and self.altCol:
            p.setPen(QColor(self.altCol.red(), self.altCol.green(), self.altCol.blue(), 160))
            p.drawText(QRect(L_PAD + 60, 1, 80, 14), Qt.AlignmentFlag.AlignLeft, self.altLabelTitle)

        p.setPen(current_stroke)
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        text_content = f"{latest_value:.1f}{self.unitSuffix}"
        if self.altCol and any(val > 0 for val in self.altHistoryBuffer):
            text_content += f"  {self._latest2:.1f}{self.unitSuffix}"
        p.drawText(QRect(0, 1, widget_w - R_PAD, 14), Qt.AlignmentFlag.AlignRight, text_content)
        p.end()
