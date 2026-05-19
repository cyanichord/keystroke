"""
main_window.py - MainWindow (PyQt6, Apple HIG layout)
Layout:
  Toolbar -> title + theme toggle + file actions
  Splitter -> Left (flow info + key capture) | Right (tabs: editor / key-ref / log)
  Action bar -> Run (Enter) + Stop (Space)
  Status bar -> status text + admin indicator
"""
from __future__ import annotations
import json
import time

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGridLayout,
    QPushButton, QLabel, QPlainTextEdit, QTabWidget,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QStatusBar, QFrame, QSizePolicy,
    QMessageBox, QToolBar, QCheckBox,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter, QAction

from ui.styles import build_stylesheet
from core.flow_manager import FlowManager
from core.listener import GlobalKeyListener
from core.executor import ScriptExecutor
from core.key_reference import KEYBOARD_KEYS


# -- JSON syntax highlighter --------------------------------------------------
class JSONHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text: str) -> None:
        import re
        rules = [
            (r'"(\\.|[^"\\])*"',       QColor("#E6DB74")),
            (r'\b(true|false|null)\b', QColor("#AE81FF")),
            (r'\b-?\d+\.?\d*\b',       QColor("#66D9EF")),
            (r'[{}\[\]]',              QColor("#F8F8F2")),
        ]
        for pattern, color in rules:
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# -- Thread-safe signal bridge ------------------------------------------------
class _Bridge(QObject):
    status_changed = pyqtSignal(str)
    key_captured   = pyqtSignal(str)


# -- MainWindow ----------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._dark = False
        self._flow_mgr  = FlowManager()
        self._executor  = ScriptExecutor()
        self._listener  = GlobalKeyListener()
        self._capture_mode = ""
        self._captured_duration: float | None = None
        self._press_times: dict[str, float] = {}
        self._auto_steps: list[dict[str, float | str]] = []
        self._auto_last_release: float | None = None
        self._tap_threshold = 0.07
        self._tap_default = 0.1
        self._bridge    = _Bridge()

        self._build_ui()
        self._connect_signals()
        self._apply_theme()
        self._listener.start()
        self._refresh_hotkey_labels()
        self._update_status("Ready - use configured hotkeys to run/stop.")

    # ------------------------------- UI BUILD ---------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle("Keystroke Script")
        self.setMinimumSize(1280, 620)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.addToolBar(self._build_toolbar())

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.addWidget(self._build_left_panel())
        self._splitter.addWidget(self._build_right_panel())
        self._splitter.setSizes([300, 660])
        root.addWidget(self._splitter, stretch=1)

        root.addWidget(self._build_action_bar())

        self._status_bar   = QStatusBar()
        self._status_label = QLabel("Ready")
        self._admin_label  = QLabel()
        self._status_bar.addWidget(self._status_label, 1)
        self._status_bar.addPermanentWidget(self._admin_label)
        self.setStatusBar(self._status_bar)
        self._refresh_admin_label()

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))

        lbl = QLabel("  Keystroke Script")
        lbl.setProperty("class", "headline")
        tb.addWidget(lbl)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self._act_new   = QAction("New",   self)
        self._act_open  = QAction("Open...", self)
        self._act_save  = QAction("Save...", self)
        self._act_theme = QAction("🌙 Dark", self)
        self._act_theme.setCheckable(True)
        for a in (self._act_new, self._act_open, self._act_save, self._act_theme):
            tb.addAction(a)
        return tb

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 6, 12)
        lay.setSpacing(12)

        info = QGroupBox("Flow Info")
        il   = QVBoxLayout(info)
        self._lbl_file    = QLabel("No file loaded")
        self._lbl_steps   = QLabel("Steps: 0")
        self._lbl_spacing = QLabel("Spacing: -")
        self._chk_loop    = QCheckBox("")
        self._chk_loop.setChecked(False)
        self._lbl_start_key = QLabel("")
        self._lbl_stop_key  = QLabel("")
        self._lbl_capture_key = QLabel("")
        self._lbl_auto_capture_key = QLabel("")
        self._btn_set_start = QPushButton("Set Start Key")
        self._btn_set_stop  = QPushButton("Set Stop Key")
        self._btn_set_capture = QPushButton("Set Capture Key")
        self._btn_set_auto_capture = QPushButton("Set Auto Capture Key")
        self._btn_set_start.setProperty("class", "secondary")
        self._btn_set_stop.setProperty("class", "secondary")
        self._btn_set_capture.setProperty("class", "secondary")
        self._btn_set_auto_capture.setProperty("class", "secondary")
        for lb in (self._lbl_file, self._lbl_steps, self._lbl_spacing):
            lb.setProperty("class", "caption")
            lb.setWordWrap(True)
            il.addWidget(lb)
        il.addWidget(self._chk_loop)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.addWidget(self._lbl_start_key, 0, 0)
        grid.addWidget(self._btn_set_start, 0, 1)
        grid.addWidget(self._lbl_stop_key, 1, 0)
        grid.addWidget(self._btn_set_stop, 1, 1)
        grid.addWidget(self._lbl_capture_key, 2, 0)
        grid.addWidget(self._btn_set_capture, 2, 1)
        grid.addWidget(self._lbl_auto_capture_key, 3, 0)
        grid.addWidget(self._btn_set_auto_capture, 3, 1)
        il.addLayout(grid)
        lay.addWidget(info)

        cap = QGroupBox("Key Capture")
        cl  = QVBoxLayout(cap)
        self._lbl_capture_hint = QLabel("")
        self._lbl_capture_hint.setProperty("class", "caption")
        self._lbl_capture_hint.setWordWrap(True)
        self._lbl_captured = QLabel("-")
        self._lbl_captured.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_captured.setProperty("class", "headline")
        self._lbl_duration = QLabel("Duration: -")
        self._lbl_duration.setProperty("class", "caption")
        self._btn_capture = QPushButton("Capture Key")
        self._btn_capture.setProperty("class", "secondary")
        self._btn_auto_capture = QPushButton("Auto Capture")
        self._btn_auto_capture.setProperty("class", "secondary")
        self._btn_insert  = QPushButton("Insert into Flow")
        self._btn_insert.setProperty("class", "secondary")
        self._btn_insert.setEnabled(False)
        for w2 in (
            self._lbl_capture_hint, self._lbl_captured, self._lbl_duration,
            self._btn_capture, self._btn_auto_capture, self._btn_insert,
        ):
            cl.addWidget(w2)
        lay.addWidget(cap)
        lay.addStretch()
        return w

    def _build_right_panel(self) -> QWidget:
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        # Tab 1 - JSON Editor
        ew  = QWidget()
        el  = QVBoxLayout(ew)
        el.setContentsMargins(12, 12, 12, 12)
        el.setSpacing(8)
        el.addWidget(QLabel("Flow JSON"))
        self._editor = QPlainTextEdit()
        self._editor.setProperty("class", "code")
        self._editor.setPlainText(self._flow_mgr.default_text())
        JSONHighlighter(self._editor.document())
        el.addWidget(self._editor, stretch=1)
        btn_row = QHBoxLayout()
        self._btn_apply = QPushButton("Apply")
        self._btn_reset = QPushButton("Reset")
        self._btn_reset.setProperty("class", "secondary")
        btn_row.addWidget(self._btn_apply)
        btn_row.addWidget(self._btn_reset)
        btn_row.addStretch()
        el.addLayout(btn_row)
        self._tabs.addTab(ew, "Flow Editor")

        # Tab 2 - Key Reference
        rw = QWidget()
        rl = QVBoxLayout(rw)
        rl.setContentsMargins(12, 12, 12, 12)
        rt = QTabWidget()
        rt.addTab(self._make_key_table(KEYBOARD_KEYS), "Keyboard")
        rl.addWidget(rt)
        self._tabs.addTab(rw, "Key Reference")

        # Tab 3 - Log
        lw = QWidget()
        ll = QVBoxLayout(lw)
        ll.setContentsMargins(12, 12, 12, 12)
        self._log = QPlainTextEdit()
        self._log.setProperty("class", "code")
        self._log.setReadOnly(True)
        ll.addWidget(self._log)
        btn_clr = QPushButton("Clear Log")
        btn_clr.setProperty("class", "secondary")
        btn_clr.clicked.connect(self._log.clear)
        ll.addWidget(btn_clr, alignment=Qt.AlignmentFlag.AlignRight)
        self._tabs.addTab(lw, "Log")

        return self._tabs

    @staticmethod
    def _make_key_table(rows: list[dict]) -> QTableWidget:
        tbl = QTableWidget(len(rows), 3)
        tbl.setHorizontalHeaderLabels(["Category", "Key String", "Description"])
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setAlternatingRowColors(True)
        for i, row in enumerate(rows):
            tbl.setItem(i, 0, QTableWidgetItem(row["category"]))
            tbl.setItem(i, 1, QTableWidgetItem(row["key"]))
            tbl.setItem(i, 2, QTableWidgetItem(row["description"]))
        return tbl

    def _build_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(10)
        self._lbl_hotkeys = QLabel("")
        self._lbl_hotkeys.setProperty("class", "caption")
        lay.addWidget(self._lbl_hotkeys)
        lay.addStretch()
        self._btn_run  = QPushButton("▶  Run")
        self._btn_run.setProperty("class", "run")
        self._btn_run.setMinimumWidth(140)
        self._btn_stop = QPushButton("⏹  Stop")
        self._btn_stop.setProperty("class", "stop")
        self._btn_stop.setMinimumWidth(140)
        lay.addWidget(self._btn_run)
        lay.addWidget(self._btn_stop)
        return bar

    # ------------------------------- SIGNALS ----------------------------------
    def _connect_signals(self) -> None:
        self._act_new.triggered.connect(self._on_new)
        self._act_open.triggered.connect(self._on_open)
        self._act_save.triggered.connect(self._on_save)
        self._act_theme.toggled.connect(self._on_theme)

        self._btn_apply.clicked.connect(self._on_apply)
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_capture.clicked.connect(self._toggle_capture)
        self._btn_auto_capture.clicked.connect(self._toggle_auto_capture)
        self._btn_insert.clicked.connect(self._insert_key)
        self._btn_set_start.clicked.connect(self._capture_start_key)
        self._btn_set_stop.clicked.connect(self._capture_stop_key)
        self._btn_set_capture.clicked.connect(self._capture_capture_key)
        self._btn_set_auto_capture.clicked.connect(self._capture_auto_capture_key)
        self._btn_run.clicked.connect(self._on_run)
        self._btn_stop.clicked.connect(self._on_stop)

        # Global listener (highest priority)
        self._listener.subscribe_run(self._on_run)
        self._listener.subscribe_stop(self._on_stop)
        self._listener.subscribe_capture(self._toggle_capture_hotkey)
        self._listener.subscribe_auto_capture(self._toggle_auto_capture_hotkey)
        self._listener.subscribe_key_down(self._on_key_down_event)
        self._listener.subscribe_key_up(self._on_key_up_event)

        # Cross-thread bridge
        self._bridge.status_changed.connect(self._update_status)
        self._bridge.key_captured.connect(self._show_captured)
        self._executor.subscribe_status(
            lambda m: self._bridge.status_changed.emit(m)
        )

    # ------------------------------- SLOTS ------------------------------------
    def _on_new(self) -> None:
        self._editor.setPlainText(self._flow_mgr.default_text())
        self._lbl_file.setText("Unsaved new flow")
        self._refresh_info()

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Flow", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            self._flow_mgr.load(path)
            self._editor.setPlainText(self._flow_mgr.to_text())
            self._lbl_file.setText(path)
            self._refresh_info()
            self._update_status(f"Loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Flow", "flow.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            self._on_apply()
            self._flow_mgr.save(path)
            self._lbl_file.setText(path)
            self._update_status(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _on_theme(self, checked: bool) -> None:
        self._dark = checked
        self._act_theme.setText("☀ Light" if checked else "🌙 Dark")
        self._apply_theme()

    def _on_apply(self) -> None:
        try:
            self._flow_mgr.from_text(self._editor.toPlainText())
            self._refresh_info()
            self._update_status("Flow applied ✓")
        except Exception as e:
            QMessageBox.warning(self, "Invalid JSON", str(e))

    def _on_reset(self) -> None:
        self._editor.setPlainText(self._flow_mgr.default_text())
        self._refresh_info()

    def _on_run(self) -> None:
        if self._executor.is_running:
            return
        try:
            self._on_apply()
        except Exception:
            return
        self._executor.run(self._flow_mgr.flow, loop=self._chk_loop.isChecked())
        self._append_log("▶ Started")

    def _on_stop(self) -> None:
        self._executor.stop()
        self._append_log("⏹ Stop requested")

    def _toggle_capture(self) -> None:
        if self._capture_mode == "flow":
            self._end_capture("Capture cancelled.")
            return
        if self._capture_mode:
            self._update_status("Finish current capture first.")
            return
        self._begin_capture("flow")
        self._btn_capture.setText("Cancel Capture")
        self._lbl_captured.setText("...waiting...")
        self._update_status("Press any key (not Enter/Space) to capture")

    def _toggle_auto_capture(self) -> None:
        if self._capture_mode == "auto":
            self._finalize_auto_capture()
            self._end_capture("Auto capture stopped.")
            return
        if self._capture_mode:
            self._update_status("Finish current capture first.")
            return
        self._auto_steps = []
        self._auto_last_release = None
        self._begin_capture("auto")
        self._btn_auto_capture.setText("Stop Auto Capture")
        self._lbl_captured.setText("...listening...")
        self._lbl_duration.setText("Duration: -")
        self._update_status("Auto capture started - press keys to build flow")

    def _capture_start_key(self) -> None:
        if self._capture_mode == "start":
            self._end_capture("Start key capture cancelled.")
            return
        self._begin_capture("start")
        self._btn_set_start.setText("Cancel Start Key")
        self._update_status("Press the start hotkey")

    def _capture_stop_key(self) -> None:
        if self._capture_mode == "stop":
            self._end_capture("Stop key capture cancelled.")
            return
        self._begin_capture("stop")
        self._btn_set_stop.setText("Cancel Stop Key")
        self._update_status("Press the stop hotkey")

    def _capture_capture_key(self) -> None:
        if self._capture_mode == "capture":
            self._end_capture("Capture hotkey cancelled.")
            return
        self._begin_capture("capture")
        self._btn_set_capture.setText("Cancel Capture Key")
        self._update_status("Press the capture hotkey")

    def _capture_auto_capture_key(self) -> None:
        if self._capture_mode == "auto_hotkey":
            self._end_capture("Auto capture hotkey cancelled.")
            return
        self._begin_capture("auto_hotkey")
        self._btn_set_auto_capture.setText("Cancel Auto Capture Key")
        self._update_status("Press the auto capture hotkey")

    def _toggle_capture_hotkey(self) -> None:
        if self._capture_mode == "flow":
            self._end_capture("Capture cancelled.")
            return
        if self._capture_mode:
            return
        self._begin_capture("flow")
        self._btn_capture.setText("Cancel Capture")
        self._lbl_captured.setText("...waiting...")
        self._update_status("Press any key to capture")

    def _toggle_auto_capture_hotkey(self) -> None:
        self._toggle_auto_capture()

    def _on_key_down_event(self, combo: str) -> None:
        if not self._capture_mode:
            return
        mode = self._capture_mode
        if mode == "flow":
            if combo in {
                self._listener.get_run_key(),
                self._listener.get_stop_key(),
                self._listener.get_capture_key(),
                self._listener.get_auto_capture_key(),
            }:
                self._update_status("Hotkeys cannot be recorded into the flow.")
                return
            if combo not in self._press_times:
                self._press_times[combo] = time.monotonic()
                self._lbl_captured.setText(combo)
                self._lbl_duration.setText("Duration: ...")
            return
        if mode == "auto":
            if combo in {
                self._listener.get_run_key(),
                self._listener.get_stop_key(),
                self._listener.get_capture_key(),
                self._listener.get_auto_capture_key(),
            }:
                return
            if self._auto_last_release is not None and self._auto_steps:
                gap = time.monotonic() - self._auto_last_release
                self._auto_steps[-1]["spacing"] = round(gap, 3)
            if combo not in self._press_times:
                self._press_times[combo] = time.monotonic()
                self._lbl_captured.setText(combo)
                self._lbl_duration.setText("Duration: ...")
            return
        self._end_capture("")
        if mode == "start":
            self._listener.set_run_key(combo)
            self._refresh_hotkey_labels()
            self._update_status(f"Start hotkey set to: {combo}")
            return
        if mode == "stop":
            self._listener.set_stop_key(combo)
            self._refresh_hotkey_labels()
            self._update_status(f"Stop hotkey set to: {combo}")
            return
        if mode == "capture":
            self._listener.set_capture_key(combo)
            self._refresh_hotkey_labels()
            self._update_status(f"Capture hotkey set to: {combo}")
            return
        if mode == "auto_hotkey":
            self._listener.set_auto_capture_key(combo)
            self._refresh_hotkey_labels()
            self._update_status(f"Auto capture hotkey set to: {combo}")
            return

    def _on_key_up_event(self, combo: str) -> None:
        if self._capture_mode not in {"flow", "auto"}:
            return
        if combo in {
            self._listener.get_run_key(),
            self._listener.get_stop_key(),
            self._listener.get_capture_key(),
            self._listener.get_auto_capture_key(),
        }:
            return
        start = self._press_times.pop(combo, None)
        if start is None:
            return
        held = time.monotonic() - start
        duration = held if held >= self._tap_threshold else self._tap_default
        self._captured_duration = round(duration, 3)
        self._lbl_duration.setText(f"Duration: {self._captured_duration}s")
        if self._capture_mode == "flow":
            self._bridge.key_captured.emit(combo)
            return
        self._auto_steps.append({"key": combo, "duration": self._captured_duration})
        self._auto_last_release = time.monotonic()
        self._update_status(
            f"Auto captured: {combo} ({self._captured_duration}s)"
        )

    def _show_captured(self, combo: str) -> None:
        self._lbl_captured.setText(combo)
        self._btn_capture.setText("Capture Key")
        self._btn_insert.setEnabled(True)
        if self._captured_duration is not None:
            self._update_status(
                f"Captured: {combo} ({self._captured_duration}s)"
            )
        else:
            self._update_status(f"Captured: {combo}")

    def _insert_key(self) -> None:
        combo = self._lbl_captured.text()
        if not combo or combo == "-":
            return
        duration = self._captured_duration or self._tap_default
        try:
            flow = json.loads(self._editor.toPlainText())
        except Exception:
            flow = {"spacing": 0.05, "steps": []}
        flow["steps"].append({"key": combo, "duration": duration})
        self._editor.setPlainText(json.dumps(flow, indent=2))
        self._refresh_info()
        self._update_status(f"Inserted: {combo} ({duration}s)")

    # ------------------------------- HELPERS ----------------------------------
    def _refresh_info(self) -> None:
        try:
            f = json.loads(self._editor.toPlainText())
            self._lbl_steps.setText(f"Steps: {len(f.get('steps', []))}")
            self._lbl_spacing.setText(f"Spacing: {f.get('spacing', '?')} s")
        except Exception:
            self._lbl_steps.setText("Steps: (invalid JSON)")

    def _refresh_admin_label(self) -> None:
        from core.privilege import is_admin
        if is_admin():
            self._admin_label.setText("🔑 Admin")
            self._admin_label.setToolTip("Running with administrator privileges")
        else:
            self._admin_label.setText("⚠ No Admin")
            self._admin_label.setToolTip(
                "Not running as administrator - global capture may be limited"
            )

    def _update_status(self, msg: str) -> None:
        self._status_label.setText(msg)
        self._append_log(msg)

    def _append_log(self, msg: str) -> None:
        self._log.appendPlainText(msg)
        self._log.verticalScrollBar().setValue(
            self._log.verticalScrollBar().maximum()
        )

    def _apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(dark=self._dark))

    def _begin_capture(self, mode: str) -> None:
        self._capture_mode = mode
        self._listener.set_hotkeys_enabled(False)
        self._btn_insert.setEnabled(False)
        self._btn_set_start.setEnabled(False)
        self._btn_set_stop.setEnabled(False)
        self._btn_set_capture.setEnabled(False)
        self._btn_set_auto_capture.setEnabled(False)
        self._btn_auto_capture.setEnabled(mode == "auto")
        if mode != "flow":
            self._btn_capture.setEnabled(False)

    def _end_capture(self, status: str) -> None:
        self._capture_mode = ""
        self._listener.set_hotkeys_enabled(True)
        self._btn_capture.setEnabled(True)
        self._btn_capture.setText("Capture Key")
        self._btn_set_start.setText("Set Start Key")
        self._btn_set_stop.setText("Set Stop Key")
        self._btn_set_capture.setText("Set Capture Key")
        self._btn_set_auto_capture.setText("Set Auto Capture Key")
        self._btn_set_start.setEnabled(True)
        self._btn_set_stop.setEnabled(True)
        self._btn_set_capture.setEnabled(True)
        self._btn_set_auto_capture.setEnabled(True)
        self._btn_auto_capture.setEnabled(True)
        self._btn_auto_capture.setText("Auto Capture")
        if status:
            self._update_status(status)

    def _finalize_auto_capture(self) -> None:
        if not self._auto_steps:
            self._update_status("Auto capture finished - no steps captured.")
            return
        try:
            flow = json.loads(self._editor.toPlainText())
        except Exception:
            flow = {"spacing": 0.05, "steps": []}
        flow_steps = flow.get("steps", [])
        flow_steps.extend(self._auto_steps)
        flow["steps"] = flow_steps
        self._editor.setPlainText(json.dumps(flow, indent=2))
        self._refresh_info()
        self._update_status(f"Auto capture appended {len(self._auto_steps)} steps.")

    def _refresh_hotkey_labels(self) -> None:
        run_key = self._listener.get_run_key()
        stop_key = self._listener.get_stop_key()
        capture_key = self._listener.get_capture_key()
        auto_capture_key = self._listener.get_auto_capture_key()
        self._lbl_start_key.setText(f"Start key: {run_key}")
        self._lbl_stop_key.setText(f"Stop key: {stop_key}")
        self._lbl_capture_key.setText(f"Capture key: {capture_key}")
        self._lbl_auto_capture_key.setText(f"Auto capture key: {auto_capture_key}")
        self._btn_run.setText(f"▶  Run ({run_key})")
        self._btn_stop.setText(f"⏹  Stop ({stop_key})")
        self._chk_loop.setText(f"Loop until {stop_key}")
        self._lbl_capture_hint.setText(
            f"Click 'Capture Key' then press any key\n(not {run_key} or {stop_key})."
        )
        self._lbl_hotkeys.setText(
            "Global hotkeys:  "
            f"{run_key} = Run  |  {stop_key} = Stop  |  "
            f"{capture_key} = Capture  |  {auto_capture_key} = Auto"
        )

    def closeEvent(self, event) -> None:
        self._executor.stop()
        self._listener.stop()
        event.accept()
