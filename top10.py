"""GitHub 주간 트렌딩 TOP10을 Slack / Telegram으로 전송.

env: SLACK_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (설정된 채널만 전송)
--dry-run: 전송 없이 메시지만 출력
"""
import html
import json
import os
import re
import sys
import urllib.request

TRENDING_URL = "https://github.com/trending?since=weekly"


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
    msg = build_message(top)
    if "--dry-run" in sys.argv:
        print(msg)
        return

    slack = os.environ.get("SLACK_WEBHOOK_URL")
    tg_token, tg_chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
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
