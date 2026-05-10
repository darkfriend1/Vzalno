import requests
import urllib3
import base64
import urllib.parse
import html
import json
import re
import os
import subprocess
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------- CONFIG ----------------

REPO_NAME = "YOUR_USERNAME/YOUR_REPOSITORY"

OUTPUT_FILE = "sub.txt"
URLS_FILE = "urls.json"

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36"
)

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

INSECURE_PATTERN = re.compile(
    r'(?:[?&;]|3%[Bb])(allowinsecure|allow_insecure|insecure)=(?:1|true|yes)',
    re.IGNORECASE,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- SESSION ----------------

def build_session():
    session = requests.Session()

    adapter = HTTPAdapter(
        pool_connections=20,
        pool_maxsize=20,
        max_retries=Retry(
            total=1,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
        ),
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": CHROME_UA
    })

    return session

SESSION = build_session()

# ---------------- HELPERS ----------------

def fetch_data(url):
    for attempt in range(3):
        try:
            verify = True

            if attempt >= 1:
                verify = False

            r = SESSION.get(
                url,
                timeout=15,
                verify=verify
            )

            r.raise_for_status()

            return r.text

        except Exception as e:
            if attempt == 2:
                raise e

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

            if any(p in decoded.lower() for p in PROTOCOL_PREFIXES):
                return decoded

        except:
            pass

    return data

def extract_host_port(line):
    try:
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
                return f"{host}:{port}"

        m = re.search(
            r"(?:@|//)([\w\.-]+):(\d+)",
            line
        )

        if m:
            return f"{m.group(1)}:{m.group(2)}"

    except:
        pass

    return None

# ---------------- MAIN ----------------

def main():

    if not os.path.exists(URLS_FILE):
        print("urls.json not found")
        return

    with open(URLS_FILE, "r", encoding="utf-8") as f:
        URLS = json.load(f)

    all_configs = []
    seen_full = set()
    seen_hostport = set()

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

                line = line.strip()

                if not line.lower().startswith(PROTOCOL_PREFIXES):
                    continue

                processed = urllib.parse.unquote(
                    html.unescape(line)
                )

                if INSECURE_PATTERN.search(processed):
                    continue

                if line in seen_full:
                    continue

                seen_full.add(line)

                hostport = extract_host_port(line)

                if hostport:

                    if hostport in seen_hostport:
                        continue

                    seen_hostport.add(hostport)

                all_configs.append(line)

            print(f"OK: {url}")

        except Exception as e:
            print(f"ERROR: {url}")
            print(str(e))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_configs))

    print()
    print(f"Saved {len(all_configs)} configs")
    print(f"Output: {OUTPUT_FILE}")

    try:
        subprocess.run(["git", "add", "."], check=True)

        subprocess.run(
            ["git", "commit", "-m", "Auto update subscription"],
            check=True
        )

        subprocess.run(["git", "push"], check=True)

        print("GitHub updated")

    except:
        print("No git changes")

if __name__ == "__main__":
    main()
