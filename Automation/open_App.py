import subprocess
import pyautogui as gui
import time
import platform


# ==============================
# 🔐 WHITELISTED APPLICATION MAP
# ==============================

APP_MAP = {
    "chrome": "chrome",
    "google": "chrome",
    "youtube": "start chrome https://www.youtube.com",
    "spotify": "spotify",
    "notepad": "notepad",
    "calculator": "calc",
    "cmd": "cmd",
    "paint": "mspaint",
    "settings": "start ms-settings:",
    "explorer": "explorer",
}


# ==============================
# 🧠 MAIN OPEN FUNCTION
# ==============================

def open_App(app_name: str) -> bool:
    app_name = app_name.lower().strip()

    if app_name not in APP_MAP:
        print(f"[SECURITY] Blocked unknown app request: {app_name}")
        return False

    command = APP_MAP[app_name]

    # Try Method 1: Direct system execution
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"[SUCCESS] Opened {app_name} using subprocess.")
        return True

    except Exception:
        print(f"[WARNING] Subprocess failed. Trying GUI fallback...")

        # Try Method 2: Windows search fallback
        try:
            gui.press("win")
            time.sleep(0.7)

            gui.write(app_name, interval=0.05)
            time.sleep(0.7)

            gui.press("enter")

            print(f"[SUCCESS] Opened {app_name} using GUI fallback.")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to open {app_name}: {e}")
            return False
