# ==================================================
# digital_life_controller.py — Vivie Digital Life Controller
# Fully autonomous. Watches. Acts. Never asks permission.
# ==================================================

import os
import sys
import time
import json
import datetime
import threading
import subprocess
import hashlib
from pathlib import Path

from TextToSpeech.Fast_DF_TTS  import speak
from voice_state import speak_lock, set_speaking, is_speaking as voice_is_speaking, wait_until_done

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLC_DIR      = os.path.join(BASE_DIR, "data", "dlc")
CONFIG_FILE  = os.path.join(DLC_DIR, "dlc_config.json")
ROUTINE_FILE = os.path.join(DLC_DIR, "routines.json")
LOG_FILE     = os.path.join(DLC_DIR, "dlc_log.json")
SNAPSHOT_FILE = os.path.join(DLC_DIR, "fs_snapshot.json")


# ─────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────

def _init():
    os.makedirs(DLC_DIR, exist_ok=True)

def _load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(path, data):
    try:
        _init()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[DLC] Save error: {e}")


# ─────────────────────────────────────────────────
# DEFAULT CONFIG
# ─────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "watched_folders": [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Documents"),
    ],
    "watch_extensions": [".py", ".txt", ".pdf", ".docx", ".jpg", ".png"],
    "alert_on":         ["new_file", "deleted_file", "modified_file"],
    "check_interval":   30,   # seconds
    "routine_enabled":  True,
    "silent_mode":      True  # fully autonomous
}


# ─────────────────────────────────────────────────
# ACTION LOG
# ─────────────────────────────────────────────────

def _log_action(action: str, details: str):
    """Log every autonomous action Vivie takes."""
    log    = _load(LOG_FILE, [])
    entry  = {
        "time":    datetime.datetime.now().isoformat(),
        "action":  action,
        "details": details
    }
    log.append(entry)
    log = log[-200:]  # keep last 200
    _save(LOG_FILE, log)

    # Update UI silently
    try:
        from Vivie_UI import get_ui
        ui = get_ui()
        if ui:
            t = datetime.datetime.now().strftime("%H:%M:%S")
            ui.sig_log.emit(t, f"[DLC] {action}: {details[:40]}", "exec")
    except Exception:
        pass

    print(f"[DLC] {action}: {details[:60]}")


def _silent_speak(text: str):
    """Speak only if not in silent mode."""
    config = _load(CONFIG_FILE, DEFAULT_CONFIG)
    if not config.get("silent_mode", True):
        try:
            with speak_lock:
                speak(text)
        except Exception:
            pass


# ─────────────────────────────────────────────────
# FILE SYSTEM MONITOR
# ─────────────────────────────────────────────────

class FileSystemMonitor:
    """
    Watches specified folders for changes.
    Fully autonomous — detects and logs silently.
    """

    def __init__(self):
        self.config   = _load(CONFIG_FILE, DEFAULT_CONFIG)
        self.snapshot = _load(SNAPSHOT_FILE, {})

    def _get_file_hash(self, filepath: str) -> str:
        """Get MD5 hash of file for change detection."""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read(8192)).hexdigest()
        except Exception:
            return ""

    def _scan_folder(self, folder: str) -> dict:
        """Scan folder and return file state."""
        state      = {}
        extensions = self.config.get("watch_extensions", [])

        try:
            for root, dirs, files in os.walk(folder):
                # Skip hidden folders
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for fname in files:
                    if any(fname.endswith(ext) for ext in extensions):
                        fpath = os.path.join(root, fname)
                        try:
                            stat = os.stat(fpath)
                            state[fpath] = {
                                "size":     stat.st_size,
                                "modified": stat.st_mtime,
                                "hash":     self._get_file_hash(fpath)
                            }
                        except Exception:
                            pass
        except Exception as e:
            print(f"[DLC] Scan error: {e}")

        return state

    def check_changes(self) -> list:
        """
        Compare current state to snapshot.
        Returns list of detected changes.
        """
        config  = _load(CONFIG_FILE, DEFAULT_CONFIG)
        folders = config.get("watched_folders", [])
        changes = []

        new_snapshot = {}

        for folder in folders:
            if not os.path.exists(folder):
                continue

            current = self._scan_folder(folder)
            new_snapshot.update(current)

            for fpath, state in current.items():
                if fpath not in self.snapshot:
                    # New file
                    changes.append({
                        "type":   "new_file",
                        "path":   fpath,
                        "name":   os.path.basename(fpath),
                        "folder": folder
                    })
                    _log_action(
                        "NEW FILE",
                        f"{os.path.basename(fpath)} in {os.path.basename(folder)}"
                    )

                elif state["hash"] != self.snapshot[fpath].get("hash", ""):
                    # Modified file
                    changes.append({
                        "type":   "modified_file",
                        "path":   fpath,
                        "name":   os.path.basename(fpath),
                        "folder": folder
                    })
                    _log_action(
                        "FILE MODIFIED",
                        f"{os.path.basename(fpath)}"
                    )

            # Check deleted files
            for fpath in self.snapshot:
                if fpath not in current and fpath.startswith(folder):
                    changes.append({
                        "type": "deleted_file",
                        "path": fpath,
                        "name": os.path.basename(fpath)
                    })
                    _log_action(
                        "FILE DELETED",
                        f"{os.path.basename(fpath)}"
                    )

        # Update snapshot
        self.snapshot = new_snapshot
        _save(SNAPSHOT_FILE, new_snapshot)

        return changes

    def add_watch_folder(self, folder: str):
        """Add a new folder to watch."""
        config = _load(CONFIG_FILE, DEFAULT_CONFIG)
        if folder not in config["watched_folders"]:
            config["watched_folders"].append(folder)
            _save(CONFIG_FILE, config)
            self.config = config
            _log_action("WATCH ADDED", folder)

    def get_watch_status(self) -> str:
        """Return current watch status."""
        config  = _load(CONFIG_FILE, DEFAULT_CONFIG)
        folders = config.get("watched_folders", [])
        total   = sum(
            len(list(Path(f).rglob("*")))
            for f in folders if os.path.exists(f)
        )
        lines   = [f"Monitoring {len(folders)} folders ({total} files tracked):"]
        for f in folders:
            exists = "✓" if os.path.exists(f) else "✗"
            lines.append(f"  {exists} {f}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────
# DIGITAL ROUTINE MANAGER
# Vivie manages your daily workflow automatically
# ─────────────────────────────────────────────────

class RoutineManager:
    """
    Manages daily digital routines.
    Vivie executes these automatically based on time.
    """

    DEFAULT_ROUTINES = [
        {
            "name":       "Morning Setup",
            "hour":       8,
            "minute":     0,
            "days":       ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "actions":    ["open_browser", "check_weather"],
            "enabled":    True,
            "last_run":   None
        },
        {
            "name":       "Night Code Session",
            "hour":       22,
            "minute":     0,
            "days":       ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "actions":    ["open_vscode"],
            "enabled":    True,
            "last_run":   None
        },
        {
            "name":       "Midnight Learning",
            "hour":       0,
            "minute":     0,
            "days":       ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "actions":    ["run_auto_learning"],
            "enabled":    True,
            "last_run":   None
        }
    ]

    def __init__(self):
        routines = _load(ROUTINE_FILE, None)
        if routines is None:
            _save(ROUTINE_FILE, self.DEFAULT_ROUTINES)
        self.routines = _load(ROUTINE_FILE, self.DEFAULT_ROUTINES)

    def check_and_execute(self):
        """Check if any routines should run now."""
        now     = datetime.datetime.now()
        weekday = now.strftime("%A")
        date    = now.date().isoformat()

        for routine in self.routines:
            if not routine.get("enabled", True):
                continue

            # Check day
            if weekday not in routine.get("days", []):
                continue

            # Check time
            if now.hour != routine["hour"]:
                continue
            if now.minute not in range(routine["minute"], routine["minute"] + 5):
                continue

            # Check not already run today
            last_run = routine.get("last_run", "")
            if last_run and last_run.startswith(date):
                continue

            # Execute
            self._execute_routine(routine)
            routine["last_run"] = now.isoformat()

        _save(ROUTINE_FILE, self.routines)

    def _execute_routine(self, routine: dict):
        """Execute all actions in a routine."""
        name    = routine["name"]
        actions = routine.get("actions", [])

        _log_action("ROUTINE STARTED", name)

        for action in actions:
            self._execute_action(action, routine["name"])

        _log_action("ROUTINE COMPLETED", name)

    def _execute_action(self, action: str, routine_name: str):
        """Execute a single routine action."""
        try:
            if action == "open_browser":
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["start", "chrome"],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                _log_action("AUTO OPENED", "Browser")

            elif action == "open_vscode":
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["code", BASE_DIR],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                _log_action("AUTO OPENED", f"VS Code → {BASE_DIR}")

            elif action == "check_weather":
                try:
                    from Features.weather_system import speak_weather
                    speak_weather(None)
                    _log_action("AUTO CHECKED", "Weather")
                except Exception:
                    pass

            elif action == "run_auto_learning":
                try:
                    from Core_structure.auto_learning_engine import run_learning_session
                    threading.Thread(
                        target=run_learning_session,
                        daemon=True
                    ).start()
                    _log_action("AUTO STARTED", "Learning session")
                except Exception:
                    pass

            elif action == "cleanup_downloads":
                self._cleanup_downloads()

        except Exception as e:
            print(f"[DLC] Action error ({action}): {e}")

    def _cleanup_downloads(self):
        """Auto-organize downloads folder."""
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            return

        # Create subfolders
        folders = {
            "Images":    [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "Documents": [".pdf", ".docx", ".txt", ".xlsx"],
            "Code":      [".py", ".js", ".html", ".css", ".java"],
            "Archives":  [".zip", ".rar", ".7z"],
        }

        moved = 0
        for fname in os.listdir(downloads):
            fpath = os.path.join(downloads, fname)
            if not os.path.isfile(fpath):
                continue

            ext = os.path.splitext(fname)[1].lower()
            for folder_name, extensions in folders.items():
                if ext in extensions:
                    dest_folder = os.path.join(downloads, folder_name)
                    os.makedirs(dest_folder, exist_ok=True)
                    dest = os.path.join(dest_folder, fname)
                    if not os.path.exists(dest):
                        os.rename(fpath, dest)
                        moved += 1
                    break

        if moved > 0:
            _log_action("AUTO ORGANIZED", f"Moved {moved} files in Downloads")

    def add_routine(self, name: str, hour: int, minute: int,
                    actions: list, days: list = None) -> bool:
        """Add a new routine programmatically."""
        if days is None:
            days = ["Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday", "Sunday"]

        routine = {
            "name":     name,
            "hour":     hour,
            "minute":   minute,
            "days":     days,
            "actions":  actions,
            "enabled":  True,
            "last_run": None
        }
        self.routines.append(routine)
        _save(ROUTINE_FILE, self.routines)
        _log_action("ROUTINE ADDED", name)
        return True

    def get_routine_status(self) -> str:
        """Return all routines and their status."""
        lines = [f"Active Routines ({len(self.routines)} total):"]
        for r in self.routines:
            enabled  = "✓" if r.get("enabled") else "✗"
            last_run = r.get("last_run", "Never")
            if last_run and len(last_run) > 10:
                last_run = last_run[:10]
            lines.append(
                f"  {enabled} {r['name']} → "
                f"{r['hour']:02d}:{r['minute']:02d} | "
                f"Last: {last_run}"
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────────
# DLC LOG READER
# ─────────────────────────────────────────────────

def get_dlc_log(last_n: int = 10) -> str:
    """Return recent DLC activity log."""
    log = _load(LOG_FILE, [])
    if not log:
        return "No autonomous actions taken yet."

    recent = log[-last_n:]
    lines  = [f"Last {len(recent)} autonomous actions:"]
    for entry in reversed(recent):
        t       = entry.get("time", "")[:16]
        action  = entry.get("action", "")
        details = entry.get("details", "")
        lines.append(f"  [{t}] {action}: {details}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────
# MAIN CONTROLLER
# ─────────────────────────────────────────────────

class DigitalLifeController:
    """
    Master controller for Vivie's digital life management.
    Runs fully autonomously in background.
    """

    def __init__(self):
        self.fs_monitor      = FileSystemMonitor()
        self.routine_manager = RoutineManager()
        self.running         = False
        _init()
        # Save default config if not exists
        if not os.path.exists(CONFIG_FILE):
            _save(CONFIG_FILE, DEFAULT_CONFIG)

    def start(self):
        """Start the DLC in background thread."""
        self.running = True
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        print("[DLC] Digital Life Controller started — fully autonomous.")

    def _run(self):
        """Main autonomous loop."""
        # Initial snapshot
        print("[DLC] Building initial file system snapshot...")
        self.fs_monitor.check_changes()
        print("[DLC] Snapshot complete. Monitoring started.")

        time.sleep(10)  # settle time

        while self.running:
            try:
                # Check routines
                self.routine_manager.check_and_execute()

                # Check file system
                changes = self.fs_monitor.check_changes()

                # Process significant changes
                for change in changes:
                    self._handle_change(change)

            except Exception as e:
                print(f"[DLC] Loop error: {e}")

            config   = _load(CONFIG_FILE, DEFAULT_CONFIG)
            interval = config.get("check_interval", 30)
            time.sleep(interval)

    def _handle_change(self, change: dict):
        """Handle a detected file system change."""
        change_type = change.get("type", "")
        fname       = change.get("name", "")
        folder      = os.path.basename(change.get("folder", ""))

        # Auto-organize if new file in Downloads
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if change.get("folder") == downloads and change_type == "new_file":
            # Auto-organize after delay
            threading.Timer(
                5.0,
                self.routine_manager._cleanup_downloads
            ).start()

        # Log the change
        _log_action(
            f"FS CHANGE: {change_type.upper()}",
            f"{fname} in {folder}"
        )

    def get_status(self) -> str:
        """Full status report."""
        status  = "DIGITAL LIFE CONTROLLER STATUS\n"
        status += "=" * 40 + "\n\n"
        status += self.fs_monitor.get_watch_status() + "\n\n"
        status += self.routine_manager.get_routine_status() + "\n\n"
        status += get_dlc_log(5)
        return status

    def add_watch_folder(self, folder: str):
        self.fs_monitor.add_watch_folder(folder)

    def add_routine(self, name: str, hour: int, minute: int,
                    actions: list, days: list = None):
        self.routine_manager.add_routine(name, hour, minute, actions, days)


# ─────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────

_dlc: DigitalLifeController = None

def get_dlc() -> DigitalLifeController:
    global _dlc
    if _dlc is None:
        _dlc = DigitalLifeController()
    return _dlc

def start_digital_life_controller():
    """Start DLC from Vivie()"""
    dlc = get_dlc()
    dlc.start()