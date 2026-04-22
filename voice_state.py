import threading
import time

# ─────────────────────────────────────────────────
# voice_state.py
#
# WHY Event + Lock, not just Lock:
#
#   threading.Lock held during speech would BLOCK
#   listen_loop from calling is_speaking() until
#   speech finishes — you'd miss interrupts.
#
#   threading.Event allows any thread to CHECK state
#   instantly (non-blocking) while the Lock only
#   guards the tiny moment of flipping the flag.
# ─────────────────────────────────────────────────

# Set when Vivie is speaking, cleared when she stops
_speaking_event = threading.Event()

# Guards the flag flip only — not held during speech
speak_lock = threading.Lock()


def set_speaking(state: bool):
    """Flip speaking state thread-safely."""
    with speak_lock:
        if state:
            _speaking_event.set()
        else:
            _speaking_event.clear()


def is_speaking() -> bool:
    """Non-blocking check — safe to call from any thread."""
    return _speaking_event.is_set()


def wait_until_done(timeout: float = None) -> bool:
    """
    Block caller until speaking stops (or timeout).
    Returns True if speech finished, False if timed out.

    NOTE: threading.Event.wait() waits until SET.
    We need to wait until CLEARED (speech stops),
    so we poll with a short sleep instead.
    """
    deadline = (time.monotonic() + timeout) if timeout else None

    while _speaking_event.is_set():
        if deadline and time.monotonic() >= deadline:
            return False   # timed out
        time.sleep(0.02)

    return True   # speech finished
