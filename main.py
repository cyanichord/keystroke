"""
main.py - Entry point
1. Request admin privileges (Windows UAC / macOS AppleScript / Linux sudo)
2. Launch the PyQt6 application
"""
import os
import sys
from datetime import datetime
from core.privilege import ensure_admin, is_admin


_LOG_PATH = os.path.join(os.path.dirname(__file__), "app.log")


def _log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {message}\n"
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass


def main() -> None:
    # Must be called BEFORE creating QApplication so the process can be
    # re-launched cleanly on Windows (UAC spawns a new process).
    _log(
        f"main start | pid={os.getpid()} | argv={sys.argv} | exe={sys.executable}"
    )
    ensure_admin()
    _log(f"ensure_admin returned | is_admin={is_admin()}")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from ui.main_window import MainWindow

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("Keystroke Script")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("KeyScriptApp")

        window = MainWindow()
        window.show()
        _log("window shown - entering event loop")
        exit_code = app.exec()
        _log(f"event loop exited | code={exit_code}")
        sys.exit(exit_code)
    except Exception as exc:
        _log(f"startup exception | {type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
