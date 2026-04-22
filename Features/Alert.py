import os
from winotify import Notification, audio
from os import getcwd
import time

def Alert(Text):
    icon_path = r'C:\Users\dell\OneDrive\Desktop\Vivie_v1\logo.png'

    toast = Notification(
    app_id= "Vivie",
    title=Text,
    duration="long",
    icon=icon_path
    
)
    time.sleep(1)

    toast.set_audio(audio.Default, loop=False)


    toast.add_actions(label="Click me", launch="https://www.google.com")
    toast.add_actions(label="Dismiss", launch="https://www.google.com")


    toast.show()