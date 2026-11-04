#!/usr/bin/env python3
"""Publish due Instagram Reels from poster/queue/ (standard library only).

Each queue file is poster/queue/<id>.json:
  {
    "account": "ctsoccerhub" | "clip.theory67",
    "due_at": "2026-11-06T09:00:00-05:00",   # ISO 8601 with offset
    "video_url": "https://raw.githubusercontent.com/...mp4",  # public, direct
    "caption": "text with #hashtags",
    "share_to_feed": true                      # optional, default true
  }

A file is posted when due_at <= now. Posts more than MAX_LATE_HOURS late are
skipped (marked "expired") instead of posted. After an attempt the file moves
to poster/done/ with a "result" block added (posted, failed or expired).
A failed post is retried on later runs up to MAX_ATTEMPTS times.

Tokens come from environment variables, one per account (see ACCOUNTS).
Run with --dry-run to see what would be posted without calling Instagram.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "queue"
DONE = ROOT / "done"
API = "https://graph.instagram.com/" + os.environ.get("IG_API_VERSION", "v23.0")
ACCOUNTS = {
    "ctsoccerhub": "IG_TOKEN_CTSOCCERHUB",
    "clip.theory67": "IG_TOKEN_CLIPTHEORY67",
}
MAX_LATE_HOURS = 6
MAX_ATTEMPTS = 3
CAPTION_LIMIT = 2200
HASHTAG_LIMIT = 30


def call(method, url, params):
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        # Never print the token: the URL/body we sent is not echoed.
        raise RuntimeError(f"HTTP {e.code}: {body[:500]}") from None


def publish(token, item):
    me = call("GET", f"{API}/me", {"fields": "user_id,username", "access_token": token})
    user_id = me.get("user_id") or me.get("id")
    if me.get("username") and me["username"].lower() != item["account"].lower():
        raise RuntimeError(f"token belongs to @{me['username']}, not @{item['account']}")
    container = call("POST", f"{API}/{user_id}/media", {
        "media_type": "REELS",
        "video_url": item["video_url"],
        "caption": item.get("caption", ""),
        "share_to_feed": "true" if item.get("share_to_feed", True) else "false",
        "access_token": token,
    })["id"]
    # Instagram downloads and processes the video; poll until it is ready.
    for _ in range(60):  # up to ~10 minutes
        time.sleep(10)
        status = call("GET", f"{API}/{container}",
                      {"fields": "status_code,status", "access_token": token})
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {code}: {status.get('status')}")
    else:
        raise RuntimeError("video still processing after 10 minutes")
    media = call("POST", f"{API}/{user_id}/media_publish",
                 {"creation_id": container, "access_token": token})["id"]
    link = call("GET", f"{API}/{media}", {"fields": "permalink", "access_token": token})
    return media, link.get("permalink")


def validate(item):
    problems = []
    if item.get("account") not in ACCOUNTS:
        problems.append(f"unknown account {item.get('account')!r}")
    url = item.get("video_url", "")
    if not url.startswith("https://") or not url.lower().split("?")[0].endswith(".mp4"):
        problems.append("video_url must be a public https .mp4 link")
    cap = item.get("caption", "")
    if len(cap) > CAPTION_LIMIT:
        problems.append(f"caption longer than {CAPTION_LIMIT} characters")
    if cap.count("#") > HASHTAG_LIMIT:
        problems.append(f"more than {HASHTAG_LIMIT} hashtags")
    try:
        due = dt.datetime.fromisoformat(item["due_at"])
        if due.tzinfo is None:
            problems.append("due_at needs a UTC offset")
    except Exception:
        problems.append("due_at is missing or not ISO 8601")
    return problems


def main():
    dry = "--dry-run" in sys.argv
    now = dt.datetime.now(dt.timezone.utc)
    DONE.mkdir(exist_ok=True)
    changed = False
    exit_code = 0
    for path in sorted(QUEUE.glob("*.json")):
        item = json.loads(path.read_text())
        problems = validate(item)
        if problems:
            print(f"[invalid] {path.name}: {'; '.join(problems)}")
            exit_code = 1
            continue
        due = dt.datetime.fromisoformat(item["due_at"])
        if due > now:
            print(f"[waiting] {path.name} @{item['account']} due {item['due_at']}")
            continue
        late_h = (now - due).total_seconds() / 3600
        result = item.setdefault("result", {})
        if late_h > MAX_LATE_HOURS:
            if dry:
                print(f"[would expire] {path.name}")
                continue
            result.update(status="expired", at=now.isoformat(),
                          note=f"{late_h:.1f}h late, not posted")
            print(f"[expired] {path.name}")
        elif dry:
            print(f"[would post] {path.name} @{item['account']} ({late_h*60:.0f} min after due)")
            continue
        else:
            token = os.environ.get(ACCOUNTS[item["account"]])
            if not token:
                print(f"[no token] {path.name}: secret {ACCOUNTS[item['account']]} is not set yet")
                continue
            try:
                media, link = publish(token, item)
                result.update(status="posted", at=now.isoformat(), media_id=media, permalink=link)
                print(f"[posted] {path.name} @{item['account']} {link}")
            except Exception as e:  # keep going with the other posts
                attempts = result.get("attempts", 0) + 1
                result.update(attempts=attempts, last_error=str(e)[:500])
                print(f"[failed {attempts}/{MAX_ATTEMPTS}] {path.name}: {str(e)[:300]}")
                exit_code = 1
                if attempts < MAX_ATTEMPTS:
                    path.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n")
                    changed = True
                    continue
                result.update(status="failed", at=now.isoformat())
        (DONE / path.name).write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n")
        path.unlink()
        changed = True
    if changed and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("changed=true\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
