# Codeforces → Discord Contest Reminder

Posts an embed to a Discord channel whenever a Codeforces contest is coming up
within the next `REMIND_WINDOW_HOURS` (default: 48). Runs on a GitHub Actions
schedule — no server needed.

## Setup

1. **Add the files in this folder to your repo** (`notify.py`,
   `requirements.txt`, `notified.json`, `.github/workflows/cf-notify.yml`).

2. **Add your webhook URL as a repo secret:**
   - GitHub repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: your webhook URL (the one you already created)

3. **Push to GitHub.** The workflow runs automatically every hour
   (`0 * * * *` cron) and can also be triggered manually from the
   Actions tab (`workflow_dispatch`).

4. **Adjust the schedule** in `.github/workflows/cf-notify.yml` if you want
   it to check more/less often — [crontab.guru](https://crontab.guru) helps
   with the cron syntax. Note: GitHub's actual run time can lag a few
   minutes behind the scheduled time under load.

5. **Adjust the reminder window** by changing `REMIND_WINDOW_HOURS` in the
   workflow's `env:` block (e.g. `24` for one day out, `168` for a week out).

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

## Extending later

The script is intentionally scoped to contest reminders only. If you
later want rating-change or submission tracking for a specific handle,
those need a different Codeforces endpoint (`user.rating` /
`user.status`) and a different dedupe strategy — happy to add that as a
separate script when you're ready.
