"""Standalone dialog windows. Just the watchlist popup for now."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
)


class PinnedProcessesDialog(QDialog):
    def __init__(self, watchlist_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pinned Processes")
        self.setMinimumSize(420, 300)

        main_layout = QVBoxLayout(self)
        hdr = QLabel("⟨ PINNED PROCESSES ⟩")
        hdr.setObjectName("sectionHdr")
        main_layout.addWidget(hdr)

        self.uiListWidget = QListWidget()
        self.uiListWidget.setAlternatingRowColors(True)
        for pid, name in watchlist_dict.items():
            item = QListWidgetItem(f"[{pid}]  {name}")
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.uiListWidget.addItem(item)
        main_layout.addWidget(self.uiListWidget)

        button_row = QHBoxLayout()
        remove_button = QPushButton("🗑  Remove Selected")
        remove_button.clicked.connect(self.deleteSelectedFromWatch)

        close_button = QPushButton("✕  Close")
        close_button.clicked.connect(self.accept)

        button_row.addWidget(remove_button)
        button_row.addWidget(close_button)
        main_layout.addLayout(button_row)

        self.watchlistDataMap = watchlist_dict

    def deleteSelectedFromWatch(self):
        for item in self.uiListWidget.selectedItems():
            pid = item.data(Qt.ItemDataRole.UserRole)
            self.watchlistDataMap.pop(pid, None)
            self.uiListWidget.takeItem(self.uiListWidget.row(item))

    def fetchUpdatedWatchlist(self):
        return self.watchlistDataMap
