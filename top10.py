"""GitHub 주간 트렌딩 TOP10을 Slack / Telegram으로 전송.

env: SLACK_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (설정된 채널만 전송)
     DEEPL_API_KEY (선택, 설명 한국어 번역)
--dry-run: 전송 없이 메시지만 출력
"""
import html
import json
import os
import re
import sys
import urllib.request

TRENDING_URL = "https://github.com/trending?since=weekly"


def env(name):
    return (os.environ.get(name) or "").strip()  # 붙여넣기 공백 방지


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "weekly-top10"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse(page):
    repos = []
    for art in re.findall(r'<article class="Box-row">(.*?)</article>', page, re.S):
        name = re.search(r'<h2.*?href="/([^"]+)"', art, re.S)
        stars = re.search(r"([\d,]+) stars this week", art)
        if not (name and stars):
            continue
        desc = re.search(r"<p [^>]*>(.*?)</p>", art, re.S)
        repos.append({
            "repo": name.group(1),
            "desc": html.unescape(re.sub(r"<[^>]+>", "", desc.group(1))).strip() if desc else "",
            "stars": int(stars.group(1).replace(",", "")),
        })
    return sorted(repos, key=lambda r: r["stars"], reverse=True)[:10]


def translate(top, key):
    """설명을 DeepL로 한 번에 한국어 번역. 실패 시 원문 유지(발송이 우선)."""
    idx = [i for i, r in enumerate(top) if r["desc"]]
    if not (key and idx):
        return top
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    req = urllib.request.Request(
        f"https://{host}/v2/translate",
        json.dumps({"text": [top[i]["desc"] for i in idx], "target_lang": "KO"}).encode(),
        {"Content-Type": "application/json", "Authorization": f"DeepL-Auth-Key {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            texts = [t["text"] for t in json.load(r)["translations"]]
    except Exception as e:  # noqa: BLE001
        print(f"DeepL 번역 실패, 원문으로 전송: {e}", file=sys.stderr)
        return top
    out = [dict(r) for r in top]
    for i, t in zip(idx, texts):
        out[i]["desc"] = t
    return out


def build_message(top):
    total = sum(r["stars"] for r in top)
    lines = [f"이번 주 깃허브 TOP{len(top)}이 받은 별 {total:,}개 ⭐", ""]
    for rank, r in reversed(list(enumerate(top, 1))):
        short = r["repo"].split("/")[1]
        desc = f" — {r['desc']}" if r["desc"] else ""
        lines.append(f"{rank}위 {short}{desc} (+{r['stars']:,}★)")
    lines += ["", "📋 링크"] + [f"github.com/{r['repo']}" for r in top]
    return "\n".join(lines)


def post_json(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()


def main():
    top = parse(fetch(TRENDING_URL))
    if not top:
        sys.exit("트렌딩 파싱 결과 0건 — GitHub 페이지 구조 변경 확인 필요")
    msg = build_message(translate(top, env("DEEPL_API_KEY")))
    if "--dry-run" in sys.argv:
        print(msg)
        return

    slack = env("SLACK_WEBHOOK_URL")
    tg_token, tg_chat = env("TELEGRAM_BOT_TOKEN"), env("TELEGRAM_CHAT_ID")
    if not (slack or (tg_token and tg_chat)):
        sys.exit("전송 채널 미설정: SLACK_WEBHOOK_URL 또는 TELEGRAM_BOT_TOKEN+TELEGRAM_CHAT_ID")
    if slack:
        post_json(slack, {"text": msg})
    if tg_token and tg_chat:
        post_json(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                  {"chat_id": tg_chat, "text": msg, "disable_web_page_preview": True})
    print("sent")


if __name__ == "__main__":
    main()
