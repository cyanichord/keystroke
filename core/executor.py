"""
executor.py - Script Executor
Runs flow steps in a daemon thread.
Keyboard: pynput.keyboard.Controller
"""
from __future__ import annotations
import time
import threading
from typing import Any, Callable
from pynput import keyboard as _kb

StatusCallback = Callable[[str], None]


class ScriptExecutor:
    def __init__(self) -> None:
        self._kb_ctrl = _kb.Controller()
        self._thread: threading.Thread | None = None
        self._running = False
        self._status_callbacks: list[StatusCallback] = []

    def subscribe_status(self, cb: StatusCallback) -> None:
        if cb not in self._status_callbacks:
            self._status_callbacks.append(cb)

    def unsubscribe_status(self, cb: StatusCallback) -> None:
        self._status_callbacks = [c for c in self._status_callbacks if c is not cb]

    def _emit(self, msg: str) -> None:
        for cb in list(self._status_callbacks):
            cb(msg)

    @property
    def is_running(self) -> bool:
        return self._running

    def run(self, flow: dict[str, Any], loop: bool = False) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._execute, args=(flow, loop), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _execute(self, flow: dict[str, Any], loop: bool) -> None:
        steps   = flow.get("steps", [])
        spacing = float(flow.get("spacing", 0.05))
        self._emit("▶ Running…" if not loop else "▶ Running (loop)…")
        try:
            cycle = 0
            while self._running:
                cycle += 1
                for i, step in enumerate(steps):
                    if not self._running:
                        break
                    key_str  = step["key"]
                    duration = float(step["duration"])
                    prefix = f"Cycle {cycle} - " if loop else ""
                    self._emit(f"{prefix}Step {i+1}/{len(steps)}: {key_str}")
                    self._press_key(key_str, duration)
                    step_spacing = step.get("spacing", spacing)
                    if step_spacing > 0:
                        self._sleep(float(step_spacing))
                if not loop:
                    break
        except Exception as exc:
            self._emit(f"⚠ Error: {exc}")
        finally:
            self._running = False
            self._emit("⏹ Stopped.")

    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while self._running and time.monotonic() < end:
            time.sleep(0.01)

    def _press_key(self, key_str: str, duration: float) -> None:
        self._press_keyboard(key_str, duration)

    def _press_keyboard(self, combo: str, duration: float) -> None:
        parts = [self._parse_key(p.strip()) for p in combo.split("+")]
        for k in parts:
            self._kb_ctrl.press(k)
        self._sleep(duration)
        for k in reversed(parts):
            self._kb_ctrl.release(k)

    @staticmethod
    def _parse_key(name: str):
        special = {
            "ctrl": _kb.Key.ctrl, "shift": _kb.Key.shift,
            "alt": _kb.Key.alt,   "cmd": _kb.Key.cmd,
            "tab": _kb.Key.tab,   "esc": _kb.Key.esc,
            "enter": _kb.Key.enter, "space": _kb.Key.space,
            "backspace": _kb.Key.backspace, "delete": _kb.Key.delete,
            "up": _kb.Key.up,     "down": _kb.Key.down,
            "left": _kb.Key.left, "right": _kb.Key.right,
            "home": _kb.Key.home, "end": _kb.Key.end,
            "page_up": _kb.Key.page_up, "page_down": _kb.Key.page_down,
            **{f"f{i}": getattr(_kb.Key, f"f{i}") for i in range(1, 13)},
        }
        lo = name.lower()
        if lo in special:
            return special[lo]
        if len(name) == 1:
            return _kb.KeyCode.from_char(name)
        try:
            return _kb.KeyCode.from_vk(int(name, 16))
        except ValueError:
            return _kb.KeyCode.from_char(name[0])

