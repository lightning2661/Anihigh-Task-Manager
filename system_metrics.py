"""Polls psutil for CPU/RAM/disk/network stuff and the process list.

Runs on its own QThread (see kickstart_threads in main_window.py) because
process_iter() can stall for a bit on a machine with a ton of processes,
and we don't want that freezing the window's animations while it waits.
"""

from datetime import datetime

import psutil
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class SysMetricsCollector(QObject):
    metricsDumped = pyqtSignal(dict)
    procListDumped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        # Calculate network through delta bytes
        net_counters = psutil.net_io_counters()
        self._last_sent = net_counters.bytes_sent
        self._last_recv = net_counters.bytes_recv
        self._sent_peak = 1.0
        self._recv_peak = 1.0

        # Disk activity delta setup
        disk_counters = psutil.disk_io_counters()
        self._last_dr = disk_counters.read_bytes if disk_counters else 0
        self._last_dw = disk_counters.write_bytes if disk_counters else 0
        self._dr_peak = 1.0
        self._dw_peak = 1.0

        # Avoid first-call returning zero
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(percpu=True, interval=None)

    @pyqtSlot()
    def grab_metrics_data(self):
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_percent(percpu=True, interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        net_counters = psutil.net_io_counters()
        sent_kb = (net_counters.bytes_sent - self._last_sent) / 1024.0
        recv_kb = (net_counters.bytes_recv - self._last_recv) / 1024.0

        self._last_sent = net_counters.bytes_sent
        self._last_recv = net_counters.bytes_recv
        self._sent_peak = max(self._sent_peak, sent_kb, 1.0)
        self._recv_peak = max(self._recv_peak, recv_kb, 1.0)
        sent_pct = min(100.0, sent_kb / self._sent_peak * 100.0)
        recv_pct = min(100.0, recv_kb / self._recv_peak * 100.0)

        disk_counters = psutil.disk_io_counters()
        if disk_counters:
            dr_kb = (disk_counters.read_bytes - self._last_dr) / 1024.0
            dw_kb = (disk_counters.write_bytes - self._last_dw) / 1024.0
            self._last_dr = disk_counters.read_bytes
            self._last_dw = disk_counters.write_bytes
        else:
            dr_kb = dw_kb = 0.0

        self._dr_peak = max(self._dr_peak, dr_kb, 1.0)
        self._dw_peak = max(self._dw_peak, dw_kb, 1.0)
        dr_pct = min(100.0, dr_kb / self._dr_peak * 100.0)
        dw_pct = min(100.0, dw_kb / self._dw_peak * 100.0)

        # Temp checks - sensor reads are highly platform-dependent
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
                if key in temps and temps[key]:
                    cpu_temp = temps[key][0].current
                    break
        except Exception:
            pass  # VMs or systems lacking sensors fall back silently

        # Battery query
        battery_status = "N/A"
        try:
            bat = psutil.sensors_battery()
            if bat:
                plug_icon = "⚡" if bat.power_plugged else ""
                battery_status = f"{bat.percent:.0f}%{plug_icon}"
        except Exception:
            pass

        self.metricsDumped.emit({
            "cpu": cpu_total, "cpu_cores": cpu_cores,
            "ram_pct": ram.percent, "ram_used_gb": ram.used / 1e9,
            "disk_pct": disk.percent,
            "sent_pct": sent_pct, "recv_pct": recv_pct,
            "sent_kb": sent_kb, "recv_kb": recv_kb,
            "dr_pct": dr_pct, "dw_pct": dw_pct,
            "dr_kb": dr_kb, "dw_kb": dw_kb,
            "temp": cpu_temp, "battery": battery_status,
            "proc_count": len(psutil.pids()),
            "uptime_s": int(datetime.now().timestamp() - psutil.boot_time()),
        })

    @pyqtSlot(str, int, bool)
    def dump_active_processes(self, query: str, sorting_index: int, hide_system_procs: bool):
        active_proc_list = []
        # Filter set of common Windows/Linux kernel OS threads
        system_exe_names = {
            "svchost.exe", "system idle process", "system", "registry",
            "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe",
            "kthreadd", "ksoftirqd/0", "kworker/0:0"
        }

        for proc in psutil.process_iter(["pid", "name", "memory_percent",
                                          "cpu_percent", "status", "create_time"]):
            try:
                info = proc.info
                name_lower = str(info["name"]).lower()

                # Checkbox check to hide system junk
                if hide_system_procs and name_lower in system_exe_names:
                    continue
                if query and query not in name_lower:
                    continue
                active_proc_list.append(info)
            except Exception:
                pass  # Ignore processes raising AccessDenied (e.g. system services)

        # Lambda sorters mapping UI dropdown indexes
        sort_lambdas = [
            lambda x: x.get("memory_percent") or 0.0,
            lambda x: x.get("cpu_percent") or 0.0,
            lambda x: (x.get("name") or "").lower(),
            lambda x: x.get("pid") or 0,
        ]

        reverse_flag = sorting_index in (0, 1)
        active_proc_list.sort(key=sort_lambdas[sorting_index], reverse=reverse_flag)
        self.procListDumped.emit(active_proc_list)
