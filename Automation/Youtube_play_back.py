import pyautogui
import time

# ==============================
#        AUTOMATION FUNCTIONS
# ==============================

# --- Basic Controls ---
def play_pause():
    pyautogui.press('space')

def mute_unmute():
    pyautogui.press('m')

def full_screen():
    pyautogui.press('f')

def theater_mode():
    pyautogui.press('t')

def mini_player():
    pyautogui.press('i')

def captions_toggle():
    pyautogui.press('c')

# --- Skip Controls ---
def forward_5_sec():
    pyautogui.press('right')

def backward_5_sec():
    pyautogui.press('left')

def forward_10_sec():
    pyautogui.press('l')

def backward_10_sec():
    pyautogui.press('j')

# --- Volume Controls ---
def volume_up():
    pyautogui.press('up')

def volume_down():
    pyautogui.press('down')

# --- Speed Controls ---
def increase_speed():
    pyautogui.hotkey('shift', '>')

def decrease_speed():
    pyautogui.hotkey('shift', '<')

# --- Navigation ---
def next_video():
    pyautogui.hotkey('shift', 'n')

def previous_video():
    pyautogui.hotkey('shift', 'p')

# --- Jump to Percentage ---
def jump_to_percent(number):
    pyautogui.press(str(number))

# --- Search YouTube ---
def search_youtube(query):
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(1)
    pyautogui.write("https://www.youtube.com")
    pyautogui.press('enter')
    time.sleep(3)

    pyautogui.press('/')
    time.sleep(1)
    pyautogui.write(query)
    pyautogui.press('enter')


# ==============================
#        COMMAND HANDLER
# ==============================

def handle_youtube_command(text):
    text = text.lower()

    # ----- BASIC CONTROLS -----
    if "play video" in text or "pause video" in text or "play pause" in text:
        play_pause()

    elif "mute" in text or "unmute" in text:
        mute_unmute()

    elif "full screen" in text:
        full_screen()

    elif "theater mode" in text:
        theater_mode()

    elif "mini player" in text:
        mini_player()

    elif "captions" in text or "subtitles" in text:
        captions_toggle()

    # ----- SKIP -----
    elif "forward 5" in text:
        forward_5_sec()

    elif "backward 5" in text:
        backward_5_sec()

    elif "forward 10" in text:
        forward_10_sec()

    elif "backward 10" in text:
        backward_10_sec()

    # ----- VOLUME -----
    elif "volume up" in text:
        volume_up()

    elif "volume down" in text:
        volume_down()

    # ----- SPEED -----
    elif "increase speed" in text or "speed up" in text:
        increase_speed()

    elif "decrease speed" in text or "slow down" in text:
        decrease_speed()

    # ----- NAVIGATION -----
    elif "next video" in text:
        next_video()

    elif "previous video" in text:
        previous_video()

    # ----- JUMP TO PERCENT -----
    elif "0 percent" in text:
        jump_to_percent(0)

    elif "10 percent" in text:
        jump_to_percent(1)

    elif "20 percent" in text:
        jump_to_percent(2)

    elif "30 percent" in text:
        jump_to_percent(3)

    elif "40 percent" in text:
        jump_to_percent(4)

    elif "50 percent" in text:
        jump_to_percent(5)

    elif "60 percent" in text:
        jump_to_percent(6)

    elif "70 percent" in text:
        jump_to_percent(7)

    elif "80 percent" in text:
        jump_to_percent(8)

    elif "90 percent" in text:
        jump_to_percent(9)

    # ----- SEARCH -----
    elif "search youtube" in text:
        query = text.replace("search youtube", "").strip()
        if query:
            search_youtube(query)
        else:
            print("Please provide search query")

    else:
        pass
