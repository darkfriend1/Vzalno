import requests
import base64
import re
import socket
import urllib.parse
import html
import json
import os

# =========================
# НАСТРОЙКИ
# =========================

URLS_FILE = "urls.json"
OUTPUT_FILE = "sub.txt"

MAX_CONFIGS = 350
PING_TIMEOUT = 2
CHECK_ALIVE = True

PROTOCOLS = (
    "vmess://", "vless://", "trojan://",
    "ss://", "socks5://"
)

# =========================
# СТРАНЫ
# =========================

COUNTRY_FLAGS = {
    "germany": "🇩🇪 Германия",
    "de": "🇩🇪 Германия",
    "russia": "🇷🇺 Россия",
    "ru": "🇷🇺 Россия",
    "netherlands": "🇳🇱 Нидерланды",
    "nl": "🇳🇱 Нидерланды",
    "france": "🇫🇷 Франция",
    "fr": "🇫🇷 Франция",
    "usa": "🇺🇸 США",
    "us": "🇺🇸 США",
    "uk": "🇬🇧 Великобритания",
    "england": "🇬🇧 Великобритания",
}

# =========================
# DOWNLOAD
# =========================

def fetch(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text

# =========================
# BASE64
# =========================

def decode_b64(data):
    try:
        data = "".join(data.split())
        pad = len(data) % 4
        if pad:
            data += "=" * (4 - pad)
        return base64.b64decode(data).decode("utf-8", errors="ignore")
    except:
        return data

# =========================
# СТРАНА
# =========================

def get_country(text):
    t = text.lower()
    for k, v in COUNTRY_FLAGS.items():
        if k in t:
            return v
    return "🌍 Unknown"

# =========================
# ПИНГ
# =========================

def check_alive(config):
    try:
        m = re.search(r"@([^:/]+):(\d+)", config)
        if not m:
            return True

        host = m.group(1)
        port = int(m.group(2))

        s = socket.socket()
        s.settimeout(PING_TIMEOUT)
        ok = s.connect_ex((host, port))
        s.close()

        return ok == 0
    except:
        return False

# =========================
# PARSE
# =========================

def parse(raw):
    raw = decode_b64(raw)

    result = []
    for line in raw.splitlines():
        line = line.strip()
        if any(line.startswith(p) for p in PROTOCOLS):
            result.append(line)

    return result

# =========================
# MAIN
# =========================

def main():

    if not os.path.exists(URLS_FILE):
        print("urls.json not found")
        return

    with open(URLS_FILE, "r", encoding="utf-8") as f:
        urls = json.load(f)

    configs = []
    seen = set()

    # 👉 системные флаги Happ
    header = [
        "#hide-settings: 1",
        "#subscription-crypto: 1",
        ""
    ]

    for url in urls:

        print("Loading:", url)

        try:
            data = fetch(url)
            configs_raw = parse(data)

            for cfg in configs_raw:

                if len(configs) >= MAX_CONFIGS:
                    break

                if cfg in seen:
                    continue

                seen.add(cfg)

                if CHECK_ALIVE:
                    if not check_alive(cfg):
                        continue

                country = get_country(cfg)
                name = f"{country} #{len(configs)+1}"

                configs.append(f"{cfg}# {name}")

        except Exception as e:
            print("ERROR:", e)

    # =========================
    # SAVE
    # =========================

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(header + configs))

    print("\nDONE:", len(configs), "configs")

if __name__ == "__main__":
    main()
