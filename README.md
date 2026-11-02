# GitHub 주간 TOP10 자동 알림

매주 월요일 09:00(KST)에 GitHub Trending 주간 순위 TOP10(이번 주 받은 별 기준)을 Slack 또는 Telegram으로 보냅니다.
GitHub Actions에서 돌아가므로 서버가 필요 없고 무료입니다.

## 결과물 예시

```
이번 주 깃허브 TOP10이 받은 별 76,461개 ⭐

10위 TradingAgents — Multi-Agents LLM Financial Trading Framework (+5,432★)
...
1위 impeccable — The design vocabulary for your coding agent. (+12,017★)

📋 링크
github.com/pbakaus/impeccable
...
```

## 설정 (10분)

1. 이 레포를 fork하거나 파일 3개(`top10.py`, `test_top10.py`, `.github/workflows/weekly-top10.yml`)를 내 레포에 복사합니다.
2. 받을 채널을 준비합니다. 둘 중 하나만 해도 됩니다.
   - **Slack**: api.slack.com/apps → Create App → Incoming Webhooks → 채널을 고르면 Webhook URL이 나옵니다.
   - **Telegram**: @BotFather에 `/newbot`을 보내 토큰을 받습니다. 봇을 채널이나 그룹에 초대한 뒤
     `https://api.telegram.org/bot<토큰>/getUpdates`에서 `chat.id`를 확인합니다.
3. 레포 Settings → Secrets and variables → Actions에 아래 값을 등록합니다.

   | Secret | 필요한 경우 |
   |---|---|
   | `SLACK_WEBHOOK_URL` | Slack으로 받을 때 |
   | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Telegram으로 받을 때 |
   | `DEEPL_API_KEY` | (선택) 레포 설명을 한국어로 번역할 때. deepl.com/pro-api 무료 플랜(월 50만 자)으로 충분합니다. 번역이 실패하면 원문으로 보냅니다 |

4. Actions 탭 → `weekly-top10` → **Run workflow**로 한 번 테스트합니다. 그다음부터는 매주 자동으로 실행됩니다.

## 로컬 확인

```bash
python test_top10.py        # 파서 자체 점검
python top10.py --dry-run   # 전송 없이 메시지만 출력
```

## 자주 묻는 것

- **발송 요일·시간 변경**: `weekly-top10.yml`의 `cron`을 수정합니다. 시간은 UTC 기준이라 KST는 9시간을 빼야 합니다.
- **"파싱 결과 0건" 에러**: GitHub Trending 페이지 구조가 바뀐 경우입니다. `top10.py`의 `parse()`를 고칩니다.
- **60일 동안 레포에 커밋이 없으면** GitHub가 예약 실행(schedule)을 자동으로 끕니다. Actions 탭에서 다시 켜면 됩니다.
- **사내망에서 직접 실행할 때**는 `github.com`, `hooks.slack.com`, `api.telegram.org`로 나가는 443 포트가 열려 있어야 합니다.
