from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from os import getcwd
import time
import threading

# Setting up Chrome options with specific arguments
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--headless=new")

# Setting up the Chrome driver with WebDriverManager and options
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Creating the URL for the website using the current working directory
website = "https://allorizenproject1.netlify.app/"

# Opening the website in the Chrome browser
driver.get(website)

Recog_File = f"{getcwd()}\\input.txt"


def listen():
    print("🎤 Vivie STT Ready...")

    try:
        start_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'startButton'))
        )

        start_button.click()
        print("🎧 Listening...")

        last_text = ""

        while True:
            output_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'output'))
            )

            current_text = output_element.text.strip()

            if current_text and current_text != last_text:
                last_text = current_text
                print("User:", current_text)

                return current_text.lower()   # ✅ IMPORTANT

            time.sleep(0.2)

    except Exception as e:
        print("[STT Error]:", e)
        return None

