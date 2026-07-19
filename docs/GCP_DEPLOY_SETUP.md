# Deploying to Cloud Run — One-Time Setup

Once this is done, every push to `main` on GitHub automatically tests and
redeploys the app (`.github/workflows/deploy.yml`). This doc is the
one-time setup to make that first deploy possible.

## 1. Enable required APIs

In the [Google Cloud Console](https://console.cloud.google.com/), with your
project selected: APIs & Services → Library → enable each of:
- **Cloud Run Admin API**
- **Artifact Registry API**
- **IAM API**

## 2. Create an Artifact Registry repository

This is where built Docker images get stored before Cloud Run runs them.

Artifact Registry → Create Repository:
- Name: `nandy-inventory`
- Format: Docker
- Region: `asia-south1` (Mumbai — matches the region in `deploy.yml`; if you
  pick a different region, update `GCP_REGION` at the top of that file too)

## 3. Create a deploy service account

This is what GitHub Actions uses to authenticate to Google Cloud and deploy
on your behalf.

1. IAM & Admin → Service Accounts → Create Service Account.
2. Name it e.g. `github-deployer`.
3. Grant it these roles (Grant Access step, or add later via IAM):
   - **Cloud Run Admin**
   - **Artifact Registry Writer**
   - **Service Account User**
4. Once created → Keys → Add Key → Create new key → JSON. Downloads a
   `.json` file — **treat it like a password**, never commit it to git.

## 4. Get your Neon connection details

In your Neon project dashboard → Connection Details. You need the host,
database name, username, and password separately (not just the combined
connection string) — the app's settings read them as individual values.

## 5. GitHub Actions secrets

Repo → Settings → Secrets and variables → Actions → New repository secret.
Add each of these (some you may have already added for the backup workflow
— reuse the same values, don't create duplicates with different names):

| Secret name | Value | Used by |
|---|---|---|
| `GCP_PROJECT_ID` | Your Google Cloud project ID (not the display name — check the Cloud Console header) | deploy |
| `GCP_SA_KEY` | Entire contents of the JSON key from step 3 | deploy |
| `DJANGO_SECRET_KEY` | A random production secret — **do not reuse** the placeholder in your local `.env`. One was generated for you: see below. | deploy, backup |
| `PROD_DB_NAME` | From Neon (step 4) | deploy, backup |
| `PROD_DB_USER` | From Neon | deploy, backup |
| `PROD_DB_PASSWORD` | From Neon | deploy, backup |
| `PROD_DB_HOST` | From Neon | deploy, backup |
| `PROD_DB_PORT` | Usually `5432` | deploy, backup |
| `PROD_ALLOWED_HOSTS` | See step 6 | deploy |
| `PROD_CSRF_TRUSTED_ORIGINS` | See step 6 | deploy |
| `BACKUP_DRIVE_FOLDER_ID` | From `BACKUP_SETUP.md`, if not already added | backup |
| `BACKUP_GOOGLE_CREDENTIALS_JSON` | From `BACKUP_SETUP.md`, if not already added | backup |

**Generated `DJANGO_SECRET_KEY` value** (fresh, random, not used anywhere
else — safe to use directly, but this value has now been shared in this
conversation, so treat it as already "seen" rather than fully secret if
that matters to you):

```
wkwk8#@1)i)zxu(u5!uwciq+jim#jj-m2l%1s)!3#81*!e(6(n
```

## 6. `PROD_ALLOWED_HOSTS` and `PROD_CSRF_TRUSTED_ORIGINS`

Before you own the domain yet, Cloud Run gives every service a default URL
like `nandy-inventory-xxxxxxxxxx-el.a.run.app`. You won't know the exact
random part until after the first deploy.

**First deploy:** set
- `PROD_ALLOWED_HOSTS` = `.a.run.app` (the leading dot matches any
  subdomain, so this covers whatever random URL Cloud Run assigns without
  needing to know it in advance)
- `PROD_CSRF_TRUSTED_ORIGINS` = `https://*.a.run.app`

**Once you own the domain** and have it mapped (see step 8), update both to
include it:
- `PROD_ALLOWED_HOSTS` = `.a.run.app,nandyengineeringworks.com,www.nandyengineeringworks.com`
- `PROD_CSRF_TRUSTED_ORIGINS` = `https://*.a.run.app,https://nandyengineeringworks.com,https://www.nandyengineeringworks.com`

Then push any commit (or re-run the workflow manually) to pick up the change.

## 7. First deploy

Push to `main` (or go to the repo's Actions tab → "Test & Deploy" →
"Run workflow" to trigger it manually). Watch the Actions tab — the `test`
job runs first (0 tests exist yet, passes trivially), then `deploy` runs
migrations against Neon and deploys to Cloud Run.

Once it finishes, find the live URL in the Cloud Run console (or in the
workflow's deploy step output) and check it loads.

## 8. Custom domain (once you've purchased nandyengineeringworks.com)

Cloud Run → your service → Manage Custom Domains → Add Mapping. Google
gives you DNS records to add at your domain registrar; propagation +
automatic HTTPS certificate provisioning can take up to ~24 hours the first
time. Not actionable until the domain is actually purchased — come back to
this step then.
