# ==================================================
# SpeechToText/vivie_stt.py
# Echo fix: pauses listening while Vivie speaks
# ==================================================

import os
import time
import threading
from typing import Any, TYPE_CHECKING, Union

if TYPE_CHECKING:
    import numpy as _np
    NDArray = _np.ndarray
else:
    NDArray = Any

AudioArray = Union[NDArray, list]

try:
    import numpy as np
    import sounddevice as sd
    from faster_whisper import WhisperModel
    _HAS_AUDIO_STT = True
except Exception:
    np = None
    sd = None
    WhisperModel = None
    _HAS_AUDIO_STT = False

_warned_missing_deps = False

SAMPLE_RATE       = 16000
CHANNELS          = 1
SILENCE_THRESHOLD = 300
SILENCE_DURATION  = 1.5
MAX_RECORD_TIME   = 12

WAKE_WORDS = [
    "vivie", "vivi", "vivian", "ivy",
    "hey vivie", "ok vivie", "yo vivie",
    "vibe", "viv", "bibi", "biwi","hello","wake up vivie","vivie wake up","wake up","boss is here","vivie are you there","are you listening"
]

STRIP_WORDS = [
    "hey vivie", "ok vivie", "yo vivie",
    "vivie", "vivi", "vivian", "ivy",
    "bibi", "biwi", "hey ", "ok ", "yo "
]

_model      = None
_model_lock = threading.Lock()


def _get_model() -> WhisperModel:
    global _model
    with _model_lock:
        if _model is None:
            print("[STT] Loading Whisper model...")
            _model = WhisperModel("base", device="cpu",
                                  compute_type="int8", num_workers=2)
            print("[STT] Whisper ready.")
    return _model


def _energy(audio: AudioArray) -> float:
    if not _HAS_AUDIO_STT or np is None:
        return 0.0
    return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))


def _is_vivie_speaking() -> bool:
    """
    Check if Vivie is currently playing audio.
    Prevents echo — mic is paused while speaker is active.
    """
    try:
        from voice_state import is_speaking
        return is_speaking()
    except Exception:
        return False


def _record() -> AudioArray:
    if not _HAS_AUDIO_STT or sd is None or np is None:
        return []
    chunk_size     = int(SAMPLE_RATE * 0.5)
    silence_chunks = 0
    silence_needed = int(SILENCE_DURATION / 0.5)
    max_chunks     = int(MAX_RECORD_TIME / 0.5)
    chunks         = []

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype='int16') as stream:
        for _ in range(max_chunks):
            # Stop recording if Vivie starts speaking mid-sentence
            if _is_vivie_speaking():
                break
            data, _ = stream.read(chunk_size)
            flat    = data.flatten()
            chunks.append(flat)
            if _energy(flat) < SILENCE_THRESHOLD:
                silence_chunks += 1
                if silence_chunks >= silence_needed and len(chunks) > 4:
                    break
            else:
                silence_chunks = 0

    return np.concatenate(chunks) if chunks else np.array([], dtype=np.int16)


def _transcribe(audio: AudioArray) -> str:
    if not _HAS_AUDIO_STT or WhisperModel is None or np is None:
        return ""
    if len(audio) < SAMPLE_RATE * 0.3:
        return ""
    try:
        audio_float = audio.astype(np.float32) / 32768.0
        segments, _ = _get_model().transcribe(
            audio_float,
            language                   = "en",
            beam_size                  = 3,
            vad_filter                 = True,
            condition_on_previous_text = False
        )
        return " ".join(s.text.strip() for s in segments).strip()
    except Exception as e:
        print(f"[STT] Transcribe error: {e}")
        return ""


def _has_wake_word(text: str) -> bool:
    t = text.lower().strip()
    if any(w in t for w in WAKE_WORDS):
        return True
    words = t.split()
    if words and (words[0].startswith("viv") or words[0] in ["ivy", "vibe"]):
        return True
    return False


def _strip_wake_word(text: str) -> str:
    t  = text.strip()
    tl = t.lower()
    for w in STRIP_WORDS:
        if tl.startswith(w):
            t  = t[len(w):].strip()
            tl = t.lower()
    return (t[0].upper() + t[1:]) if t else ""


def listen() -> str:
    """
    Listen for ONE wake word + command. Returns clean text string.
    Automatically pauses while Vivie is speaking (echo prevention).
    Called in a while True loop by listen_loop() in main_brain.py.
    """
    global _warned_missing_deps
    if not _HAS_AUDIO_STT:
        if not _warned_missing_deps:
            print("[STT] Audio dependencies not available; skipping microphone input.")
            _warned_missing_deps = True
        time.sleep(0.5)
        return ""
    print("🎤 Vivie STT Ready...")
    chunk_samples = int(SAMPLE_RATE * 1.5)

    # Phase 1: Wait for wake word
    while True:
        try:
            # KEY FIX: Skip entirely while Vivie is speaking
            # This prevents her voice from being picked up as a wake word
            if _is_vivie_speaking():
                time.sleep(0.1)
                continue

            # Extra buffer: wait 0.8s after she stops speaking
            # (playsound has ~200ms tail, this gives full clearance)
            if not _is_vivie_speaking():
                # Check energy before transcribing — saves CPU
                with sd.InputStream(samplerate=SAMPLE_RATE,
                                    channels=CHANNELS, dtype='int16') as stream:
                    data, _ = stream.read(chunk_samples)
                    flat    = data.flatten()

                if _energy(flat) < SILENCE_THRESHOLD * 0.7:
                    continue

                # Still not speaking? OK to transcribe
                if _is_vivie_speaking():
                    continue

                text = _transcribe(flat)
                if not text or not _has_wake_word(text):
                    continue

                print(f"[STT] Wake word: '{text}'")
                break

        except Exception as e:
            print(f"[STT] Wake error: {e}")
            time.sleep(0.5)

    # Phase 2: Record command
    print("🎧 Listening...")
    try:
        # Small pause to let user start speaking after wake word
        time.sleep(0.15)
        audio = _record()
        if len(audio) == 0:
            return ""

        full_text = _transcribe(audio)
        if not full_text:
            return ""

        clean = _strip_wake_word(full_text)
        if clean and len(clean) > 1:
            print(f"User: {clean}")
            return clean.lower()

        return ""

    except Exception as e:
        print(f"[STT] Command error: {e}")
        return ""
