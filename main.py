import sys, os, platform, csv
import psutil
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

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

C = dict(THEMES["Violet Night"])


class StatsWorker(QObject):
    """runs in a background thread so the UI doesnt freeze while polling cpu/disk etc"""
    stats_ready = pyqtSignal(dict)
    procs_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        # need baseline network numbers for delta calculation
        net = psutil.net_io_counters()
        self._prev_sent = net.bytes_sent
        self._prev_recv = net.bytes_recv
        self._peak_sent = 1.0
        self._peak_recv = 1.0

        # same idea for disk io
        disk = psutil.disk_io_counters()
        self._prev_dread  = disk.read_bytes  if disk else 0
        self._prev_dwrite = disk.write_bytes if disk else 0
        self._peak_dread  = 1.0
        self._peak_dwrite = 1.0

        # first call always returns 0.0 so we throw it away
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(percpu=True, interval=None)

    @pyqtSlot()
    def poll(self):
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_percent(percpu=True, interval=None)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        net = psutil.net_io_counters()
        sent_kb = (net.bytes_sent - self._prev_sent) / 1024.0
        recv_kb = (net.bytes_recv - self._prev_recv) / 1024.0
        self._prev_sent = net.bytes_sent
        self._prev_recv = net.bytes_recv
        self._peak_sent = max(self._peak_sent, sent_kb, 1.0)
        self._peak_recv = max(self._peak_recv, recv_kb, 1.0)
        sent_pct = min(100.0, sent_kb / self._peak_sent * 100.0)
        recv_pct = min(100.0, recv_kb / self._peak_recv * 100.0)

        dsk = psutil.disk_io_counters()
        if dsk:
            dr_kb = (dsk.read_bytes  - self._prev_dread)  / 1024.0
            dw_kb = (dsk.write_bytes - self._prev_dwrite) / 1024.0
            self._prev_dread  = dsk.read_bytes
            self._prev_dwrite = dsk.write_bytes
        else:
            dr_kb = dw_kb = 0.0

        self._peak_dread  = max(self._peak_dread,  dr_kb, 1.0)
        self._peak_dwrite = max(self._peak_dwrite, dw_kb, 1.0)
        dr_pct = min(100.0, dr_kb / self._peak_dread  * 100.0)
        dw_pct = min(100.0, dw_kb / self._peak_dwrite * 100.0)

        # temp reading is super flaky on VMs/some hardware, just skip if it errors
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
                if key in temps and temps[key]:
                    cpu_temp = temps[key][0].current
                    break
        except Exception:
            pass

        battery = "N/A"
        try:
            bat = psutil.sensors_battery()
            if bat:
                plug = "⚡" if bat.power_plugged else ""
                battery = f"{bat.percent:.0f}%{plug}"
        except Exception:
            pass

        self.stats_ready.emit({
            "cpu": cpu_total, "cpu_cores": cpu_cores,
            "ram_pct": ram.percent, "ram_used_gb": ram.used / 1e9,
            "disk_pct": disk.percent,
            "sent_pct": sent_pct, "recv_pct": recv_pct,
            "sent_kb": sent_kb,   "recv_kb": recv_kb,
            "dr_pct": dr_pct, "dw_pct": dw_pct,
            "dr_kb": dr_kb,   "dw_kb": dw_kb,
            "temp": cpu_temp, "battery": battery,
            "proc_count": len(psutil.pids()),
            "uptime_s": int(datetime.now().timestamp() - psutil.boot_time()),
        })

    @pyqtSlot(str, int, bool)
    def get_procs(self, query: str, sort_idx: int, hide_sys: bool):
        procs = []

        # these are noisy kernel/OS processes that most people dont care about
        sys_names = {
            "svchost.exe", "system idle process", "system", "registry",
            "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe",
            "kthreadd", "ksoftirqd/0", "kworker/0:0"
        }

        for p in psutil.process_iter(["pid", "name", "memory_percent",
                                       "cpu_percent", "status", "create_time"]):
            try:
                info = p.info
                nm = str(info["name"]).lower()
                if hide_sys and nm in sys_names:
                    continue
                if query and query not in nm:
                    continue
                procs.append(info)
            except Exception:
                pass  # access denied on some system procs, just skip em

        sorters = [
            lambda x: x.get("memory_percent") or 0.0,
            lambda x: x.get("cpu_percent")     or 0.0,
            lambda x: (x.get("name") or "").lower(),
            lambda x: x.get("pid")             or 0,
        ]
        reverse = sort_idx in (0, 1)
        procs.sort(key=sorters[sort_idx], reverse=reverse)
        self.procs_ready.emit(procs)


class AniHighTaskManager(QMainWindow):
    _request_procs = pyqtSignal(str, int, bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("✦ AniHigh Task Manager ✦")
        self.resize(1300, 800)
        self.setMinimumSize(960, 640)
        self.theme_name = "Violet Night"
        self.last_stats = {}
        self._proc_busy = False

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(12, 8, 12, 10)
        main.setSpacing(7)

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

        self.debug_lbl = QLabel("waiting for stats...")
        self.debug_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.debug_lbl)

        self._apply_styles()
        self._start_workers()

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _start_workers(self):
        self._thread = QThread(self)
        self._worker = StatsWorker()
        self._worker.moveToThread(self._thread)

        self._worker.stats_ready.connect(self._on_stats)
        self._worker.procs_ready.connect(self._on_procs)
        self._request_procs.connect(self._worker.get_procs)
        self._thread.start()

        self._stats_timer = QTimer()
        self._stats_timer.setInterval(1500)
        self._stats_timer.timeout.connect(self._worker.poll)
        self._stats_timer.moveToThread(self._thread)
        QMetaObject.invokeMethod(self._stats_timer, "start",
                                 Qt.ConnectionType.QueuedConnection)

        self._proc_timer = QTimer(self)
        self._proc_timer.setInterval(5000)
        self._proc_timer.timeout.connect(self._refresh_procs)
        self._proc_timer.start()

        QTimer.singleShot(300, self._worker.poll)
        QTimer.singleShot(400, self._refresh_procs)

    def _refresh_procs(self):
        if self._proc_busy:
            return
        self._proc_busy = True
        self._request_procs.emit("", 0, True)

    @pyqtSlot(dict)
    def _on_stats(self, s):
        self.last_stats = s
        self.debug_lbl.setText(
            f"CPU: {s['cpu']:.1f}%  RAM: {s['ram_pct']:.1f}%  "
            f"NET tx:{s['sent_kb']:.1f}kb rx:{s['recv_kb']:.1f}kb  "
            f"DISK r:{s['dr_kb']:.1f}kb w:{s['dw_kb']:.1f}kb"
        )

    @pyqtSlot(list)
    def _on_procs(self, procs):
        self._proc_busy = False
        # procs arriving fine, will wire up table next

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

    def closeEvent(self, e):
        self._stats_timer.stop()
        self._thread.quit()
        self._thread.wait(2000)
        super().closeEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = AniHighTaskManager()
    win.show()
    sys.exit(app.exec())