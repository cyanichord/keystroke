"""
listener.py - Global Keyboard Listener (Observer / Listener Pattern)
Uses pynput for OS-level keyboard capture - works even without focus.

Priority rules:
  Enter  -> fire all run-callbacks   (highest priority)
  Space  -> fire all stop-callbacks  (highest priority)
  Other  -> fire key-captured callbacks with combo string
"""
from __future__ import annotations
import threading
from typing import Callable
from pynput import keyboard as _kb

KeyCallback = Callable[[str], None]
KeyDownCallback = Callable[[str], None]
KeyUpCallback = Callable[[str], None]


def _normalise(key) -> str:
    if key is None:
        return ""
    if isinstance(key, _kb.KeyCode):
        if key.char:
            return key.char
        return f"<0x{key.vk:x}>" if key.vk else str(key)
    return key.name if hasattr(key, "name") else str(key)


class GlobalKeyListener:
    """
    Singleton. Wraps pynput Listener and dispatches to registered observers.
    """
    _instance: "GlobalKeyListener | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "GlobalKeyListener":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init()
                cls._instance = inst
        return cls._instance

    def _init(self) -> None:
        self._run_callbacks:  list[Callable[[], None]] = []
        self._stop_callbacks: list[Callable[[], None]] = []
        self._capture_callbacks: list[Callable[[], None]] = []
        self._auto_capture_callbacks: list[Callable[[], None]] = []
        self._key_down_callbacks: list[KeyDownCallback] = []
        self._key_up_callbacks: list[KeyUpCallback] = []
        self._key_callbacks:  list[KeyCallback] = []
        self._pressed_mods:   set[str] = set()
        self._down_map: dict[object, str] = {}
        self._listener: _kb.Listener | None = None
        self._active = False
        self._run_key = ","
        self._stop_key = "."
        self._capture_key = "["
        self._auto_capture_key = "]"
        self._hotkeys_enabled = True

    # -- Observer registration -------------------------------------------------
    def subscribe_run(self, cb: Callable[[], None]) -> None:
        if cb not in self._run_callbacks:
            self._run_callbacks.append(cb)

    def unsubscribe_run(self, cb: Callable[[], None]) -> None:
        self._run_callbacks = [c for c in self._run_callbacks if c is not cb]

    def subscribe_stop(self, cb: Callable[[], None]) -> None:
        if cb not in self._stop_callbacks:
            self._stop_callbacks.append(cb)

    def unsubscribe_stop(self, cb: Callable[[], None]) -> None:
        self._stop_callbacks = [c for c in self._stop_callbacks if c is not cb]

    def subscribe_key(self, cb: KeyCallback) -> None:
        if cb not in self._key_callbacks:
            self._key_callbacks.append(cb)

    def unsubscribe_key(self, cb: KeyCallback) -> None:
        self._key_callbacks = [c for c in self._key_callbacks if c is not cb]

    def subscribe_key_down(self, cb: KeyDownCallback) -> None:
        if cb not in self._key_down_callbacks:
            self._key_down_callbacks.append(cb)

    def unsubscribe_key_down(self, cb: KeyDownCallback) -> None:
        self._key_down_callbacks = [c for c in self._key_down_callbacks if c is not cb]

    def subscribe_key_up(self, cb: KeyUpCallback) -> None:
        if cb not in self._key_up_callbacks:
            self._key_up_callbacks.append(cb)

    def unsubscribe_key_up(self, cb: KeyUpCallback) -> None:
        self._key_up_callbacks = [c for c in self._key_up_callbacks if c is not cb]

    def subscribe_capture(self, cb: Callable[[], None]) -> None:
        if cb not in self._capture_callbacks:
            self._capture_callbacks.append(cb)

    def unsubscribe_capture(self, cb: Callable[[], None]) -> None:
        self._capture_callbacks = [c for c in self._capture_callbacks if c is not cb]

    def subscribe_auto_capture(self, cb: Callable[[], None]) -> None:
        if cb not in self._auto_capture_callbacks:
            self._auto_capture_callbacks.append(cb)

    def unsubscribe_auto_capture(self, cb: Callable[[], None]) -> None:
        self._auto_capture_callbacks = [c for c in self._auto_capture_callbacks if c is not cb]

    def set_run_key(self, combo: str) -> None:
        self._run_key = combo.strip().lower()

    def set_stop_key(self, combo: str) -> None:
        self._stop_key = combo.strip().lower()

    def set_capture_key(self, combo: str) -> None:
        self._capture_key = combo.strip().lower()

    def set_auto_capture_key(self, combo: str) -> None:
        self._auto_capture_key = combo.strip().lower()

    def get_run_key(self) -> str:
        return self._run_key

    def get_stop_key(self) -> str:
        return self._stop_key

    def get_capture_key(self) -> str:
        return self._capture_key

    def get_auto_capture_key(self) -> str:
        return self._auto_capture_key

    def set_hotkeys_enabled(self, enabled: bool) -> None:
        self._hotkeys_enabled = enabled

    # -- Lifecycle -------------------------------------------------------------
    def start(self) -> None:
        if self._active:
            return
        self._listener = _kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        self._active = True

    def stop(self) -> None:
        if not self._active:
            return
        if self._listener:
            self._listener.stop()
        self._active = False

    # -- pynput callbacks ------------------------------------------------------
    _MOD_CANONICAL = {
        "ctrl_l": "ctrl", "ctrl_r": "ctrl", "ctrl": "ctrl",
        "shift_l": "shift", "shift_r": "shift", "shift": "shift",
        "alt_l": "alt", "alt_r": "alt", "alt_gr": "alt",
        "cmd": "cmd", "cmd_r": "cmd",
    }

    def _on_press(self, key) -> None:
        name = _normalise(key)
        canonical = self._MOD_CANONICAL.get(name, name)

        if canonical in ("ctrl", "shift", "alt", "cmd"):
            self._pressed_mods.add(canonical)
            return

        combo = self._build_combo(canonical)
        if combo == self._capture_key:
            for cb in list(self._capture_callbacks):
                cb()
            return
        if combo == self._auto_capture_key:
            for cb in list(self._auto_capture_callbacks):
                cb()
            return
        if self._hotkeys_enabled:
            if combo == self._run_key:
                for cb in list(self._run_callbacks):
                    cb()
                return
            if combo == self._stop_key:
                for cb in list(self._stop_callbacks):
                    cb()
                return

        self._down_map[key] = combo
        for cb in list(self._key_down_callbacks):
            cb(combo)
        for cb in list(self._key_callbacks):
            cb(combo)

    def _on_release(self, key) -> None:
        name = _normalise(key)
        canonical = self._MOD_CANONICAL.get(name, name)
        if canonical in ("ctrl", "shift", "alt", "cmd"):
            self._pressed_mods.discard(canonical)
            return

        combo = self._down_map.pop(key, self._build_combo(canonical))
        for cb in list(self._key_up_callbacks):
            cb(combo)

    def _build_combo(self, key_name: str) -> str:
        parts = [m for m in ("ctrl", "shift", "alt", "cmd")
                 if m in self._pressed_mods]
        parts.append(key_name)
        return "+".join(parts)
