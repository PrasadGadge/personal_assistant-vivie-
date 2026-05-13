import time
import random
import webbrowser
from urllib.parse import quote_plus

try:
    import pywhatkit as kt
    _HAS_PYWHATKIT = True
except Exception:
    kt = None
    _HAS_PYWHATKIT = False
from DATA.DLG_Data import playsong, playing_dlg
from TextToSpeech.Fast_DF_TTS import speak


def play_music_on_youtube(text):
    playdlg = random.choice(playsong)
    speak(playdlg,3)
    if _HAS_PYWHATKIT:
        kt.playonyt(text)
    else:
        url = f"https://www.youtube.com/results?search_query={quote_plus(text)}"
        webbrowser.open(url)
    time.sleep(3)
    playdlg =random.choice(playing_dlg)
    speak(playdlg+text,3)
