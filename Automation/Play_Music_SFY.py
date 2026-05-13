import webbrowser
import time
from urllib.parse import quote


def play_music_on_spotify(song_name: str):
    """
    Opens Spotify Web and searches + plays the requested song.
    """

    try:
        if not song_name.strip():
            print("No song name provided.")
            return

        # Encode song name safely for URL
        query = quote(song_name)

        # Spotify Web Search URL
        spotify_url = f"https://open.spotify.com/search/{query}"

        # Open in default browser
        webbrowser.open(spotify_url)

        print(f"Opening Spotify and searching for: {song_name}")

        # Small delay for page to load
        time.sleep(5)

        # Optional: Auto press play using keyboard (works if Spotify tab focused)
        import pyautogui as gui
        gui.press("space")

    except Exception as e:
        print(f"Spotify Error: {e}")
