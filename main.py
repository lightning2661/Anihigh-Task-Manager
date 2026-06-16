import sys
import psutil
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer

class test(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 650, 400)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["pid", "name", "mem"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        
        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)
        
        self.t = QTimer()
        self.t.timeout.connect(self.load_procs)
        self.t.start(2000) 
        
        self.load_procs()

    def load_procs(self):
        self.table.setRowCount(0)
        
        for p in psutil.process_iter():
            try:
                pid = p.pid
                name = p.name()
                mem = p.memory_percent()
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(pid)))
                self.table.setItem(row, 1, QTableWidgetItem(name))
                self.table.setItem(row, 2, QTableWidgetItem(str(round(mem, 2)) + "%"))
            except:
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = test()
    ex.show()
    sys.exit(app.exec())