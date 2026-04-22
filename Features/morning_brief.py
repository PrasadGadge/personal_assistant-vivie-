from Features.weather_system import speak_weather
from Features.check_internet_speed import get_internet_speed
from Features.web_search import search_web
from TextToSpeech.Fast_DF_TTS import speak


def morning_brief():

    speak("Good morning boss. Here is your daily briefing.")

    # Weather
    speak_weather()

    # Internet speed
    speed = get_internet_speed()
    speak(f"Your internet speed is {speed} megabits per second.")

    # News
    results = search_web("latest world news")

    if results:
        headline = results[0]["title"]
        speak(f"Today's top headline: {headline}")