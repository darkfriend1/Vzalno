import requests
import base64
import re
import socket

# =========================
# НАСТРОЙКИ
# =========================

SUB_URL = "https://raw.githubusercontent.com/darkfriend1/vzalno/main/sub.txt"

MAX_CONFIGS = 300   # 👈 сколько конфигов в подписке

PROTOCOLS = (
    "vmess://", "vless://", "trojan://", "ss://", "socks5://"
)

COUNTRY_FLAGS = {
    "germany": "🇩🇪 Германия",
    "de": "🇩🇪 Германия",
    "russia": "🇷🇺 Россия",
    "ru": "🇷🇺 Россия",
    "netherlands": "🇳🇱 Нидерланды",
    "nl": "🇳🇱 Нидерланды",
    "usa": "🇺🇸 США",
    "us": "🇺🇸 США",
    "france": "🇫🇷 Франция",
    "fr": "🇫🇷 Франция",
}

# =========================
# ЗАГРУЗКА
# =========================

def fetch_sub():
    r = requests.get(SUB_URL, timeout=15)
    return r.text

# =========================
# BASE64 DECODE
# =========================

def decode_base64(text):
    try:
        missing = len(text) % 4
        if missing:
            text += "=" * (4 - missing)
        return base64.b64decode(text).decode("utf-8", errors="ignore")
    except:
        return text

# =========================
# СТРАНА
# =========================

def detect_country(text):
    t = text.lower()
    for key, name in COUNTRY_FLAGS.items():
        if key in t:
            return name
    return "🌍 Unknown"

# =========================
# ПИНГ / ПРОВЕРКА ЖИВОСТИ
# =========================

def check_config_alive(config: str, timeout=1.5) -> bool:
    try:
        match = re.search(r"@([^:/]+):(\d+)", config)
        if not match:
            return True

        host = match.group(1)
        port = int(match.group(2))

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        result = sock.connect_ex((host, port))
        sock.close()

        return result == 0

    except:
        return False

# =========================
# ПАРСИНГ
# =========================

def parse_configs(raw):
    raw = decode_base64(raw)

    configs = []
    for line in raw.splitlines():
        line = line.strip()
        if any(line.startswith(p) for p in PROTOCOLS):
            configs.append(line)

    return configs

# =========================
# СБОРКА ПОДПИСКИ
# =========================

def build_subscription(configs):
    result = []
    count = 0

    for cfg in configs:

        if count >= MAX_CONFIGS:
            break

        # ❌ проверка живости
        if not check_config_alive(cfg):
            continue

        country = detect_country(cfg)
        name = f"{country} #{count + 1}"

        result.append(f"{cfg}  # {name}")
        count += 1

    return "\n".join(result)

# =========================
# MAIN
# =========================

def main():
    raw = fetch_sub()
    configs = parse_configs(raw)

    final = build_subscription(configs)

    with open("sub_clean.txt", "w", encoding="utf-8") as f:
        f.write(final)

    print(f"Готово: обработано {len(configs)} конфигов")

if __name__ == "__main__":
    main()
