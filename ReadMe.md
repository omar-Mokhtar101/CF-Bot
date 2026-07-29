# Codeforces → Discord Contest Reminder

Posts an embed to a Discord channel whenever a Codeforces contest is coming up
within the next `REMIND_WINDOW_HOURS` (default: 48). Runs on a GitHub Actions
schedule — no server needed.

## How duplicate prevention works

`notified.json` stores the IDs of contests already announced. After each
run, the workflow commits the updated file back to the repo, so the bot
"remembers" across runs and won't repost the same contest.

## Local testing

```bash
pip install -r requirements.txt
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python notify.py
```
