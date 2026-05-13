import time
import logging

logging.getLogger('selenium').setLevel(logging.WARNING)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    _HAS_SELENIUM = True
except Exception:
    webdriver = None
    By = None
    Options = None
    WebDriverWait = None
    EC = None
    ChromeDriverManager = None
    Service = None
    _HAS_SELENIUM = False

_driver = None

def _get_driver():
    global _driver
    if not _HAS_SELENIUM:
        return None
    if _driver is None:
        chromo_options = Options()
        chromo_options.add_argument("--headless")
        chromo_options.add_argument("--disable-blink-features=AutomationControlled")
        chromo_service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=chromo_service, options=chromo_options)
    return _driver


def get_internet_speed():
    if not _HAS_SELENIUM:
        print("[Speed] selenium not available; skipping internet speed check.")
        return None
    try:
        driver = _get_driver()
        if driver is None:
            return None
        driver.get("https://fast.com/")
        time.sleep(11)
        WebDriverWait(driver,60).until(EC.presence_of_all_elements_located((By.ID,'speed-value')))
        speed_value = driver.find_element(By.ID,'speed-value')
        speed_value = speed_value.text
        return speed_value
    except Exception as e:
        print(e)
