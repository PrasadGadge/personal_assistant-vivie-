# ==================================================
# Vivie_UI.py — WebSocket Bridge + Volume Control
# Fixed: volume uses pycaw/ctypes COM properly,
#        mute actually works on Windows 10/11
# ==================================================

import asyncio
import websockets
import json
import threading
import os

CLIENTS = set()
_loop   = None

# ─────────────────────────────────────────────────
# WINDOWS VOLUME CONTROL
# Three fallback approaches — one will work
# ─────────────────────────────────────────────────

_muted           = False
_vol_before_mute = 80


def set_system_volume(level: int):
    """
    Set Windows master volume 0-100.
    Tries pycaw first (best), falls back to PowerShell,
    then to WinMM as last resort.
    """
    level = max(0, min(100, int(level)))

    # ── Approach 1: pycaw (most reliable, already installed) ──
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        print(f"[UI] Volume → {level}% (pycaw)")
        return
    except Exception:
        pass

    # ── Approach 2: PowerShell (always on Windows 10/11) ──
    try:
        import subprocess
        scalar = level / 100.0
        ps = (
            f"$vol = [math]::Round({scalar} * 65535);"
            f"$sig = '[DllImport(\"winmm.dll\")] public static extern int waveOutSetVolume(IntPtr h, uint v);';"
            f"$t = Add-Type -MemberDefinition $sig -Name WinMM -Namespace Win -PassThru;"
            f"$t::waveOutSetVolume([IntPtr]::Zero, ($vol -bor ($vol -shl 16)))"
        )
        subprocess.run(
            ['powershell', '-WindowStyle', 'Hidden', '-Command', ps],
            capture_output=True, timeout=2
        )
        print(f"[UI] Volume → {level}% (PowerShell)")
        return
    except Exception:
        pass

    # ── Approach 3: WinMM ctypes (legacy fallback) ──
    try:
        import ctypes
        vol = int(level / 100 * 0xFFFF)
        ctypes.windll.winmm.waveOutSetVolume(0, vol | (vol << 16))
        print(f"[UI] Volume → {level}% (winmm)")
    except Exception as e:
        print(f"[UI] Volume control unavailable: {e}")


def get_system_volume() -> int:
    """Get current Windows master volume 0-100."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        return round(volume.GetMasterVolumeLevelScalar() * 100)
    except Exception:
        try:
            import ctypes
            vol = ctypes.c_ulong()
            ctypes.windll.winmm.waveOutGetVolume(0, ctypes.byref(vol))
            return round((vol.value & 0xFFFF) / 0xFFFF * 100)
        except Exception:
            return 80


def set_mute(state: bool):
    """Mute or unmute system audio."""
    global _muted, _vol_before_mute

    # ── pycaw mute (cleanest — uses actual mute flag) ──
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMute(1 if state else 0, None)
        _muted = state
        print(f"[UI] Mute → {state} (pycaw)")
        return
    except Exception:
        pass

    # ── Fallback: set volume to 0 / restore ──
    if state:
        _vol_before_mute = get_system_volume()
        set_system_volume(0)
    else:
        set_system_volume(_vol_before_mute)
    _muted = state
    print(f"[UI] Mute → {state} (volume fallback)")


# ─────────────────────────────────────────────────
# WEBSOCKET SERVER
# ─────────────────────────────────────────────────

async def _handle_client(websocket):
    CLIENTS.add(websocket)
    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
                # Run blocking volume ops in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, _handle_incoming, msg.get('type'), msg.get('value')
                )
            except Exception as e:
                print(f"[UI] Message error: {e}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CLIENTS.discard(websocket)


def _handle_incoming(msg_type: str, value):
    """Handle commands FROM browser TO Python."""
    if msg_type == 'set_volume':
        set_system_volume(int(value or 80))
    elif msg_type == 'set_mute':
        set_mute(bool(value))
    else:
        print(f"[UI] Unknown: {msg_type}")


async def _serve():
    async with websockets.serve(_handle_client, "localhost", 8765):
        print("[UI] WebSocket server ready")
        await asyncio.Future()


def _run_server():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(_serve())


def start_websocket_server():
    print("🌐 Starting WebSocket Bridge on ws://localhost:8765")
    threading.Thread(target=_run_server, daemon=True).start()


# ─────────────────────────────────────────────────
# EMIT TO UI
# ─────────────────────────────────────────────────

def emit_to_ui(event_type: str, value):
    if not CLIENTS or not _loop:
        return
    try:
        message = json.dumps({"type": event_type, "value": value})
        for client in list(CLIENTS):
            asyncio.run_coroutine_threadsafe(
                _safe_send(client, message), _loop
            )
    except Exception as e:
        print(f"[UI] Emit error: {e}")


async def _safe_send(client, message: str):
    try:
        await client.send(message)
    except Exception:
        CLIENTS.discard(client)


# ─────────────────────────────────────────────────
# AUTO-LAUNCH BROWSER
# ─────────────────────────────────────────────────

def launch_ui():
    """Open ui.html in browser after WebSocket starts."""
    import time, webbrowser, urllib.request
    time.sleep(0.8)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    live_url = "http://127.0.0.1:5500/ui.html"
    file_url = f"file:///{base_dir}/ui.html".replace("\\", "/")
    try:
        urllib.request.urlopen(live_url, timeout=0.5)
        url = live_url
    except Exception:
        url = file_url
    webbrowser.open(url)
    print(f"[UI] Browser: {url}")
