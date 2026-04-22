

import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

from log_config import suppress_noise
suppress_noise()

# ==================================================
# Vivie.py — Main Entry Point (UI Integrated)
# ==================================================

import threading
import sys
import random
import atexit
import os as _os
import os as _os_ui
import webbrowser

from Automation.internet_check    import is_Online
from Features.Alert               import Alert
from DATA.DLG_Data                import online_dlg, offline_dlg
from main_brain                   import Vivie
from TextToSpeech.Fast_DF_TTS     import speak
from Automation.Battery           import check_plug
from Time_operations.time_monitor import check_schedule, check_Alam
from Vivie_UI                     import launch_ui

_BASE = _os.path.dirname(_os.path.abspath(__file__))
Alarm_path = _os.path.join(_BASE, "alarm_data.txt")
file_path  = _os.path.join(_BASE, "schedule.txt")

ran_online_dlg  = random.choice(online_dlg)
ran_offline_dlg = random.choice(offline_dlg)


# ─────────────────────────────────────────────────
# EXIT HANDLER — saves session on close
# ─────────────────────────────────────────────────

def _on_exit():
    try:
        from memory_core.session_memory import get_session_memory
        get_session_memory().end_session()
        print("[SessionMemory] Session saved on exit.")
    except Exception:
        pass

atexit.register(_on_exit)

def open_ui():
    """Auto-open Vivie UI in default browser after short delay."""
    import time, threading
    def _launch():
        time.sleep(2)   # wait for WebSocket server to start
        ui_path = _os_ui.path.join(
            _os_ui.path.dirname(_os_ui.path.abspath(__file__)),
            "UI.html"
        )
        webbrowser.open(f"file:///{ui_path.replace(chr(92), '/')}")
        print("🖥  UI launched in browser.")
    threading.Thread(target=_launch, daemon=True).start()


# ─────────────────────────────────────────────────
# WISH
# ─────────────────────────────────────────────────

def wish():
    t1 = threading.Thread(target=speak, args=(ran_online_dlg,))
    t2 = threading.Thread(target=Alert, args=(ran_online_dlg,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


# ─────────────────────────────────────────────────
# BRAIN THREADS
# ─────────────────────────────────────────────────

def start_brain_threads():
    t3 = threading.Thread(target=check_plug,                           daemon=True)
    t5 = threading.Thread(target=Vivie,                                daemon=True)
    t6 = threading.Thread(target=check_schedule, args=(file_path,),    daemon=True)
    t7 = threading.Thread(target=check_Alam,     args=(Alarm_path,),   daemon=True)
    t3.start()
    t5.start()
    t6.start()
    t7.start()
    open_ui()


# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────

import time

def main():
    if is_Online():
        wish()
        
        # Start all the brain background threads
        start_brain_threads()
        launch_ui()
        
        # Keep the main Python script running forever
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down Vivie...")
            sys.exit(0)

    else:
        Alert(ran_offline_dlg)

main()