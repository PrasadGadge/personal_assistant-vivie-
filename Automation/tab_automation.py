try:
    import pyautogui
    _HAS_PYAUTOGUI = True
except Exception:
    pyautogui = None
    _HAS_PYAUTOGUI = False

def _hotkey(*keys):
    if not _HAS_PYAUTOGUI:
        print("[Browser] pyautogui not available; skipping hotkey action.")
        return
    pyautogui.hotkey(*keys)

def _press(key):
    if not _HAS_PYAUTOGUI:
        print("[Browser] pyautogui not available; skipping key press.")
        return
    pyautogui.press(key)

def _scroll(amount):
    if not _HAS_PYAUTOGUI:
        print("[Browser] pyautogui not available; skipping scroll.")
        return
    pyautogui.scroll(amount)

# ================= TAB CONTROLS =================
def open_new_tab():
    _hotkey('ctrl', 't')

def close_tab():
    _hotkey('ctrl', 'w')

def reopen_closed_tab():
    _hotkey('ctrl', 'shift', 't')

def next_tab():
    _hotkey('ctrl', 'tab')

def previous_tab():
    _hotkey('ctrl', 'shift', 'tab')

def go_to_tab_1():
    _hotkey('ctrl', '1')

def go_to_tab_2():
    _hotkey('ctrl', '2')

def go_to_tab_3():
    _hotkey('ctrl', '3')

def go_to_last_tab():
    _hotkey('ctrl', '9')


# ================= NAVIGATION =================
def refresh_page():
    _hotkey('ctrl', 'r')

def hard_refresh():
    _hotkey('ctrl', 'shift', 'r')

def go_back():
    _hotkey('alt', 'left')

def go_forward():
    _hotkey('alt', 'right')

def stop_loading():
    _press('esc')

def focus_address_bar():
    _hotkey('ctrl', 'l')

def find_on_page():
    _hotkey('ctrl', 'f')


# ================= ZOOM =================
def zoom_in():
    _hotkey('ctrl', '+')

def zoom_out():
    _hotkey('ctrl', '-')

def reset_zoom():
    _hotkey('ctrl', '0')


# ================= SCROLL =================
def scroll_down():
    _scroll(-800)

def scroll_up():
    _scroll(800)

def scroll_to_top():
    _hotkey('home')

def scroll_to_bottom():
    _hotkey('end')


# ================= WINDOW =================
def toggle_full_screen():
    _press('f11')

def minimize_window():
    _hotkey('win', 'down')

def maximize_window():
    _hotkey('win', 'up')

def close_window():
    _hotkey('alt', 'f4')

def open_private_window():
    _hotkey('ctrl', 'shift', 'n')


# ================= DEV & TOOLS =================
def open_dev_tools():
    _hotkey('ctrl', 'shift', 'i')

def open_history():
    _hotkey('ctrl', 'h')

def open_downloads():
    _hotkey('ctrl', 'j')

def print_page():
    _hotkey('ctrl', 'p')

def save_page():
    _hotkey('ctrl', 's')


# ================= COMMAND HANDLER =================
def perform_brower_action(text):
    text = text.lower()

    # TAB
    if "open new tab" in text or "new tab kholo" in text or "open tab" in text:
        open_new_tab()

    elif "close tab" in text or "tab band karo" in text or "close the tab":
        close_tab()

    elif "last tab" in text or "close tab window" in text:
        reopen_closed_tab()

    elif "next tab" in text:
        next_tab()

    elif "previous tab" in text:
        previous_tab()

    elif "go to tab 1" in text:
        go_to_tab_1()

    elif "go to tab 2" in text:
        go_to_tab_2()

    elif "go to tab 3" in text:
        go_to_tab_3()

    elif "last tab" in text:
        go_to_last_tab()

    # NAVIGATION
    elif "refresh" in text:
        refresh_page()

    elif "hard refresh" in text:
        hard_refresh()

    elif "go back" in text or "piche jao" in text:
        go_back()

    elif "go forward" in text or "aage jao" in text:
        go_forward()

    elif "stop loading" in text:
        stop_loading()

    elif "address bar" in text:
        focus_address_bar()

    elif "find on page" in text:
        find_on_page()

    # ZOOM
    elif "zoom in" in text:
        zoom_in()

    elif "zoom out" in text:
        zoom_out()

    elif "reset zoom" in text:
        reset_zoom()

    # SCROLL
    elif "scroll down" in text:
        scroll_down()

    elif "scroll up" in text:
        scroll_up()

    elif "top of page" in text:
        scroll_to_top()

    elif "bottom of page" in text:
        scroll_to_bottom()

    # WINDOW
    elif "full screen" in text:
        toggle_full_screen()

    elif "minimize window" in text:
        minimize_window()

    elif "maximize window" in text:
        maximize_window()

    elif "close window" in text:
        close_window()

    elif "private window" in text or "incognito" in text:
        open_private_window()

    # DEV & TOOLS
    elif "developer tools" in text:
        open_dev_tools()

    elif "history" in text:
        open_history()

    elif "downloads" in text:
        open_downloads()

    elif "print page" in text:
        print_page()

    elif "save page" in text:
        save_page()

    else:
        pass
