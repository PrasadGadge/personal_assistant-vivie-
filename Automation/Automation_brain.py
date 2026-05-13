# ==========================================
# Automation/Automation_brain.py
# Fixed: music handler replaced input.txt polling
#        with input_queue (NetHyTech STT compatible),
#        play/pause conflict resolved, return values fixed
# ==========================================

from Automation.open_App         import open_App
from Automation.Web_Open         import openweb
from Automation.Play_Music_YT    import play_music_on_youtube
from Automation.Play_Music_SFY   import play_music_on_spotify
from Automation.Battery          import check_percentage
from Automation.tab_automation   import perform_brower_action
from Automation.Youtube_play_back import handle_youtube_command
from Automation.scroll_system    import perform_scroll_action
from Automation.info             import get_info
from TextToSpeech.Fast_DF_TTS    import speak, speak_blocking
from DATA.App_web_data           import APP_NOT_FOUND_LINES, WEBSITE_NOT_FOUND_LINES

import time
import threading
import random
import webbrowser
from urllib.parse import quote_plus

try:
    import pyautogui as gui
    _HAS_PYAUTOGUI = True
except Exception:
    gui = None
    _HAS_PYAUTOGUI = False

try:
    import pywhatkit
    _HAS_PYWHATKIT = True
except Exception:
    pywhatkit = None
    _HAS_PYWHATKIT = False

# ── Import after-play lines safely ───────────────
try:
    from DATA.close_window import YOUTUBE_AFTER_PLAY_LINES, SPOTIFY_AFTER_PLAY_LINES
except ImportError:
    YOUTUBE_AFTER_PLAY_LINES = ["Playing your song Boss."]
    SPOTIFY_AFTER_PLAY_LINES = ["Playing on Spotify Boss."]


# ─────────────────────────────────────────────────
# BASIC CONTROLS
# ─────────────────────────────────────────────────

def play_pause():
    if not _HAS_PYAUTOGUI:
        print("[Automation] pyautogui not available; skipping play/pause.")
        return
    gui.press("space")

def close_window():
    if not _HAS_PYAUTOGUI:
        print("[Automation] pyautogui not available; skipping close window.")
        return
    gui.hotkey('alt', 'f4')

def search_google(text):
    if _HAS_PYWHATKIT:
        pywhatkit.search(text)
        return
    url = f"https://www.google.com/search?q={quote_plus(text)}"
    webbrowser.open(url)

def search(text):
    if not _HAS_PYAUTOGUI:
        print("[Automation] pyautogui not available; skipping in-page search.")
        return
    gui.press("/")
    time.sleep(0.4)
    gui.write(text)
    time.sleep(0.8)
    gui.press("enter")


# ─────────────────────────────────────────────────
# OPEN HANDLER
# ─────────────────────────────────────────────────

def open_brain(text):
    if "website" in text or "open website named" in text:
        name = (text.replace("open website named", "")
                    .replace("open", "")
                    .replace("website", "")
                    .strip())
        try:
            t1 = threading.Thread(target=speak, args=(f"Boss, navigating to {name}.",))
            t2 = threading.Thread(target=openweb, args=(name,))
            t1.start(); t2.start()
            t1.join();  t2.join()
        except Exception:
            speak(random.choice(WEBSITE_NOT_FOUND_LINES))
    else:
        name = text.replace("open", "").replace("app", "").strip()
        try:
            t1 = threading.Thread(target=speak, args=(f"Boss, launching {name}.",))
            t2 = threading.Thread(target=open_App, args=(name,))
            t1.start(); t2.start()
            t1.join();  t2.join()
        except Exception:
            speak(random.choice(APP_NOT_FOUND_LINES))


# ─────────────────────────────────────────────────
# MUSIC HANDLER
# FIX: replaced input.txt polling loop with input_queue
#      The old version blocked forever reading input.txt —
#      NetHyTech STT puts text in input_queue, not files.
# ─────────────────────────────────────────────────

def _get_song_from_queue(timeout: float = 15.0) -> str:
    """
    Wait for a song name from the STT input_queue.
    Returns the song name or empty string on timeout.
    """
    try:
        from main_brain import input_queue
        song = input_queue.get(timeout=timeout)
        return song.strip() if song else ""
    except Exception:
        return ""


def handle_music_youtube():
    speak_blocking("Which song would you like me to play on YouTube, Boss?")
    song = _get_song_from_queue(timeout=15)
    if song:
        play_music_on_youtube(song)
        speak(random.choice(YOUTUBE_AFTER_PLAY_LINES))
    else:
        speak("Sorry Boss, I didn't catch the song name.")


def handle_music_spotify():
    speak_blocking("Please tell me the song name for Spotify, Boss.")
    song = _get_song_from_queue(timeout=15)
    if song:
        play_music_on_spotify(song)
        speak(random.choice(SPOTIFY_AFTER_PLAY_LINES))
    else:
        speak("Sorry Boss, I didn't catch the song name.")


# ─────────────────────────────────────────────────
# MAIN AUTOMATION BRAIN
# ─────────────────────────────────────────────────

def Auto_main_brain(text: str) -> bool:
    """
    Handle automation commands.
    Returns True if handled (brain_loop should not process further),
    Returns False if not an automation command.
    """
    try:
        t = text.lower().strip()

        # OPEN
        if t.startswith("open"):
            open_brain(t)
            return True

        # CLOSE
        if "close" in t and any(w in t for w in ["window", "that site", "this", "tab"]):
            close_window()
            speak("Boss, closing the window.")
            return True

        # YOUTUBE MUSIC — check BEFORE generic "play" check
        if "play music on youtube" in t or ("play music" in t and "spotify" not in t):
            threading.Thread(target=handle_music_youtube, daemon=True).start()
            return True

        # SPOTIFY MUSIC
        if "play some music" in t or "play music on spotify" in t or "play on spotify" in t:
            threading.Thread(target=handle_music_spotify, daemon=True).start()
            return True

        # BATTERY
        if any(w in t for w in ["check battery", "battery percentage", "battery status"]):
            check_percentage()
            return True

        # PAGE SEARCH — only trigger for in-browser search, NOT for news/research queries
        # news/latest/today go to main_brain web_search handler
        page_search_blocklist = ["news", "latest", "today", "weather",
                                  "google", "research", "about", "what",
                                  "current", "find", "tell", "explain"]
        if (t.startswith("search") and
                "google" not in t and
                not any(w in t for w in page_search_blocklist)):
            query = t.replace("search", "").strip()
            speak(f"Boss, searching for {query} on this page.")
            search(query)
            time.sleep(0.5)
            if _HAS_PYAUTOGUI:
                gui.press("enter")
            return True

        # GOOGLE SEARCH
        if "search in google" in t:
            query = t.replace("search in google", "").strip()
            speak(f"Boss, searching Google for {query}.")
            search_google(query)
            return True

        # BROWSER ACTIONS — scroll, tab, back, forward, refresh
        if any(k in t for k in ["scroll up", "scroll down", "page up", "page down"]):
            perform_scroll_action(t)
            return True

        if any(k in t for k in ["new tab", "close tab", "next tab", "previous tab",
                                  "go back", "go forward", "refresh"]):
            perform_brower_action(t)
            return True

        # YOUTUBE PLAYBACK CONTROL
        if any(k in t for k in ["pause video", "resume video", "skip video",
                                  "next video", "previous video"]):
            handle_youtube_command(t)
            return True

        # SYSTEM INFO
        if any(k in t for k in ["cpu usage", "ram usage", "disk usage",
                                  "memory usage", "system info"]):
            get_info(t)
            return True

        # PLAY/PAUSE — generic media control
        # NOTE: checked LAST to avoid catching "play music" commands
        if t in ["play", "pause", "stop media"]:
            play_pause()
            return True

        return False

    except Exception as e:
        print(f"[Automation Error]: {e}")
        return False
