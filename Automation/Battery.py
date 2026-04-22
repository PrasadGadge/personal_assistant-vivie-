# pip install psutil

import psutil
import time
from TextToSpeech.Fast_DF_TTS import speak
import threading
from Features.Alert import Alert


battery = psutil.sensors_battery()

import random

BATTERY_GOOD_LINES = [
    "Everything looks stable, Boss.",
    "No worries, Sir.",
    "Battery health is looking good.",
    "We’re in a safe zone.",
]

BATTERY_MEDIUM_LINES = [
    "We still have decent power left.",
    "No immediate concern, Boss.",
    "Battery is holding fine.",
    "We’re doing okay for now.",
]

BATTERY_LOW_LINES = [
    "You may want to keep the charger nearby.",
    "It’s getting a little low, Boss.",
    "Charging soon would be wise.",
    "Battery is dropping steadily.",
]

BATTERY_CRITICAL_LINES = [
    "Boss, we really need to charge soon.",
    "Sir, this is critical now.",
    "Power is extremely low.",
    "Please connect the charger immediately.",
]

def battery_Alert():
    while True:
        time.sleep(3)
        percentage = int(battery.percent)

        if percentage == 100:
            t1 = threading.Thread(target=Alert, args=("Battery Fully Charged",))
            t2 = threading.Thread(
                target=speak,
                args=("Boss, your laptop is fully charged now. You can unplug it whenever you're ready.",)
            )
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        elif percentage <= 5:
            t1 = threading.Thread(target=Alert, args=("Critical Battery Level",))
            t2 = threading.Thread(
                target=speak,
                args=("Boss, this is critical. The battery is extremely low. Please plug in the charger immediately to avoid shutdown.",)
            )
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        elif percentage <= 10:
            t1 = threading.Thread(target=Alert, args=("Battery Very Low",))
            t2 = threading.Thread(
                target=speak,
                args=("Boss, we are running on very low battery. It’s around ten percent. I strongly suggest connecting the charger now.",)
            )
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        elif percentage <= 20:
            t1 = threading.Thread(target=Alert, args=("Battery Low",))
            t2 = threading.Thread(
                target=speak,
                args=("Boss, the battery is getting low. It’s around twenty percent now. Please consider charging soon.",)
            )
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        time.sleep(30)


def check_plug():
    print("Monitoring charging status...")
    battery = psutil.sensors_battery()
    previous_state = battery.power_plugged

    while True:
        battery = psutil.sensors_battery()

        if battery.power_plugged != previous_state:

            if battery.power_plugged:
                t1 = threading.Thread(target=Alert, args=("Charging Started",))
                t2 = threading.Thread(
                    target=speak,
                    args=("Boss, charging has started.",)
                )
            else:
                t1 = threading.Thread(target=Alert, args=("Charging Stopped",))
                t2 = threading.Thread(
                    target=speak,
                    args=("Boss, charging has stopped.",)
                )

            t1.start()
            t2.start()
            t1.join()
            t2.join()

            previous_state = battery.power_plugged

        time.sleep(2)


def check_percentage():
    battery = psutil.sensors_battery()
    percent = int(battery.percent)

    # Select follow-up tone
    if percent >= 70:
        follow_line = random.choice(BATTERY_GOOD_LINES)

    elif 40 <= percent < 70:
        follow_line = random.choice(BATTERY_MEDIUM_LINES)

    elif 20 <= percent < 40:
        follow_line = random.choice(BATTERY_LOW_LINES)

    else:
        follow_line = random.choice(BATTERY_CRITICAL_LINES)

    # Combine into ONE natural sentence
    final_message = f"Boss, the device is currently at {percent} percent battery. {follow_line}"

    speak(final_message)