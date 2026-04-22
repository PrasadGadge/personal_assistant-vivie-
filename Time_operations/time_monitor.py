import os
import time
import threading
from Features.Alert import Alert
from TextToSpeech.Fast_DF_TTS import speak
from Time_operations.time_managar import input_manage,input_manage_Alam,parse_input_Alarm,parse_input
from os import getcwd


def load_schedule(file_path):
    schedule = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if '=' in line:
                    line_time, activity = line.strip().split(' = ')
                    schedule[line_time.strip()] = activity.strip()
    except Exception as e:
        print(f"Error loading schedule: {e}")
    return schedule

def check_schedule(file_path):
    last_modified = 0
    while True:
        current_time = time.strftime("%I:%M%p")
        try:
            # Check file modification time
            modified = os.path.getmtime(file_path)
            if modified != last_modified:
                last_modified = modified
                schedule = load_schedule(file_path)

            if current_time in schedule:
                text = schedule[current_time]
                t1 = threading.Thread(target=Alert, args=(text,))
                t2 = threading.Thread(target=speak, args=(text,))
                t1.start()
                t2.start()
                t1.join()
                t2.join()

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(60)



def load_Alam_Time(file_path):
    schedule = {}
    try:
        with open(file_path, 'r') as file:
            schedule= file.read()
    except Exception as e:
        print(f"Error loading schedule: {e}")
    return schedule


Alam_path = r"C:\Users\dell\OneDrive\Desktop\Vivie_v1\alarm_data.txt"

def check_Alam(Alam_path):
    last_modified = 0
    while True:
        current_time = time.strftime("%I:%M%p")
        try:
            # Check file modification time
            modified = os.path.getmtime(Alam_path)
            if modified != last_modified:
                last_modified = modified
                schedule = load_Alam_Time(Alam_path)

            if current_time in schedule:
                text = "This is Alarm"
                t1 = threading.Thread(target=Alert, args=(text,))
                t2 = threading.Thread(target=speak, args=(text,))
                t1.start()
                t2.start()
                t1.join()
                t2.join()

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(10)