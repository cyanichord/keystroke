"""
privilege.py
Cross-platform admin-privilege escalation.
  Windows  -> ShellExecuteW UAC prompt
  macOS    -> AppleScript sudo re-launch
  Linux    -> pkexec / gksudo / sudo re-launch
"""
import os
import sys
import platform
from datetime import datetime


_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.log")


def _log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {message}\n"
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass


def is_admin() -> bool:
    if platform.system() == "Windows":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.getuid() == 0


def ensure_admin() -> None:
    """
    If not already admin, re-launch the script with elevated privileges.
    On Windows this triggers a UAC dialog box.
    """
    _log(f"ensure_admin start | pid={os.getpid()} | argv={sys.argv}")
    if is_admin():
        _log("already admin - continuing")
        return

    system = platform.system()

    if system == "Windows":
        import ctypes
        params = " ".join(f'"{a}"' for a in sys.argv)
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        _log(f"ShellExecuteW runas ret={ret}")
        # ret <= 32 means failure (e.g. user cancelled UAC) - continue without admin
        if ret > 32:
            _log("relaunch requested - exiting original process")
            sys.exit(0)

    elif system == "Darwin":
        cmd = " ".join([sys.executable] + sys.argv).replace('"', '\\"')
        script = f'do shell script "{cmd}" with administrator privileges'
        os.system(f"osascript -e '{script}' &")
        _log("macOS relaunch requested - exiting original process")
        sys.exit(0)

    else:
        args = [sys.executable] + sys.argv
        for escalator in ("pkexec", "gksudo", "kdesudo"):
            if os.system(f"which {escalator} > /dev/null 2>&1") == 0:
                _log(f"linux relaunch via {escalator}")
                os.execvp(escalator, [escalator] + args)
        _log("linux relaunch via sudo")
        os.execvp("sudo", ["sudo"] + args)
