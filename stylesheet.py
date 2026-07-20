"""Turns a theme dict into the QSS string that gets handed to setStyleSheet.

Kept out of main_window.py mostly because the f-string gets long and it's
annoying to scroll past when you're trying to find a click handler.

The overall look here is meant to read more like a mecha/HUD control panel
than a "glassmorphism dashboard" - panels have one corner chopped off
instead of being uniformly rounded, headers get an underline tab instead
of a soft glow, buttons are squared off. If you came here wanting to
tweak the rounding, `CUT` below controls how big the corner notch is.
"""

CUT = 14        # how big the chopped corner on panels is, in px
SNIP = 6        # smaller version for buttons/inputs


def build_stylesheet(theme):
    alt_row = theme.get("alt_row", theme["panel2"])
    accent = theme["accent"]
    border = theme["border"]
    glow = theme["glow"]

    return f"""
    * {{ font-family: 'Segoe UI', 'Yu Gothic UI', sans-serif; }}

    QMainWindow, QWidget {{ background: {theme['bg']}; color: {theme['text']}; }}

    QLabel#title {{
        font-size: 14pt;
        font-weight: 800;
        color: {accent};
        letter-spacing: 4px;
    }}
    QLabel#titleSub {{
        font-size: 7pt;
        color: {theme['muted']};
        letter-spacing: 2px;
    }}
    QLabel#clock {{ font-family: Consolas; font-size: 9pt; color: {theme['muted']}; }}

    QLabel#platBadge {{
        background: {theme['panel2']};
        border: 1px solid {accent};
        border-top-right-radius: {SNIP}px;
        border-bottom-left-radius: {SNIP}px;
        padding: 2px 10px;
        color: {theme['accent3']};
        font-size: 8pt;
        font-weight: 600;
    }}

    QLabel#sectionHdr {{
        color: {accent};
        font-size: 8pt;
        font-weight: bold;
        letter-spacing: 2px;
        border-bottom: 2px solid {accent}66;
        padding-bottom: 3px;
    }}

    /* Panels get one clipped corner instead of the same rounded-all-sides
       look every dashboard on earth uses - top-left square, bottom-right
       chopped. Cheap trick, but it reads as "console" not "web card". */
    QWidget#panel {{
        background: {theme['panel']};
        border: 1px solid {border};
        border-top-left-radius: 2px;
        border-top-right-radius: 2px;
        border-bottom-right-radius: {CUT}px;
        border-bottom-left-radius: 2px;
        border-left: 2px solid {accent}99;
    }}
    QWidget#barsPanel {{
        background: {theme['panel']};
        border: 1px solid {border};
        border-top-left-radius: 2px;
        border-top-right-radius: {SNIP + 2}px;
        border-bottom-right-radius: 2px;
        border-bottom-left-radius: 2px;
        border-left: 2px solid {accent}66;
    }}

    QTableWidget {{
        background: {theme['panel2']};
        border: 1px solid {border};
        border-radius: 2px;
        gridline-color: {border};
        alternate-background-color: {alt_row};
        selection-background-color: {glow}44;
        outline: none;
    }}
    QHeaderView::section {{
        background: {theme['panel2']};
        color: {accent};
        border: none;
        border-bottom: 2px solid {accent};
        padding: 3px 5px;
        font-size: 7pt;
        font-weight: bold;
        letter-spacing: 1px;
    }}
    QTableWidget::item {{ padding: 1px 5px; font-size: 8pt; }}
    QTableWidget::item:selected {{ color: {theme['text']}; background: {glow}55; }}

    QLineEdit, QComboBox {{
        background: {theme['panel2']};
        border: 1px solid {border};
        border-radius: {SNIP - 2}px;
        padding: 4px 9px;
        color: {theme['text']};
        font-size: 8pt;
    }}
    QLineEdit:focus {{ border: 1px solid {accent}; }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background: {theme['panel2']};
        border: 1px solid {border};
        color: {theme['text']};
        selection-background-color: {glow}55;
    }}

    QCheckBox {{ font-size: 8pt; color: {theme['accent3']}; }}
    QCheckBox::indicator {{
        width: 12px; height: 12px;
        border: 1px solid {border};
        background: {theme['panel2']};
    }}
    QCheckBox::indicator:checked {{ background: {accent}; border: 1px solid {accent}; }}

    /* Squared-off buttons with a nick out of the top-right corner rather
       than the rounded-pill thing - matches the panels above them. */
    QPushButton {{
        background: {theme['panel2']};
        border: 1px solid {border};
        border-top-right-radius: {SNIP}px;
        border-bottom-left-radius: 2px;
        border-top-left-radius: 2px;
        border-bottom-right-radius: 2px;
        padding: 4px 10px;
        color: {theme['muted']};
        font-size: 8pt;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: {glow}33;
        border: 1px solid {accent};
        color: {accent};
    }}
    QPushButton:pressed {{ background: {glow}66; }}

    QScrollBar:vertical {{ background: {theme['panel2']}; width: 6px; }}
    QScrollBar::handle:vertical {{ background: {border}; min-height: 20px; }}
    QScrollBar::handle:vertical:hover {{ background: {accent}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ height: 0; }}

    QMessageBox {{ background: {theme['panel']}; }}
    QMessageBox QLabel {{ color: {theme['text']}; }}
    QDialog {{ background: {theme['panel']}; }}

    QListWidget {{
        background: {theme['panel2']};
        border: 1px solid {border};
        alternate-background-color: {alt_row};
    }}
    QListWidget::item {{ padding: 4px 8px; font-size: 9pt; }}
    QListWidget::item:selected {{ background: {glow}55; }}
    """
