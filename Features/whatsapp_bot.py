import time
import json
import os
from TextToSpeech.Fast_DF_TTS import speak
from os import getcwd

try:
    import pywhatkit as kit
    _HAS_PYWHATKIT = True
except Exception:
    kit = None
    _HAS_PYWHATKIT = False

# ==============================
# 📂 File Paths
# ==============================
base_path = getcwd()
input_file = os.path.join(base_path, "input.txt")
contact_file = os.path.join(base_path, "contacts.json")

# ==============================
# 📥 Load Contacts
# ==============================
def load_contacts():
    try:
        with open(contact_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print("Contact loading error:", e)
        speak("Unable to load contact dataset.")
        return {}

# ==============================
# 🧹 Clear Input File
# ==============================
def clear_file():
    with open(input_file, "w", encoding="utf-8") as file:
        file.truncate(0)

# ==============================
# 🔍 Find Contact
# ==============================
def find_contact(name, contacts):
    name = name.lower().strip()
    for contact_name in contacts:
        if contact_name.lower() in name:
            return contacts[contact_name]
    return None

# ==============================
# 💬 Send WhatsApp Message
# ==============================
def send_whatsapp(contact_number, message):
    try:
        if not _HAS_PYWHATKIT:
            speak("WhatsApp integration is unavailable right now.")
            print("pywhatkit not available; skipping WhatsApp send.")
            return
        speak("Sending message now.")

        # Small delay for system stability
        time.sleep(2)

        kit.sendwhatmsg_instantly(
            contact_number,
            message,
            wait_time=25,      # Give WhatsApp enough time to load
            tab_close=True,
            close_time=5
        )

        speak("Message sent successfully.")
        print("Message sent to:", contact_number)

    except Exception as e:
        print("Sending failed:", e)
        speak("Failed to send message.")

# ==============================
# 🚀 Main Function
# ==============================
def send_msg():
    contacts = load_contacts()
    if not contacts:
        return

    speak("Who do you want to send the message to?")
    last_text = ""

    while True:
        try:
            with open(input_file, "r", encoding="utf-8") as file:
                current_text = file.read().lower().strip()

            if current_text and current_text != last_text:
                last_text = current_text

                # Step 1: Detect contact command
                if current_text.startswith(("send to", "send tu")):
                    name = current_text.replace("send to", "").replace("send tu", "").strip()

                    contact_number = find_contact(name, contacts)

                    if not contact_number:
                        speak("Contact not found in dataset.")
                        clear_file()
                        continue

                    speak("by the way what is the message, Boss ?")

                # Step 2: Detect message
                elif current_text.startswith("message is"):
                    message = current_text.replace("message is", "").strip()

                    if message:
                        send_whatsapp(contact_number, message)
                        clear_file()
                        break  # Exit safely after sending

            time.sleep(0.5)

        except Exception as e:
            print("Runtime error:", e)
            time.sleep(1)
