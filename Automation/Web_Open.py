import webbrowser
import socket
from Automation.Web_Data import websites


# ===============================
# 🌐 Internet Check
# ===============================

def is_online() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


# ===============================
# 🌍 Open Website Automation
# ===============================

def openweb(webname: str) -> bool:
    if not webname.strip():
        print("[ERROR] Empty website name.")
        return False

    if not is_online():
        print("[ERROR] No internet connection.")
        return False

    websites_name = webname.lower().split()
    counts = {}
    not_found = []

    for name in websites_name:
        counts[name] = counts.get(name, 0) + 1

    urls_to_open = []

    for name, count in counts.items():
        if name in websites:
            urls_to_open.extend([websites[name]] * count)
        else:
            not_found.append(name)

    for url in urls_to_open:
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[ERROR] Failed to open {url}: {e}")

    if urls_to_open:
        print("[SUCCESS] Website(s) opening...")
    if not_found:
        print(f"[WARNING] Not found: {', '.join(not_found)}")

    return bool(urls_to_open)