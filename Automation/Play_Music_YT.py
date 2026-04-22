import time
import pywhatkit as kt
import random
from DATA.DLG_Data import playsong, playing_dlg
from TextToSpeech.Fast_DF_TTS import speak


def play_music_on_youtube(text):
    playdlg = random.choice(playsong)
    speak(playdlg,3)
    kt.playonyt(text)
    time.sleep(3)
    playdlg =random.choice(playing_dlg)
    speak(playdlg+text,3)

