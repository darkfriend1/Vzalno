import requests
import urllib3
import base64
import urllib.parse
import html
import json
import re
import socket

# =========================
# НАСТРОЙКИ
# =========================

OUTPUT_FILE = "sub.txt"
URLS_FILE = "urls.json"

# 👇 СКОЛЬКО КОНФИГОВ БУДЕТ В ПОДПИСКЕ
MAX_CONFIGS = 92

# 👇 ПРОВЕРКА РАБОТОСПОСОБНОСТИ
CHECK_ALIVE = True

# 👇 ТАЙМАУТ ПРОВЕРКИ
PING_TIMEOUT = 1.5

# =========================
# ПРОТОКОЛЫ
# =========================

PROTOCOL_PREFIXES = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "ssr://",
    "tuic://",
    "hysteria://",
    "hysteria2://",
    "hy2://"
)

# =========================
# ФЛАГИ СТРАН
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

    "japan": "🇯🇵 Япония",
    "jp": "🇯🇵 Япония",

    "singapore": "🇸🇬 Сингапур",
    "sg": "🇸🇬 Сингапур",

    "canada": "🇨🇦 Канада",
    "ca": "🇨🇦 Канада",

    "turkey": "🇹🇷 Турция",
    "tr": "🇹🇷 Турция",

    "poland": "🇵🇱 Польша",
    "pl": "🇵🇱 Польша",
}

# =========================
# SESSION
# =========================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# =========================
# BASE64
# =========================

def try_decode_base64(data):

    if "://" not in data:

        try:
            clean = "".join(data.split())

            rem = len(clean) % 4

            if rem:
                clean += "=" * (4 - rem)

            decoded = base64.b64decode(clean).decode(
                "utf-8",
                errors="ignore"
            )

            if any(
                p in decoded.lower()
                for p in PROTOCOL_PREFIXES
            ):
                return decoded

        except:
            pass

    return data

# =========================
# СКАЧИВАНИЕ
# =========================

def fetch_data(url):

    r = SESSION.get(
        url,
        timeout=20,
        verify=False
    )

    r.raise_for_status()

    return r.text

# =========================
# ПОЛУЧЕНИЕ HOST:PORT
# =========================

def extract_host_port(line):

    try:

        # VMESS
        if line.startswith("vmess://"):

            payload = line[8:]

            rem = len(payload) % 4

            if rem:
                payload += "=" * (4 - rem)

            decoded = base64.b64decode(payload).decode(
                "utf-8",
                errors="ignore"
            )

            j = json.loads(decoded)

            host = j.get("add")
            port = j.get("port")

            if host and port:
                return str(host), int(port)

        # ДРУГИЕ ПРОТОКОЛЫ
        m = re.search(
            r"(?:@|//)([\w\.-]+):(\d+)",
            line
        )

        if m:
            return m.group(1), int(m.group(2))

    except:
        pass

    return None

# =========================
# ПРОВЕРКА ЖИВОСТИ
# =========================

def check_alive(host, port):

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(PING_TIMEOUT)

        result = sock.connect_ex((host, port))

        sock.close()

        return result == 0

    except:
        return False

# =========================
# СТРАНА
# =========================

def detect_country(text):

    t = text.lower()

    for key, value in COUNTRY_FLAGS.items():

        if key in t:
            return value

    return "🌍 Unknown"

# =========================
# ИМЯ КОНФИГА
# =========================

def rename_config(config, new_name):

    # vmess
    if config.startswith("vmess://"):

        try:

            payload = config[8:]

            rem = len(payload) % 4

            if rem:
                payload += "=" * (4 - rem)

            decoded = base64.b64decode(payload).decode(
                "utf-8",
                errors="ignore"
            )

            j = json.loads(decoded)

            j["ps"] = new_name

            encoded = base64.b64encode(
                json.dumps(
                    j,
                    ensure_ascii=False
                ).encode()
            ).decode()

            return "vmess://" + encoded

        except:
            return config

    # остальные
    if "#" in config:
        config = config.split("#")[0]

    return config + "#" + urllib.parse.quote(new_name)

# =========================
# MAIN
# =========================

def main():

    if not os.path.exists(URLS_FILE):

        print("urls.json not found")
        return

    with open(
        URLS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        URLS = json.load(f)

    all_configs = []

    seen_full = set()
    seen_hostport = set()

    print()
    print("START PARSER")
    print()

    for url in URLS:

        print(f"Downloading: {url}")

        try:

            data = fetch_data(url)

            data = try_decode_base64(data)

            pattern = "|".join(
                p.replace("://", "")
                for p in PROTOCOL_PREFIXES
            )

            data = re.sub(
                rf"({pattern})://",
                r"\n\1://",
                data,
                flags=re.IGNORECASE
            )

            for line in data.splitlines():

                if len(all_configs) >= MAX_CONFIGS:
                    break

                line = line.strip()

                if not line.lower().startswith(
                    PROTOCOL_PREFIXES
                ):
                    continue

                processed = urllib.parse.unquote(
                    html.unescape(line)
                )

                if line in seen_full:
                    continue

                seen_full.add(line)

                hp = extract_host_port(line)

                if hp:

                    host, port = hp

                    key = f"{host}:{port}"

                    if key in seen_hostport:
                        continue

                    seen_hostport.add(key)

                    # ПРОВЕРКА РАБОТОСПОСОБНОСТИ
                    if CHECK_ALIVE:

                        alive = check_alive(
                            host,
                            port
                        )

                        if not alive:
                            continue

                country = detect_country(processed)

                name = (
                    f"{country} "
                    f"| #{len(all_configs)+1}"
                )

                line = rename_config(
                    line,
                    name
                )

                all_configs.append(line)

            print("OK")

        except Exception as e:

            print("ERROR")
            print(str(e))

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("\n".join(all_configs))

    print()
    print(f"ГОТОВО: {len(all_configs)} конфигов")
    print(f"Сохранено: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
