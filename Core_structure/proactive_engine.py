# ==================================================
# proactive_engine.py — Vivie Proactive Engine
# Fixed: overlapping speech, PyQt UI calls,
#        duplicate reminder firing, loop backoff
# ==================================================

import threading
import time
import datetime
import os
import json

from Features.web_search      import search_web
from Features.morning_brief   import morning_brief
from TextToSpeech.Fast_DF_TTS import speak_blocking   # FIX: blocking speak
from voice_state              import set_speaking, is_speaking


# ─────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────

CHECK_INTERVAL    = 30 * 60   # seconds between full check cycles
MORNING_HOUR      = 8
MORNING_MINUTE    = 0
BATTERY_THRESHOLD = 20
MAX_LOOP_ERRORS   = 5         # consecutive errors before long backoff

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR    = os.path.dirname(BASE_DIR)
SCHEDULE_FILE  = os.path.join(PROJECT_DIR, "schedule.txt")
REMINDERS_FILE = os.path.join(PROJECT_DIR, "data", "reminders.json")


# ─────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────

_state = {
    "morning_brief_done":  False,
    "last_news_update":    None,
    "last_check_date":     None,
    "last_run":            None,
    "last_behavior_check": None,
    "last_battery_alert":  None,
}


# ─────────────────────────────────────────────────
# SAFE SPEAK
# FIX: was using non-blocking speak() — voices overlapped.
# Now uses speak_blocking() so each proactive message
# waits to finish before the next check runs.
# Also updates voice_state so main_brain knows we're speaking.
# ─────────────────────────────────────────────────

def _safe_speak(text: str):
    """Speak proactive message and block until done."""
    if not text or not text.strip():
        return
    # Don't interrupt if Vivie is already speaking
    if is_speaking():
        print(f"[ProactiveEngine] Skipping speak — already speaking: {text[:40]}")
        return
    try:
        set_speaking(True)
        speak_blocking(text, intent="suggestion")
    except Exception as e:
        print(f"[ProactiveEngine] Speak error: {e}")
    finally:
        set_speaking(False)


# ─────────────────────────────────────────────────
# UI UPDATE
# FIX: was calling get_ui() (PyQt) — crashes with WebSocket UI.
# Now routes through emit_to_ui WebSocket bridge.
# ─────────────────────────────────────────────────

def _update_ui(text: str):
    """Push a log message to the UI via WebSocket."""
    try:
        from Vivie_UI import emit_to_ui
        now = datetime.datetime.now().strftime("%H:%M:%S")
        emit_to_ui("sig_log", f"[{now}] 💡 {text}")
    except Exception:
        pass   # UI not connected — silent is fine for proactive logs


# ─────────────────────────────────────────────────
# RESET DAILY STATE
# ─────────────────────────────────────────────────

def _reset_daily_state_if_needed():
    today = datetime.date.today().isoformat()
    if _state["last_check_date"] != today:
        _state["morning_brief_done"]  = False
        _state["last_news_update"]    = None
        _state["last_check_date"]     = today
        _state["last_battery_alert"]  = None
        print("[ProactiveEngine] New day — state reset.")


# ─────────────────────────────────────────────────
# CHECK 1 — MORNING BRIEF
# ─────────────────────────────────────────────────

def _check_morning_brief():
    try:
        now = datetime.datetime.now()
        if (now.hour  == MORNING_HOUR and
            now.minute < 35 and
            not _state["morning_brief_done"]):

            print("[ProactiveEngine] Morning brief...")
            _safe_speak("Good morning Boss. Here is your morning brief.")
            morning_brief()
            _state["morning_brief_done"] = True
            _update_ui("Morning brief delivered.")

    except Exception as e:
        print(f"[ProactiveEngine] Morning brief error: {e}")


# ─────────────────────────────────────────────────
# CHECK 2 — NEWS UPDATES
# ─────────────────────────────────────────────────

def _check_news_updates():
    try:
        now  = datetime.datetime.now()
        last = _state["last_news_update"]

        if last and (now - last).total_seconds() / 3600 < 2:
            return

        topics = _get_interest_topics()

        import random
        topic   = random.choice(topics)
        results = search_web(topic)

        if results:
            top   = results[0]
            title = top.get("title", "").split(".")[0]
            if title:
                msg = (
                    f"Boss, here's something you might find interesting. "
                    f"{title}. Want me to tell you more about it?"
                )
                _safe_speak(msg)
                _state["last_news_update"] = now
                _update_ui(f"News: {title[:60]}")

    except Exception as e:
        print(f"[ProactiveEngine] News update error: {e}")


def _get_interest_topics() -> list:
    try:
        from Core_structure.behavior_engine import get_active_hours
        if get_active_hours():
            return [
                "artificial intelligence latest 2026",
                "machine learning research news",
                "Python programming updates 2026",
                "robotics technology news",
                "deep learning breakthroughs",
            ]
    except Exception:
        pass
    return [
        "artificial intelligence latest news",
        "machine learning research 2026",
        "Python programming updates",
    ]


# ─────────────────────────────────────────────────
# CHECK 3 — REMINDERS
# FIX: was firing every loop cycle within 35-min window
# because it only checked time diff, not a "fired" flag.
# Now marks reminders as done immediately on first fire.
# ─────────────────────────────────────────────────

def _load_reminders() -> list:
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_reminders(reminders: list):
    try:
        os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ProactiveEngine] Save reminders error: {e}")


def add_reminder(text: str, remind_time: str) -> bool:
    try:
        reminders = _load_reminders()
        reminders.append({
            "text":       text,
            "time":       remind_time,
            "created_at": datetime.datetime.now().isoformat(),
            "done":       False,
        })
        _save_reminders(reminders)
        print(f"[ProactiveEngine] Reminder added: {text} at {remind_time}")
        return True
    except Exception as e:
        print(f"[ProactiveEngine] Add reminder error: {e}")
        return False


def _check_reminders():
    try:
        reminders = _load_reminders()
        if not reminders:
            return

        now     = datetime.datetime.now()
        updated = False

        for reminder in reminders:
            if reminder.get("done"):
                continue

            remind_time_str = reminder.get("time", "")
            if not remind_time_str:
                continue

            try:
                fmt = "%Y-%m-%d %H:%M" if len(remind_time_str) > 5 else "%Y-%m-%d %H:%M"
                if len(remind_time_str) <= 5:
                    remind_dt = datetime.datetime.strptime(
                        f"{now.date()} {remind_time_str}", "%Y-%m-%d %H:%M"
                    )
                else:
                    remind_dt = datetime.datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M")

                diff = (now - remind_dt).total_seconds()

                # FIX: tighter 5-min window (was 35 min) + mark done immediately
                # so it can never fire twice even if loop runs again within window
                if 0 <= diff <= 300:
                    _safe_speak(f"Boss, reminder: {reminder['text']}.")
                    _update_ui(f"Reminder: {reminder['text']}")
                    reminder["done"] = True   # mark BEFORE save — prevents double fire
                    updated = True
                    print(f"[ProactiveEngine] Reminder fired: {reminder['text']}")

            except ValueError:
                continue

        if updated:
            _save_reminders(reminders)

    except Exception as e:
        print(f"[ProactiveEngine] Reminder check error: {e}")


# ─────────────────────────────────────────────────
# CHECK 4 — SCHEDULE
# ─────────────────────────────────────────────────

def _check_schedule():
    try:
        if not os.path.exists(SCHEDULE_FILE):
            return

        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        now = datetime.datetime.now()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("|")
            if len(parts) < 2:
                continue

            try:
                event_dt     = datetime.datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M")
                event_str    = parts[1].strip()
                diff_minutes = (event_dt - now).total_seconds() / 60

                if 0 <= diff_minutes <= 35:
                    mins = int(diff_minutes)
                    msg  = (
                        f"Boss, {event_str} is starting now."
                        if mins <= 1 else
                        f"Boss, {event_str} is coming up in {mins} minutes."
                    )
                    _safe_speak(msg)
                    _update_ui(f"{event_str} in {mins} min")

            except ValueError:
                continue

    except Exception as e:
        print(f"[ProactiveEngine] Schedule check error: {e}")


# ─────────────────────────────────────────────────
# CHECK 5 — BATTERY ALERT
# ─────────────────────────────────────────────────

def _check_battery():
    try:
        import psutil
        bat = psutil.sensors_battery()
        if not bat:
            return

        pct     = int(bat.percent)
        plugged = bat.power_plugged
        now     = datetime.datetime.now()

        last_alert = _state["last_battery_alert"]
        if last_alert and (now - last_alert).total_seconds() / 3600 < 1:
            return

        if pct <= BATTERY_THRESHOLD and not plugged:
            _safe_speak(f"Boss, battery is at {pct} percent. Please plug in your charger.")
            _state["last_battery_alert"] = now
            _update_ui(f"Battery low: {pct}%")

    except Exception as e:
        print(f"[ProactiveEngine] Battery check error: {e}")


# ─────────────────────────────────────────────────
# CHECK 6 — BEHAVIORAL PATTERNS
# ─────────────────────────────────────────────────

def _check_behavior_patterns():
    try:
        now  = datetime.datetime.now()
        last = _state["last_behavior_check"]

        if last and (now - last).total_seconds() / 3600 < 1:
            return

        from Core_structure.behavior_engine import get_suggestions
        suggestions = get_suggestions(top_k=1)

        if not suggestions:
            return

        best = suggestions[0]
        if best.get("confidence", 0) >= 0.65:
            _safe_speak(f"Boss, {best['message']}")
            _update_ui(best["message"])
            _state["last_behavior_check"] = now

    except Exception as e:
        print(f"[ProactiveEngine] Behavior check error: {e}")


# ─────────────────────────────────────────────────
# MAIN PROACTIVE LOOP
# FIX: exponential backoff on repeated errors so a
# broken check doesn't silently spam logs 48x/day
# ─────────────────────────────────────────────────

def _proactive_loop():
    print("[ProactiveEngine] Background engine started.")
    time.sleep(60)   # let Vivie finish booting

    consecutive_errors = 0

    while True:
        try:
            print("[ProactiveEngine] Running checks...")

            _reset_daily_state_if_needed()

            _check_morning_brief();    time.sleep(2)
            _check_reminders();        time.sleep(2)
            _check_schedule();         time.sleep(2)
            _check_battery();          time.sleep(2)
            _check_behavior_patterns(); time.sleep(2)
            _check_news_updates()       # last — heaviest

            _state["last_run"]   = datetime.datetime.now().isoformat()
            consecutive_errors   = 0   # reset on success
            print("[ProactiveEngine] All checks done. Next in 30 min.")

        except Exception as e:
            consecutive_errors += 1
            # FIX: exponential backoff — 2^n minutes, max 60 min
            backoff = min(60 * 60, (2 ** consecutive_errors) * 60)
            print(
                f"[ProactiveEngine] Loop error #{consecutive_errors}: {e} "
                f"— backing off {backoff//60} min"
            )
            time.sleep(backoff)
            continue

        time.sleep(CHECK_INTERVAL)


# ─────────────────────────────────────────────────
# START
# ─────────────────────────────────────────────────

def start_proactive_engine():
    t = threading.Thread(target=_proactive_loop, daemon=True)
    t.start()
    print("[ProactiveEngine] Engine launched in background.")
