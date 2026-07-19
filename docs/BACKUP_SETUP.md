# Database Backup — One-Time Setup

This sets up a daily automated backup of the production database to a Google
Drive folder, via a scheduled GitHub Actions workflow
(`.github/workflows/backup.yml`) running `python manage.py backup_database`.

**What this protects against:** accidental data loss, corruption, or the
hosting provider's account/database being suspended or deleted. **What it
does not do:** bring the database back online faster if it's just paused
(e.g. a free-tier usage cap) — that's a separate availability concern, not
a data-loss one.

## 1. Enable the Google Drive API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/), using
   the same project you're using for Cloud Run (or a new one).
2. APIs & Services → Library → search "Google Drive API" → Enable.

## 2. Create a service account

1. APIs & Services → Credentials → Create Credentials → Service Account.
2. Give it any name (e.g. `inventory-backup`). No project roles/IAM
   permissions are needed — access is granted by sharing a Drive folder with
   it directly (step 4), not through IAM.
3. Once created, open the service account → Keys → Add Key → Create new key
   → JSON. This downloads a `.json` file — **treat it like a password**,
   don't commit it to git.
4. Open the JSON file and note the `client_email` field (looks like
   `inventory-backup@your-project.iam.gserviceaccount.com`) — you'll need it
   in the next step.

## 3. Create and share the backup folder

1. In [Google Drive](https://drive.google.com), create a folder, e.g.
   "Nandy Inventory Backups".
2. Right-click → Share → paste the service account's `client_email` → give
   it **Editor** access.
3. Open the folder and copy its ID from the URL:
   `https://drive.google.com/drive/folders/`**`THIS_PART_IS_THE_FOLDER_ID`**

## 4. Add GitHub Actions secrets

In your GitHub repo: Settings → Secrets and variables → Actions → New
repository secret. Add each of these:

| Secret name | Value |
|---|---|
| `DJANGO_SECRET_KEY` | Same value as production's `SECRET_KEY` (or any random string — this job doesn't serve web requests, it just needs Django settings to load) |
| `PROD_DB_NAME` | From your Neon connection details |
| `PROD_DB_USER` | From your Neon connection details |
| `PROD_DB_PASSWORD` | From your Neon connection details |
| `PROD_DB_HOST` | From your Neon connection details |
| `PROD_DB_PORT` | Usually `5432` |
| `BACKUP_DRIVE_FOLDER_ID` | The folder ID from step 3 |
| `BACKUP_GOOGLE_CREDENTIALS_JSON` | The **entire contents** of the JSON key file from step 2 |

## 5. Test it

Go to the repo's Actions tab → "Database Backup" workflow → "Run workflow"
(this is the `workflow_dispatch` trigger — lets you run it on demand instead
of waiting for the 2 AM schedule). Check the Drive folder afterwards for a
new `nandy_inventory_backup_<timestamp>.dump` file.

After that, it runs automatically every day — nothing more to do unless you
want to change the schedule (edit the `cron` line in the workflow file) or
retention window (the `RETENTION_DAYS` constant in
`ops/management/commands/backup_database.py`, currently 30 days).

If something ever goes wrong and you need to restore from one of these
backups, see [`BACKUP_RESTORE.md`](BACKUP_RESTORE.md).
