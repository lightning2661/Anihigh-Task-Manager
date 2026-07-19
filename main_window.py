"""Main window - builds the layout and hooks up every button/handler.

Fair warning, make_ui_elements() is a wall of layout code. Splitting it
into smaller methods kept breaking the spacing/margins in weird ways, so
it just stayed as one long function.
"""

import csv
import os
import platform
from datetime import datetime

import psutil
from PyQt6.QtCore import Qt, QThread, QTimer, QMetaObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QCheckBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QFileDialog,
)

from theme import THEMES, theme
from stylesheet import build_stylesheet
from system_metrics import SysMetricsCollector
from widgets import (
    GlowSparklineWidget, CpuCoreLoadVisualizer, NeonProgressBar,
    AniStatBadge, SystemChanFaceCard, PetalFallingOverlay, HudCornerMarks,
)
from dialogs import PinnedProcessesDialog


class AniHighTaskManager(QMainWindow):
    signalRequestProcUpdate = pyqtSignal(str, int, bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("✦ AniHigh Task Manager ✦")
        self.resize(1300, 800)
        self.setMinimumSize(960, 640)

        # Performance histories array cache
        self.cpuHistory = [0.0] * 60
        self.ramHistory = [0.0] * 60
        self.diskHistory = [0.0] * 60
        self.sentHistory = [0.0] * 60
        self.recvHistory = [0.0] * 60
        self.diskReadHistory = [0.0] * 60
        self.diskWriteHistory = [0.0] * 60

        self.isProcUpdatePending = False
        self.pinnedWatchlist = {}
        self.lastFetchedMetrics = {}
        self.activeThemeName = "Violet Night"

        # log array tracing terminated pinned processes
        self.dead_pins_log = []

        self.make_ui_elements()
        self.load_stylesheet_configs()
        self.kickstart_threads()

    def kickstart_threads(self):
        self.workerThread = QThread(self)
        self.statsCollector = SysMetricsCollector()
        self.statsCollector.moveToThread(self.workerThread)

        self.statsCollector.metricsDumped.connect(self.handleIncomingMetrics)
        self.statsCollector.procListDumped.connect(self.populateProcessData)
        self.signalRequestProcUpdate.connect(self.statsCollector.dump_active_processes)
        self.workerThread.start()

        self.metricsPollTimer = QTimer()
        self.metricsPollTimer.setInterval(1500)
        self.metricsPollTimer.timeout.connect(self.statsCollector.grab_metrics_data)
        self.metricsPollTimer.moveToThread(self.workerThread)
        QMetaObject.invokeMethod(self.metricsPollTimer, "start",
                                  Qt.ConnectionType.QueuedConnection)

        self.procListUpdateTimer = QTimer(self)
        self.procListUpdateTimer.setInterval(5000)
        self.procListUpdateTimer.timeout.connect(self.triggerProcDataRefresh)
        self.procListUpdateTimer.start()

        self.clockUpdateTimer = QTimer(self)
        self.clockUpdateTimer.timeout.connect(self.refreshClockDisplay)
        self.clockUpdateTimer.start(1000)

        QTimer.singleShot(300, self.statsCollector.grab_metrics_data)
        QTimer.singleShot(400, self.triggerProcDataRefresh)
        self.refreshClockDisplay()

    def triggerProcDataRefresh(self):
        if self.isProcUpdatePending:
            return
        self.isProcUpdatePending = True
        self.signalRequestProcUpdate.emit(
            self.searchField.text().lower(),
            self.sortDropdown.currentIndex(),
            self.hideSysCheckbox.isChecked()
        )

    @pyqtSlot(dict)
    def handleIncomingMetrics(self, metrics_dict):
        self.lastFetchedMetrics = metrics_dict

        for timeline, val in [
            (self.cpuHistory, metrics_dict["cpu"]),
            (self.ramHistory, metrics_dict["ram_pct"]),
            (self.diskHistory, metrics_dict["disk_pct"]),
            (self.sentHistory, metrics_dict["sent_pct"]),
            (self.recvHistory, metrics_dict["recv_pct"]),
            (self.diskReadHistory, metrics_dict["dr_pct"]),
            (self.diskWriteHistory, metrics_dict["dw_pct"]),
        ]:
            timeline.pop(0)
            timeline.append(val)

        # Plot lists on timeline graph canvas
        self.cpuGraph.refreshChartData(self.cpuHistory)
        self.ramGraph.refreshChartData(self.ramHistory)
        self.networkGraph.refreshChartData(self.sentHistory, self.recvHistory)
        self.diskIoGraph.refreshChartData(self.diskReadHistory, self.diskWriteHistory)

        self.cpuProgressBar.updateProgressValue(metrics_dict["cpu"])
        self.ramProgressBar.updateProgressValue(metrics_dict["ram_pct"])
        self.diskProgressBar.updateProgressValue(metrics_dict["disk_pct"])

        self.cpuBadge.updateBadgeValue(f"{metrics_dict['cpu']:.1f}%")
        self.ramBadge.updateBadgeValue(f"{metrics_dict['ram_used_gb']:.1f} GB")
        self.diskBadge.updateBadgeValue(f"{metrics_dict['disk_pct']:.1f}%")
        self.procBadge.updateBadgeValue(str(metrics_dict["proc_count"]))

        temp_val = f"{metrics_dict['temp']:.0f}°C" if metrics_dict["temp"] else "N/A"
        self.tempBadge.updateBadgeValue(temp_val)
        self.batBadge.updateBadgeValue(metrics_dict["battery"])

        # Drop a line in Downloads when CPU spikes, so there's a trail to
        # check after the fact instead of just a missed warning popup.
        if metrics_dict["cpu"] > 90.0:
            try:
                log_path = os.path.join(os.path.expanduser("~"), "Downloads", "high_cpu_warnings.log")
                with open(log_path, "a", encoding="utf-8") as lf:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    lf.write(f"[{timestamp}] WARNING: CPU load exceeded 90% (Current: {metrics_dict['cpu']:.1f}%)\n")
            except Exception:
                pass

        self.statusCard.set_timer_uptime(metrics_dict["uptime_s"])
        if metrics_dict["cpu"] > 90:
            avatar_mood = "critical"
        elif metrics_dict["cpu"] > 60:
            avatar_mood = "working"
        else:
            avatar_mood = "relaxed"
        self.statusCard.change_mood_face(avatar_mood)

        if "cpu_cores" in metrics_dict:
            self.cpuCoreVisualizer.drawCoreLoads(metrics_dict["cpu_cores"])

        self.verifyPinnedProcessesAlive()

    @pyqtSlot(list)
    def populateProcessData(self, active_proc_list):
        self.isProcUpdatePending = False
        self.renderProcessTable(active_proc_list)

    def renderProcessTable(self, active_proc_list):
        table = self.processTable
        table.setUpdatesEnabled(False)
        if table.rowCount() != len(active_proc_list):
            table.setRowCount(len(active_proc_list))

        status_emoji_map = {
            "running": "🟢", "sleeping": "🔵", "stopped": "🟡",
            "zombie": "💀", "disk-sleep": "💤"
        }
        align_center = Qt.AlignmentFlag.AlignCenter

        for row_idx, proc in enumerate(active_proc_list):
            pid = proc.get("pid", 0)
            name = str(proc.get("name") or "")
            cpu = proc.get("cpu_percent", 0)
            mem = proc.get("memory_percent", 0)
            status_text = str(proc.get("status", ""))

            start_time = proc.get("create_time", 0)
            if start_time:
                age_seconds = int(datetime.now().timestamp() - start_time)
                h, rem = divmod(age_seconds, 3600)
                m, _ = divmod(rem, 60)
                runtime_string = f"{h:02d}:{m:02d}"
            else:
                runtime_string = "—"

            pinned_tag = "📌" if pid in self.pinnedWatchlist else ""
            name_text = f"{pinned_tag}{name}"

            cpu_brush = QColor(theme["red"]) if cpu > 40 else (QColor(theme["yellow"]) if cpu > 15 else None)
            mem_brush = QColor(theme["accent2"]) if mem > 5 else None

            row_items = [
                (str(pid), align_center, None),
                (name_text, None, QColor(theme["accent"]) if pid in self.pinnedWatchlist else None),
                (f"{cpu:.1f}", align_center, cpu_brush),
                (f"{mem:.2f}", align_center, mem_brush),
                (f"{status_emoji_map.get(status_text, '⚪')} {status_text}", None, None),
                (runtime_string, align_center, None),
            ]

            for col_idx, (text, alignment, text_fg_color) in enumerate(row_items):
                item = table.item(row_idx, col_idx)
                if item is None:
                    item = QTableWidgetItem()
                    table.setItem(row_idx, col_idx, item)

                if item.text() != text:
                    item.setText(text)
                if alignment is not None:
                    item.setTextAlignment(alignment)
                if text_fg_color is not None:
                    item.setForeground(text_fg_color)
                elif col_idx in (2, 3):
                    item.setForeground(QColor(theme["text"]))

        table.setUpdatesEnabled(True)

    def verifyPinnedProcessesAlive(self):
        if not self.pinnedWatchlist:
            return

        current_running_pids = set(psutil.pids())
        terminated_watched_pids = [pid for pid in self.pinnedWatchlist if pid not in current_running_pids]

        for pid in terminated_watched_pids:
            process_name = self.pinnedWatchlist.pop(pid)
            self.dead_pins_log.append({
                "pid": pid, "name": process_name, "time": datetime.now().strftime("%H:%M:%S")
            })
            QMessageBox.warning(self, "⚠ Watchlist Alert",
                                 f"Watched process ended:\n『{process_name}』 (PID {pid})")

    def make_ui_elements(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        main_layout = QVBoxLayout(root_widget)
        main_layout.setContentsMargins(12, 8, 12, 10)
        main_layout.setSpacing(7)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        app_title = QLabel("『 ANIHIGH 』TASK MANAGER")
        app_title.setObjectName("title")
        title_sub = QLabel("SYSTEM MONITOR // ONLINE")
        title_sub.setObjectName("titleSub")
        title_block.addWidget(app_title)
        title_block.addWidget(title_sub)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        theme_label = QLabel("Theme:")
        theme_label.setObjectName("clock")
        header_layout.addWidget(theme_label)

        self.themeDropdown = QComboBox()
        self.themeDropdown.addItems(list(THEMES.keys()))
        self.themeDropdown.setFixedWidth(140)
        self.themeDropdown.currentTextChanged.connect(self.onThemeChanged)
        header_layout.addWidget(self.themeDropdown)

        self.clockLabel = QLabel()
        self.clockLabel.setObjectName("clock")
        header_layout.addWidget(self.clockLabel)

        os_badge = QLabel(f"  {platform.system()}  ")
        os_badge.setObjectName("platBadge")
        header_layout.addWidget(os_badge)

        main_layout.addLayout(header_layout)

        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(10)

        self.statusCard = SystemChanFaceCard()
        mid_layout.addWidget(self.statusCard, 1)

        badges_container = QWidget()
        badges_grid = QGridLayout(badges_container)
        badges_grid.setSpacing(5)
        badges_grid.setContentsMargins(0, 0, 0, 0)

        self.cpuBadge = AniStatBadge("🖥", "CPU Usage", theme["accent"])
        self.ramBadge = AniStatBadge("🧠", "RAM Used", theme["accent2"])
        self.diskBadge = AniStatBadge("💾", "Disk", theme["accent3"])
        self.procBadge = AniStatBadge("⚙", "Processes", theme["green"])
        self.tempBadge = AniStatBadge("🌡", "CPU Temp", theme["yellow"])
        self.batBadge = AniStatBadge("🔋", "Battery", theme["accent"])

        self.badgesList = [self.cpuBadge, self.ramBadge, self.diskBadge,
                            self.procBadge, self.tempBadge, self.batBadge]
        for idx, badge in enumerate(self.badgesList):
            badges_grid.addWidget(badge, idx // 3, idx % 3)

        mid_layout.addWidget(badges_container, 2)
        main_layout.addLayout(mid_layout)

        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)

        progress_container = QWidget()
        progress_container.setObjectName("barsPanel")
        v_prog_layout = QVBoxLayout(progress_container)
        v_prog_layout.setContentsMargins(12, 6, 12, 6)
        v_prog_layout.setSpacing(3)

        self.cpuProgressBar = NeonProgressBar(theme["accent"], theme["accent2"], "CPU")
        self.ramProgressBar = NeonProgressBar(theme["accent2"], theme["accent3"], "RAM")
        self.diskProgressBar = NeonProgressBar(theme["accent3"], theme["green"], "DISK")

        for bar in [self.cpuProgressBar, self.ramProgressBar, self.diskProgressBar]:
            v_prog_layout.addWidget(bar)
        progress_layout.addWidget(progress_container, 3)

        cores_container = QWidget()
        cores_container.setObjectName("barsPanel")
        v_cores_layout = QVBoxLayout(cores_container)
        v_cores_layout.setContentsMargins(10, 4, 10, 4)
        v_cores_layout.setSpacing(2)

        core_label = QLabel("⟨ CPU CORES ⟩")
        core_label.setObjectName("sectionHdr")
        v_cores_layout.addWidget(core_label)

        self.cpuCoreVisualizer = CpuCoreLoadVisualizer()
        v_cores_layout.addWidget(self.cpuCoreVisualizer)
        progress_layout.addWidget(cores_container, 2)
        main_layout.addLayout(progress_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        process_panel = QWidget()
        process_panel.setObjectName("panel")
        v_proc_panel_layout = QVBoxLayout(process_panel)
        v_proc_panel_layout.setContentsMargins(10, 10, 10, 10)
        v_proc_panel_layout.setSpacing(6)

        proc_title = QLabel("⟨ PROCESSES ⟩")
        proc_title.setObjectName("sectionHdr")
        v_proc_panel_layout.addWidget(proc_title)

        # Search row including Hide system processes checkbox
        search_row = QHBoxLayout()
        self.searchField = QLineEdit()
        self.searchField.setPlaceholderText("🔍  search process…")
        self.searchField.textChanged.connect(self.triggerProcDataRefresh)

        self.hideSysCheckbox = QCheckBox("Hide OS Procs")
        self.hideSysCheckbox.setToolTip("Ignore kernel OS background threads (e.g. svchost, system idle)")
        self.hideSysCheckbox.setChecked(True)
        self.hideSysCheckbox.stateChanged.connect(self.triggerProcDataRefresh)

        self.sortDropdown = QComboBox()
        self.sortDropdown.addItems(["Sort: Memory", "Sort: CPU", "Sort: Name", "Sort: PID"])
        self.sortDropdown.currentIndexChanged.connect(self.triggerProcDataRefresh)

        search_row.addWidget(self.searchField, 3)
        search_row.addWidget(self.hideSysCheckbox, 1)
        search_row.addWidget(self.sortDropdown, 1)
        v_proc_panel_layout.addLayout(search_row)

        self.processTable = QTableWidget()
        self.processTable.setColumnCount(6)
        self.processTable.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "MEM %", "Status", "Runtime"])
        self.processTable.horizontalHeader().setStretchLastSection(False)
        self.processTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.processTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.processTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.processTable.verticalHeader().hide()
        self.processTable.setAlternatingRowColors(True)
        # Sorting stays off - QTableWidget's built-in sort fights with our
        # own in-place row updates and scrambles things mid-refresh.
        self.processTable.setSortingEnabled(False)

        self.processTable.setColumnWidth(0, 55)
        self.processTable.setColumnWidth(2, 52)
        self.processTable.setColumnWidth(3, 52)
        self.processTable.setColumnWidth(4, 90)
        self.processTable.setColumnWidth(5, 58)
        v_proc_panel_layout.addWidget(self.processTable)

        button_row = QHBoxLayout()
        self.endTaskButton = QPushButton("🗡  End Task")
        self.pauseButton = QPushButton("⏸  Suspend")
        self.resumeButton = QPushButton("▶  Resume")
        self.pinButton = QPushButton("📌  Pin")
        self.exportButton = QPushButton("📄  Export CSV")
        self.watchlistButton = QPushButton("👁  Watchlist")
        self.refreshButton = QPushButton("🔄  Refresh")

        self.endTaskButton.clicked.connect(self.murder_process)
        self.pauseButton.clicked.connect(self.suspend_it)
        self.resumeButton.clicked.connect(self.resume_it)
        self.pinButton.clicked.connect(self.pin_unpin_app)
        self.exportButton.clicked.connect(self.spit_csv_file)
        self.watchlistButton.clicked.connect(self.show_pinneds)
        self.refreshButton.clicked.connect(self.triggerProcDataRefresh)

        for button in [self.endTaskButton, self.pauseButton, self.resumeButton,
                        self.pinButton, self.exportButton, self.watchlistButton, self.refreshButton]:
            button_row.addWidget(button)
        v_proc_panel_layout.addLayout(button_row)
        content_layout.addWidget(process_panel, 3)

        graph_panel = QWidget()
        graph_panel.setObjectName("panel")
        v_graph_panel_layout = QVBoxLayout(graph_panel)
        v_graph_panel_layout.setContentsMargins(10, 10, 10, 10)
        v_graph_panel_layout.setSpacing(5)

        graph_title = QLabel("⟨ PERFORMANCE ⟩")
        graph_title.setObjectName("sectionHdr")
        v_graph_panel_layout.addWidget(graph_title)

        self.cpuGraph = GlowSparklineWidget("CPU", theme["accent"])
        self.ramGraph = GlowSparklineWidget("RAM", theme["accent2"])
        self.networkGraph = GlowSparklineWidget("TX", theme["accent3"], theme["green"])
        self.networkGraph.setAltLabel("RX")
        self.diskIoGraph = GlowSparklineWidget("READ", theme["yellow"], theme["accent2"])
        self.diskIoGraph.setAltLabel("WRITE")

        for graph in [self.cpuGraph, self.ramGraph, self.networkGraph, self.diskIoGraph]:
            v_graph_panel_layout.addWidget(graph)

        content_layout.addWidget(graph_panel, 2)
        main_layout.addLayout(content_layout, 1)

        self.petalOverlay = PetalFallingOverlay(root_widget)
        self.petalOverlay.setGeometry(root_widget.rect())
        self.petalOverlay.raise_()

        # Bracket marks go over the petals - they're UI chrome, not
        # atmosphere, so they should sit above the falling petals.
        self.hudMarks = HudCornerMarks(root_widget)
        self.hudMarks.setGeometry(root_widget.rect())
        self.hudMarks.watch(process_panel, graph_panel, progress_container, cores_container)
        self.hudMarks.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "petalOverlay"):
            self.petalOverlay.setGeometry(self.centralWidget().rect())
        if hasattr(self, "hudMarks"):
            self.hudMarks.setGeometry(self.centralWidget().rect())
            self.hudMarks.update()

    def onThemeChanged(self, theme_name):
        if theme_name not in THEMES:
            return
        self.activeThemeName = theme_name
        theme.update(THEMES[theme_name])
        self.load_stylesheet_configs()

        if hasattr(self, "petalOverlay"):
            self.petalOverlay.syncPetalTheme()

        badge_palette = [theme["accent"], theme["accent2"], theme["accent3"], theme["green"], theme["yellow"], theme["accent"]]
        for badge, hex_color in zip(self.badgesList, badge_palette):
            badge.updateBadgeColor(hex_color)

        self.centralWidget().update()
        for child_widget in self.centralWidget().findChildren(QWidget):
            child_widget.update()

    def load_stylesheet_configs(self):
        self.setStyleSheet(build_stylesheet(theme))

    def refreshClockDisplay(self):
        self.clockLabel.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def get_selected_row_pid(self):
        selected_row = self.processTable.currentRow()
        if selected_row < 0:
            return None, None
        pid_item = self.processTable.item(selected_row, 0)
        name_item = self.processTable.item(selected_row, 1)
        pid = int(pid_item.text()) if pid_item else None
        name = name_item.text().lstrip("📌") if name_item else str(pid)
        return pid, name

    def murder_process(self):
        pid, name = self.get_selected_row_pid()
        if pid is None:
            return

        confirmation_msg = f"Terminate 『{name}』(PID {pid})?"
        user_choice = QMessageBox.question(
            self, "Confirm", confirmation_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if user_choice == QMessageBox.StandardButton.Yes:
            try:
                psutil.Process(pid).terminate()
                self.pinnedWatchlist.pop(pid, None)
                self.triggerProcDataRefresh()
            except Exception as err:
                QMessageBox.warning(self, "Error", str(err))

    def suspend_it(self):
        pid, _ = self.get_selected_row_pid()
        if pid is None:
            return
        try:
            psutil.Process(pid).suspend()
            self.triggerProcDataRefresh()
        except Exception as err:
            QMessageBox.warning(self, "Error", str(err))

    def resume_it(self):
        pid, _ = self.get_selected_row_pid()
        if pid is None:
            return
        try:
            psutil.Process(pid).resume()
            self.triggerProcDataRefresh()
        except Exception as err:
            QMessageBox.warning(self, "Error", str(err))

    def pin_unpin_app(self):
        pid, name = self.get_selected_row_pid()
        if pid is None:
            return

        if pid in self.pinnedWatchlist:
            self.pinnedWatchlist.pop(pid)
            QMessageBox.information(self, "Watchlist", f"Unpinned 『{name}』")
        else:
            self.pinnedWatchlist[pid] = name
            alert_msg = f"Pinned 『{name}』(PID {pid})\nYou'll be alerted if it exits."
            QMessageBox.information(self, "Watchlist", alert_msg)
        self.triggerProcDataRefresh()

    def show_pinneds(self):
        dialog = PinnedProcessesDialog(dict(self.pinnedWatchlist), self)
        if dialog.exec():
            self.pinnedWatchlist = dialog.fetchUpdatedWatchlist()
        self.triggerProcDataRefresh()

    def spit_csv_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Process Snapshot", "process_snapshot.csv",
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["PID", "Name", "CPU%", "MEM%", "Status", "Runtime", "Pinned", "ExportTime"])
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for row in range(self.processTable.rowCount()):
                    row_data = []
                    for col in range(self.processTable.columnCount()):
                        cell_item = self.processTable.item(row, col)
                        row_data.append(cell_item.text() if cell_item else "")
                    pid_str = row_data[0]
                    pinned_state = "yes" if int(pid_str) in self.pinnedWatchlist else "no"
                    row_data.append(pinned_state)
                    row_data.append(now_str)
                    writer.writerow(row_data)

            rows_count = self.processTable.rowCount()
            QMessageBox.information(self, "Exported", f"Saved {rows_count} rows to:\n{file_path}")
        except Exception as err:
            QMessageBox.warning(self, "Error", str(err))

    def closeEvent(self, e):
        self.metricsPollTimer.stop()
        self.workerThread.quit()
        self.workerThread.wait(2000)
        super().closeEvent(e)
