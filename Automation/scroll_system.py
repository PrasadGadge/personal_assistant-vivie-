import time

try:
    import pyautogui
    _HAS_PYAUTOGUI = True
except Exception:
    pyautogui = None
    _HAS_PYAUTOGUI = False

def _press(key, presses=1):
    if not _HAS_PYAUTOGUI:
        print("[Scroll] pyautogui not available; skipping key press.")
        return
    pyautogui.press(key, presses=presses)

def _hotkey(*keys):
    if not _HAS_PYAUTOGUI:
        print("[Scroll] pyautogui not available; skipping hotkey.")
        return
    pyautogui.hotkey(*keys)

def _scroll(amount):
    if not _HAS_PYAUTOGUI:
        print("[Scroll] pyautogui not available; skipping scroll.")
        return
    pyautogui.scroll(amount)


# Scroll up (smooth mouse scroll)
def scroll_up():
    _press("up", presses=5)


# Scroll down (smooth mouse scroll)
def scroll_down():
    _scroll(-800)


# Scroll to top of page
def scroll_to_top():
    _hotkey('home')


# Scroll to bottom of page
def scroll_to_bottom():
    _hotkey('end')

def perform_scroll_action(text):
    if "scroll up" in text or "upar scroll karo" in text or "upar karo" in text:
        scroll_up()

    elif "scroll down" in text or "neeche scroll karo" in text or "neeche karo" in text:
        scroll_down()

    elif "scroll to top" in text or "shuruat par jao" in text or "start with starting" in text:
        scroll_to_top()

    elif "scroll to bottom" in text or "ant par jao" in text:
        scroll_to_bottom()

    else:
        pass
