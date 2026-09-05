#!/usr/bin/env python3
"""arg_fetch.py — headless fallback for fetching /partial-capture.

Primary fetch path is Playwright MCP browser (browser session is authenticated).
This script is the alternative for cron/manual runs without MCP: requires a
.Blizzard cookie file at .blizzard-cookie (gitignored).

Idempotent: same hash → no-op. Different hash → append entry + regenerate index.html.
NEVER pushes to git (regla no-auto-push). Just commits locally for user to review.
"""
import json, sys, hashlib, pathlib, subprocess, urllib.request, urllib.error
from datetime import datetime, timezone

DIR = pathlib.Path(__file__).parent
DATA = DIR / "data" / "transmissions.json"
HASH_FILE = DIR / ".last-hash"
COOKIE_FILE = DIR / ".blizzard-cookie"
LOG_FILE = DIR / ".fetch.log"

ENDPOINT = "https://starcraft.blizzard.com/en-us/partial-capture"


def utc_now(fmt: str) -> str:
    """Current UTC time formatted with strftime pattern."""
    return datetime.now(timezone.utc).strftime(fmt)


def git_commit(message: str, cwd: pathlib.Path) -> None:
    """Stage all + commit. Never pushes (regla no-auto-push)."""
    subprocess.run(["git", "add", "-A"], cwd=cwd, check=False)
    subprocess.run(["git", "commit", "-m", message], cwd=cwd, check=False)


def decode_binary(binary: str) -> str:
    """Decode an 8-bit ASCII binary string (whitespace-separated) to text.

    Non-8-bit chunks are filtered out. Invalid chars become '?'.
    """
    out = []
    for chunk in binary.split():
        if len(chunk) != 8 or not all(c in "01" for c in chunk):
            continue
        try:
            out.append(chr(int(chunk, 2)))
        except (ValueError, OverflowError):
            out.append("?")
    return "".join(out)


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def fetch_endpoint(cookie: str) -> str:
    req = urllib.request.Request(
        ENDPOINT,
        headers={"Accept": "application/json", "Cookie": cookie},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_messages(payload: str) -> dict | None:
    """Extract transmission + messages from the response payload.

    Returns None if the response is gated (no messages in data, regardless
    of inner status/message — server signals gate via empty data).
    """
    try:
        j = json.loads(payload)
    except json.JSONDecodeError:
        return None
    data = j.get("data") or {}
    messages = data.get("messages") or []
    if not messages:
        return None  # gate (CONNECTION BREACHED, empty data, etc.)
    return {
        "transmission": data.get("transmission"),
        "messages": messages,
    }


def append_entry(messages: list, transmission: str) -> bool:
    """Append a decoded entry to today's day in transmissions.json.

    Returns True if appended, False if duplicate.
    """
    if not DATA.exists():
        raise FileNotFoundError(DATA)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    today = utc_now("%Y-%m-%d")
    now = utc_now("%H:%M")

    decoded_msgs = []
    for m in messages:
        if not m:
            continue
        if all(c in "01 \n" for c in m) and any(len(c) == 8 for c in m.split()):
            decoded_msgs.append(decode_binary(m))
        else:
            decoded_msgs.append(m)

    new_entry = {
        "time": now,
        "type": "found",
        "label": f"transmission {transmission}",
        "title": f"Nueva transmission {transmission}",
        "body_html": "<pre class=\"memo\">" + "\n\n".join(
            f"Mensaje {idx}: {m[:500]}{'...' if len(m) > 500 else ''}"
            for idx, m in enumerate(decoded_msgs) if m
        ) + "</pre>",
    }

    # Find or create today's day block
    today_day = None
    for d in data["days"]:
        if d["date"] == today:
            today_day = d
            break
    if today_day is None:
        today_day = {
            "date": today, "open": True,
            "transmission": transmission, "entries": [],
        }
        data["days"].append(today_day)

    # Dedup: skip if last entry has same label
    if today_day["entries"] and today_day["entries"][-1].get("label") == new_entry["label"]:
        return False

    today_day["entries"].append(new_entry)
    today_day["open"] = True
    today_day["transmission"] = transmission

    DATA.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def main() -> int:
    if not COOKIE_FILE.exists():
        log("no .blizzard-cookie file; skipping")
        return 0
    cookie = COOKIE_FILE.read_text(encoding="utf-8").strip()
    if not cookie:
        log("empty cookie; skipping")
        return 0

    try:
        payload = fetch_endpoint(cookie)
    except urllib.error.HTTPError as e:
        log(f"http {e.code}: gate or expired cookie")
        return 0
    except (urllib.error.URLError, TimeoutError) as e:
        log(f"network: {e}")
        return 0

    new_hash = sha256(payload)
    old_hash = HASH_FILE.read_text(encoding="utf-8").strip() if HASH_FILE.exists() else ""
    if new_hash == old_hash:
        log("no change")
        return 0

    parsed = parse_messages(payload)
    if parsed is None:
        log("gate response (CONNECTION BREACHED); skipping")
        return 0

    if not append_entry(parsed["messages"], parsed["transmission"]):
        log("duplicate entry; skipping")
        HASH_FILE.write_text(new_hash, encoding="utf-8")
        return 0

    HASH_FILE.write_text(new_hash, encoding="utf-8")
    log(f"new transmission {parsed['transmission']}")

    # Regenerate index.html
    r = subprocess.run([sys.executable, str(DIR / "render.py")])
    if r.returncode != 0:
        log("render.py failed")
        return 1

    # Local commit only — never push (regla no-auto-push)
    git_commit(
        f"ARG: transmission {parsed['transmission']} @ {utc_now('%Y-%m-%d %H:%M')} UTC",
        cwd=DIR,
    )
    log("committed locally (no push)")
    return 0


if __name__ == "__main__":
    sys.exit(main())