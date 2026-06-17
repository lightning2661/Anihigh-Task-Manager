import sys, os, platform
import psutil
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# theme colors - spent way too long on these lol
# violet night is the best one dont @ me
THEMES = {
    "Violet Night": {
        "bg":"#0a0812","panel":"#0f0d1a","panel2":"#161228","panel3":"#1c1735",
        "accent":"#a78bfa","accent2":"#f472b6","accent3":"#67e8f9",
        "green":"#34d399","yellow":"#fbbf24","red":"#f87171",
        "text":"#e2d9f3","muted":"#5b5280","border":"#251f40","glow":"#7c3aed",
        "alt_row":"#130f24","sakura":(240,170,210),
    },
    "Midnight Ocean": {
        "bg":"#060d18","panel":"#0a1525","panel2":"#0f1e35","panel3":"#152540",
        "accent":"#38bdf8","accent2":"#818cf8","accent3":"#34d399",
        "green":"#4ade80","yellow":"#fbbf24","red":"#fb7185",
        "text":"#e0f2fe","muted":"#4a6080","border":"#1e3a5f","glow":"#0284c7",
        "alt_row":"#0d1a2e","sakura":(150,210,255),
    },
    "Sakura Dawn": {
        "bg":"#1a0d0f","panel":"#261318","panel2":"#321a1f","panel3":"#3d2028",
        "accent":"#fb7185","accent2":"#f9a8d4","accent3":"#fda4af",
        "green":"#86efac","yellow":"#fde68a","red":"#fca5a5",
        "text":"#fce7f3","muted":"#9d6070","border":"#5c2d38","glow":"#e11d48",
        "alt_row":"#2a1419","sakura":(255,182,193),
    },
    "Forest Miko": {
        "bg":"#060f0a","panel":"#0b1a11","panel2":"#112317","panel3":"#162d1e",
        "accent":"#4ade80","accent2":"#a3e635","accent3":"#67e8f9",
        "green":"#34d399","yellow":"#fbbf24","red":"#f87171",
        "text":"#dcfce7","muted":"#3d6b4a","border":"#1a4028","glow":"#16a34a",
        "alt_row":"#0d1f13","sakura":(180,240,190),
    },
    "Light Shrine": {
        "bg":"#f5f0ff","panel":"#ffffff","panel2":"#f0ebff","panel3":"#e8e0ff",
        "accent":"#7c3aed","accent2":"#db2777","accent3":"#0891b2",
        "green":"#16a34a","yellow":"#d97706","red":"#dc2626",
        "text":"#1e1530","muted":"#8b7aaa","border":"#ddd6fe","glow":"#7c3aed",
        "alt_row":"#f8f4ff","sakura":(220,170,210),
    },
}

# global color dict, gets swapped out when user picks a new theme
C = dict(THEMES["Violet Night"])


class AniHighTaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✦ AniHigh Task Manager ✦")
        self.resize(1300, 800)
        self.setMinimumSize(960, 640)
        self.theme_name = "Violet Night"

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(12, 8, 12, 10)
        main.setSpacing(7)

        # header
        hdr = QHBoxLayout()
        title = QLabel("✦ ANIME TASK MANAGER ✦")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        theme_lbl = QLabel("Theme:")
        theme_lbl.setObjectName("clock")
        hdr.addWidget(theme_lbl)

        self.theme_cb = QComboBox()
        self.theme_cb.addItems(list(THEMES.keys()))
        self.theme_cb.setFixedWidth(140)
        self.theme_cb.currentTextChanged.connect(self._change_theme)
        hdr.addWidget(self.theme_cb)

        self.clock_lbl = QLabel()
        self.clock_lbl.setObjectName("clock")
        hdr.addWidget(self.clock_lbl)

        os_lbl = QLabel(f"  {platform.system()}  ")
        os_lbl.setObjectName("platBadge")
        hdr.addWidget(os_lbl)
        main.addLayout(hdr)

        placeholder = QLabel("more stuff coming soon...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(placeholder)

        self._apply_styles()

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _tick_clock(self):
        self.clock_lbl.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _change_theme(self, name):
        if name not in THEMES:
            return
        self.theme_name = name
        C.update(THEMES[name])
        self._apply_styles()
        self.centralWidget().update()
        for w in self.centralWidget().findChildren(QWidget):
            w.update()

    def _apply_styles(self):
        self.setStyleSheet(f"""
        * {{ font-family:'Segoe UI', sans-serif; }}
        QMainWindow, QWidget {{ background:{C['bg']}; color:{C['text']}; }}
        QLabel#title {{
            font-size:13pt; font-weight:bold;
            color:{C['accent']}; letter-spacing:3px;
        }}
        QLabel#clock {{ font-family:Consolas; font-size:9pt; color:{C['muted']}; }}
        QLabel#platBadge {{
            background:{C['panel2']}; border:1px solid {C['border']};
            border-radius:6px; padding:2px 8px;
            color:{C['accent3']}; font-size:8pt;
        }}
        QComboBox {{
            background:{C['panel2']}; border:1px solid {C['border']};
            border-radius:8px; padding:4px 9px;
            color:{C['text']}; font-size:8pt;
        }}
        QComboBox::drop-down {{ border:none; width:18px; }}
        QComboBox QAbstractItemView {{
            background:{C['panel2']}; border:1px solid {C['border']};
            color:{C['text']}; selection-background-color:{C['glow']}55;
        }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = AniHighTaskManager()
    win.show()
    sys.exit(app.exec())