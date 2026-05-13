import os
import time

try:
    from winotify import Notification, audio
    _HAS_WINOTIFY = True
except Exception:
    Notification = None
    audio = None
    _HAS_WINOTIFY = False

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Expected repo layout: logo.png lives at the project root.
_ICON_PATH = os.path.join(_BASE_DIR, "logo.png")

def Alert(Text):
    if not _HAS_WINOTIFY or os.name != "nt":
        print(Text)
        return

    icon_path = _ICON_PATH if os.path.exists(_ICON_PATH) else None
    toast = Notification(
        app_id="Vivie",
        title=Text,
        duration="long",
        icon=icon_path,
    )
    time.sleep(1)

    toast.set_audio(audio.Default, loop=False)

    toast.add_actions(label="Click me", launch="https://www.google.com")
    toast.add_actions(label="Dismiss", launch="https://www.google.com")

    toast.show()
