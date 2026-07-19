# Restoring from a Backup

Read this fully before running anything — restoring is destructive to
whatever database you point it at.

**Before you reach for this doc, check: is the database actually gone, or
just temporarily paused/unreachable?** (e.g. a free-tier host asleep or over
its usage cap.) If it's paused, restoring a backup elsewhere doesn't fix
that faster — you'd just be creating a second, separate copy of the data
while the original is still sitting there, and any orders placed after your
backup was taken would only exist in the paused original. Restoring is for
when the data itself is actually lost, corrupted, or you're deliberately
migrating to a new database host.

## 1. Get the backup file

Open the Google Drive backup folder (see `BACKUP_SETUP.md` for where it is)
and download the `.dump` file you want — usually the most recent one, named
`nandy_inventory_backup_<date>_<time>.dump`.

## 2. Have a target database ready

This should almost always be a **fresh, empty** Postgres database — either
a new one you just created with your host, or a new local database for
testing the restore itself. Get its connection details (host, port, user,
password, database name).

## 3. Restore

From a machine with `pg_restore` installed (the same PostgreSQL client
tools used for backups) and the downloaded `.dump` file in your current
directory:

```bash
pg_restore \
  --host=<target-host> \
  --port=<target-port> \
  --username=<target-user> \
  --dbname=<target-database-name> \
  --clean --if-exists --no-owner \
  nandy_inventory_backup_<date>_<time>.dump
```

It will prompt for the password (or set `PGPASSWORD` in the environment
first). `--clean --if-exists` drops existing objects in the target database
before recreating them — this is why the target must be a database you're
sure you want overwritten, not a live production database with newer data
you care about.

## 4. Point the app at the restored database

Update `DB_HOST` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` (in `.env` for
local, or the hosting platform's environment variables for production) to
the restored database, then restart the app.

## 5. Verify

Log in and check a few things look right: recent orders are present, item
counts look sane, staff accounts still exist. Don't consider the restore
done until you've actually looked, not just assumed the command succeeding
means the data is correct.
