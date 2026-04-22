import pyautogui

# ================= TAB CONTROLS =================
def open_new_tab():
    pyautogui.hotkey('ctrl', 't')

def close_tab():
    pyautogui.hotkey('ctrl', 'w')

def reopen_closed_tab():
    pyautogui.hotkey('ctrl', 'shift', 't')

def next_tab():
    pyautogui.hotkey('ctrl', 'tab')

def previous_tab():
    pyautogui.hotkey('ctrl', 'shift', 'tab')

def go_to_tab_1():
    pyautogui.hotkey('ctrl', '1')

def go_to_tab_2():
    pyautogui.hotkey('ctrl', '2')

def go_to_tab_3():
    pyautogui.hotkey('ctrl', '3')

def go_to_last_tab():
    pyautogui.hotkey('ctrl', '9')


# ================= NAVIGATION =================
def refresh_page():
    pyautogui.hotkey('ctrl', 'r')

def hard_refresh():
    pyautogui.hotkey('ctrl', 'shift', 'r')

def go_back():
    pyautogui.hotkey('alt', 'left')

def go_forward():
    pyautogui.hotkey('alt', 'right')

def stop_loading():
    pyautogui.press('esc')

def focus_address_bar():
    pyautogui.hotkey('ctrl', 'l')

def find_on_page():
    pyautogui.hotkey('ctrl', 'f')


# ================= ZOOM =================
def zoom_in():
    pyautogui.hotkey('ctrl', '+')

def zoom_out():
    pyautogui.hotkey('ctrl', '-')

def reset_zoom():
    pyautogui.hotkey('ctrl', '0')


# ================= SCROLL =================
def scroll_down():
    pyautogui.scroll(-800)

def scroll_up():
    pyautogui.scroll(800)

def scroll_to_top():
    pyautogui.hotkey('home')

def scroll_to_bottom():
    pyautogui.hotkey('end')


# ================= WINDOW =================
def toggle_full_screen():
    pyautogui.press('f11')

def minimize_window():
    pyautogui.hotkey('win', 'down')

def maximize_window():
    pyautogui.hotkey('win', 'up')

def close_window():
    pyautogui.hotkey('alt', 'f4')

def open_private_window():
    pyautogui.hotkey('ctrl', 'shift', 'n')


# ================= DEV & TOOLS =================
def open_dev_tools():
    pyautogui.hotkey('ctrl', 'shift', 'i')

def open_history():
    pyautogui.hotkey('ctrl', 'h')

def open_downloads():
    pyautogui.hotkey('ctrl', 'j')

def print_page():
    pyautogui.hotkey('ctrl', 'p')

def save_page():
    pyautogui.hotkey('ctrl', 's')


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

