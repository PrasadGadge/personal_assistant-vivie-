# ==================================================
# Fast_DF_TTS.py — SSML Streaming Version (FIXED)
# ==================================================

import asyncio, io, threading, time, re, tempfile, os

try:
    import edge_tts
    _HAS_EDGE_TTS = True
except Exception:
    edge_tts = None
    _HAS_EDGE_TTS = False
# Import the personality module normally at the top - MUCH faster than importlib
try:
    import voice_personality as vp
except ImportError:
    # Fallback if the file is in a different folder
    from . import voice_personality as vp

_is_playing  = False
_stop_event  = threading.Event()
_loop        = None
_loop_thread = None

def _get_loop():
    global _loop, _loop_thread
    if _loop is None or not _loop.is_running():
        _loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
        _loop_thread.start()
    return _loop

def stop_speaking():
    _stop_event.set()

def _preprocess(text: str) -> str:
    """Clean text before speech — remove markdown and symbols."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    text = re.sub(r'#{1,6}\s',      '',    text)
    text = re.sub(r'`(.*?)`',       r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    replacements = {
        "→": "leads to", "←": "from", "✅": "", "❌": "",
        "•": "", "&": "and", "\n": ". ", "↑": "increased", "↓": "decreased",
    }
    for sym, word in replacements.items():
        text = text.replace(sym, word)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Limit length to prevent API timeouts
    words = text.split()
    if len(words) > 150:
        text = " ".join(words[:150]) + "."
    return text

async def _fetch_audio(ssml_or_text: str, voice: str, rate: str, pitch: str, use_ssml: bool = True) -> bytes:
    """Fetch audio from Edge TTS."""
    buf = io.BytesIO()
    
    # FIX: Strip whitespace to ensure it starts exactly with <speak
    ssml_or_text = ssml_or_text.strip()

    if use_ssml and ssml_or_text.startswith('<speak'):
        # If it's SSML, edge-tts only needs the SSML string and the voice
        communicate = edge_tts.Communicate(ssml_or_text, voice)
    else:
        # Plain text mode
        communicate = edge_tts.Communicate(ssml_or_text, voice, rate=rate, pitch=pitch)

    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
            if _stop_event.is_set():
                return b""
    except Exception as e:
        print(f"[TTS Fetch Error]: {e}")
        return b""

    return buf.getvalue()

def _play_blocking_audio(text: str, intent: str = "chat"):
    """Full pipeline: build SSML → fetch audio → play."""
    global _is_playing
    if not _HAS_EDGE_TTS:
        print("[TTS] edge-tts not available; skipping audio output.")
        return

    # 1. Use the imported vp module to get SSML and params
    ssml = vp.build_ssml(text, intent)
    params = vp.get_voice_params(text, intent)
    
    voice = params["voice"]
    rate = params["rate"]
    pitch = params["pitch"]
    
    # Determine if we are actually using SSML
    use_ssml = (ssml is not None and ssml.startswith('<speak'))
    audio_input = ssml if use_ssml else text

    # 2. Fetch audio via the async loop
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(
        _fetch_audio(audio_input, voice, rate, pitch, use_ssml), loop
    )
    
    try:
        mp3_bytes = future.result(timeout=30)
    except Exception as e:
        print(f"[TTS fetch error] {e}")
        return

    if not mp3_bytes or _stop_event.is_set():
        return

    # 3. Play via playsound
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(mp3_bytes)
            tmp_path = f.name

        _is_playing = True
        _stop_event.clear()

        from playsound import playsound
        # We use a thread for playsound so we can monitor the _stop_event
        play_thread = threading.Thread(target=playsound, args=(tmp_path, True), daemon=True)
        play_thread.start()

        while play_thread.is_alive():
            if _stop_event.is_set():
                # Note: playsound is hard to kill instantly, but we can stop tracking it
                break
            time.sleep(0.05)

        play_thread.join(timeout=1)

    except Exception as e:
        print(f"[TTS play error] {e}")
    finally:
        _is_playing = False
        _stop_event.clear()
        if tmp_path:
            try: os.unlink(tmp_path)
            except Exception: pass

# ==================================================
# PUBLIC API
# ==================================================

def speak(text: str, intent: str = "chat") -> bool:
    """Non-blocking speak."""
    if not text or not text.strip(): return False
    print(f"\n🔊 Vivie: {text}\n")
    clean = _preprocess(text)
    if not clean: return False
    threading.Thread(target=_play_blocking_audio, args=(clean, intent), daemon=True).start()
    return True

def speak_blocking(text: str, intent: str = "chat") -> bool:
    """Blocking speak."""
    if not text or not text.strip(): return False
    print(f"\n🔊 Vivie: {text}\n")
    clean = _preprocess(text)
    if not clean: return False
    _play_blocking_audio(clean, intent)
    return True

def is_speaking() -> bool:
    return _is_playing
