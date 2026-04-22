import requests
import threading
import time
import random
from TextToSpeech.Fast_DF_TTS import speak


# ============================================
# CONFIGURATION
# ============================================

API_KEY = "7b36d1d4b25a45ddb03195417262302"
CHECK_INTERVAL = 600  # 10 minutes


# ============================================
# GLOBAL MEMORY
# ============================================

weather_cache = {}
user_city = None
last_alert_type = None
system_started = False


# ============================================
# WEATHER COMMENT ENGINE (SMART)
# ============================================

def smart_weather_advice(temp, condition, humidity, wind):

    condition = condition.lower()

    advice = []

    # Heat logic
    if temp >= 38:
        advice.append("Extreme heat detected. Avoid direct sun exposure.")
    elif temp >= 33:
        advice.append("Stay hydrated and limit outdoor activity.")

    # Cold logic
    if temp <= 10:
        advice.append("Very cold conditions. Wear layered clothing.")

    # Rain logic
    if "rain" in condition:
        advice.append("Carry an umbrella.")

    # Humidity logic
    if humidity >= 75:
        advice.append("High humidity may cause fatigue.")

    # Wind logic
    if wind >= 30:
        advice.append("Strong winds detected. Be cautious outdoors.")

    if not advice:
        advice.append("Weather conditions are stable.")

    return " ".join(advice)


# ============================================
# LOCATION DETECTION
# ============================================

def detect_city():

    global user_city

    try:
        response = requests.get("http://ip-api.com/json", timeout=5)
        data = response.json()
        user_city = data.get("city")
        return user_city
    except:
        return None


# ============================================
# WEATHER FETCH ENGINE (FORECAST + AQI)
# ============================================

def fetch_weather(city):

    global weather_cache

    try:
        city = city.strip()

        url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days=3&aqi=yes"

        response = requests.get(url, timeout=20)
        data = response.json()

        if "error" in data:
            print("API Error:", data["error"]["message"])
            return None

        current = data["current"]

        weather_cache = {
            "city": data["location"]["name"],
            "temp": int(current["temp_c"]),
            "condition": current["condition"]["text"],
            "humidity": current["humidity"],
            "wind": current["wind_kph"],
            "aqi": current["air_quality"]["us-epa-index"],
            "forecast": data["forecast"]["forecastday"],
            "last_update": time.time()
        }

        return weather_cache

    except Exception as e:
        print("Weather Fetch Error:", e)
        return None


# ============================================
# SPEAK WEATHER REPORT (ADVANCED)
# ============================================

def speak_weather(city=None):

    global user_city

    try:
        if city:
            result = fetch_weather(city)
        else:
            if not user_city:
                detect_city()
            result = fetch_weather(user_city)

        if not result:
            speak("Boss, weather data unavailable.")
            return

        city_name = result["city"]
        temp = result["temp"]
        condition = result["condition"]
        humidity = result["humidity"]
        wind = result["wind"]
        aqi = result["aqi"]

        advice = smart_weather_advice(temp, condition, humidity, wind)

        report = (
            f"Boss, current temperature in {city_name} is {temp} degree Celsius "
            f"with {condition}. Humidity is {humidity} percent and wind speed "
            f"is {wind} kilometers per hour. Air quality index level is {aqi}. "
            f"{advice}"
        )

        print(report)
        speak(report)

    except Exception as e:
        print("Speak Weather Error:", e)
        speak("Boss, weather system failure.")


# ============================================
# FORECAST SUMMARY
# ============================================

def speak_forecast():

    if not weather_cache:
        speak("Forecast data not available.")
        return

    forecast_days = weather_cache["forecast"]

    summary = "Here is the 3 day forecast. "

    for day in forecast_days:
        date = day["date"]
        max_temp = int(day["day"]["maxtemp_c"])
        min_temp = int(day["day"]["mintemp_c"])
        condition = day["day"]["condition"]["text"]

        summary += (
            f"On {date}, maximum {max_temp} and minimum {min_temp} degree Celsius "
            f"with {condition}. "
        )

    print(summary)
    speak(summary)


# ============================================
# ALERT ENGINE (INTELLIGENT)
# ============================================

def check_alerts():

    global last_alert_type

    if not weather_cache:
        return

    temp = weather_cache["temp"]
    condition = weather_cache["condition"].lower()
    aqi = weather_cache["aqi"]

    if "rain" in condition and last_alert_type != "rain":
        speak("Rain alert detected.")
        last_alert_type = "rain"

    elif temp >= 42 and last_alert_type != "heatwave":
        speak("Heatwave level temperature detected.")
        last_alert_type = "heatwave"

    elif aqi >= 4 and last_alert_type != "pollution":
        speak("Air quality is unhealthy. Consider wearing a mask.")
        last_alert_type = "pollution"


# ============================================
# BACKGROUND LOOP
# ============================================

def weather_background_loop():

    global user_city

    while True:
        try:
            if not user_city:
                detect_city()

            if user_city:
                result = fetch_weather(user_city)
                if result:
                    check_alerts()

        except:
            pass

        time.sleep(CHECK_INTERVAL)


# ============================================
# START SYSTEM
# ============================================

def start_weather_system():

    global system_started

    if system_started:
        return

    system_started = True

    thread = threading.Thread(target=weather_background_loop)
    thread.daemon = True
    thread.start()