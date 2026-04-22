import pyautogui
import time


# Scroll up (smooth mouse scroll)
def scroll_up():
    pyautogui.press("up", presses=5)


# Scroll down (smooth mouse scroll)
def scroll_down():
    pyautogui.scroll('down', presses=5)


# Scroll to top of page
def scroll_to_top():
    pyautogui.hotkey('home')


# Scroll to bottom of page
def scroll_to_bottom():
    pyautogui.hotkey('end')

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
