import time
import threading
from os import getcwd

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    _HAS_SELENIUM = True
except Exception:
    webdriver = None
    By = None
    WebDriverWait = None
    EC = None
    Service = None
    ChromeDriverManager = None
    _HAS_SELENIUM = False

_driver = None
_driver_lock = threading.Lock()
_WEBSITE = "https://allorizenproject1.netlify.app/"
Recog_File = f"{getcwd()}\\input.txt"


def _get_driver():
    if not _HAS_SELENIUM:
        return None
    global _driver
    with _driver_lock:
        if _driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--use-fake-ui-for-media-stream")
            chrome_options.add_argument("--headless=new")
            _driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options,
            )
            _driver.get(_WEBSITE)
        return _driver


def listen():
    if not _HAS_SELENIUM:
        print("[STT] selenium not available; skipping web STT.")
        return None

    driver = _get_driver()
    if driver is None:
        return None

    print("🎤 Vivie STT Ready...")

    try:
        start_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "startButton"))
        )

        start_button.click()
        print("🎧 Listening...")

        last_text = ""

        while True:
            output_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "output"))
            )

            current_text = output_element.text.strip()

            if current_text and current_text != last_text:
                last_text = current_text
                print("User:", current_text)

                return current_text.lower()

            time.sleep(0.2)

    except Exception as e:
        print("[STT Error]:", e)
        return None
