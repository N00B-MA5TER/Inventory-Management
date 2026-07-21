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

In your Neon project dashboard → Connection Details. The app's settings
need the **host, database name, username, and password as five separate
values**, not the combined connection string.

If Neon shows you a single connection string like:

```
postgresql://alex:AbC123xyz@ep-cool-lab-12345.ap-southeast-1.aws.neon.tech/inventory_db?sslmode=require
```

it breaks down as:

| Piece | Where it is in the string | Example |
|---|---|---|
| `PROD_DB_USER` | between `://` and `:` | `alex` |
| `PROD_DB_PASSWORD` | between `:` and `@` | `AbC123xyz` |
| `PROD_DB_HOST` | between `@` and the next `/` | `ep-cool-lab-12345.ap-southeast-1.aws.neon.tech` |
| `PROD_DB_NAME` | after the `/`, before `?` | `inventory_db` |
| `PROD_DB_PORT` | not shown in the string — Neon uses `5432` | `5432` |

(Some Neon dashboards also have a "Parameters" toggle next to the
connection string that shows these already split out — use that if it's
there, it's less error-prone than copying substrings by hand.)

## 5. GitHub Actions secrets — step by step

These are encrypted values GitHub stores for the automated workflow to use,
so your database password and other sensitive values never sit in the code
itself. You have not added any of these yet — that's expected, this is the
step that does it.

**How to add one secret:**
1. Go to `github.com/N00B-MA5TER/Inventory-Management`
2. Click **Settings** (top tab of the repo itself — not your personal
   GitHub account settings)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click the green **New repository secret** button
5. Type the **Name** exactly as shown below (capitalization matters — copy
   it rather than retyping if you can), paste the **Value**, click
   **Add secret**
6. Repeat for every row in the table below, one at a time

**You need these 10 to deploy.** (The two `BACKUP_*` secrets from
`BACKUP_SETUP.md` are for the separate daily-backup workflow — skip them
for now, deployment doesn't need them.)

| Secret name | Value | Where to find it |
|---|---|---|
| `GCP_PROJECT_ID` | your project ID | Cloud Console, top bar next to the Google Cloud logo → project dropdown. Use **Project ID**, not the display name (it's usually lowercase-with-hyphens, sometimes with random numbers) |
| `GCP_SA_KEY` | the whole JSON file's contents | Open the `.json` file from step 3 in Notepad, Ctrl+A to select everything, Ctrl+C, paste it all (including the `{` and `}`) as the value |
| `DJANGO_SECRET_KEY` | see below | A random production secret — **do not reuse** the placeholder in your local `.env` |
| `PROD_DB_NAME` | from step 4 | |
| `PROD_DB_USER` | from step 4 | |
| `PROD_DB_PASSWORD` | from step 4 | |
| `PROD_DB_HOST` | from step 4 | |
| `PROD_DB_PORT` | `5432` | |
| `PROD_ALLOWED_HOSTS` | `.run.app` | literal value — type exactly this, see step 6 for why |
| `PROD_CSRF_TRUSTED_ORIGINS` | `https://*.run.app` | literal value — type exactly this, see step 6 for why |

**Generated `DJANGO_SECRET_KEY` value** (fresh, random, not used anywhere
else — safe to use directly, but this value has now been shared in this
conversation, so treat it as already "seen" rather than fully secret if
that matters to you):

```
wkwk8#@1)i)zxu(u5!uwciq+jim#jj-m2l%1s)!3#81*!e(6(n
```

## 6. `PROD_ALLOWED_HOSTS` and `PROD_CSRF_TRUSTED_ORIGINS`

Before you own the domain yet, Cloud Run gives every service a default URL
like `nandy-inventory-xxxxxxxxxx-el.run.app`. You won't know the exact
random part until after the first deploy.

**First deploy:** set
- `PROD_ALLOWED_HOSTS` = `.run.app` (the leading dot matches any
  subdomain, so this covers whatever random URL Cloud Run assigns without
  needing to know it in advance)
- `PROD_CSRF_TRUSTED_ORIGINS` = `https://*.run.app`

**Once you own the domain** and have it mapped (see step 8), update both to
include it:
- `PROD_ALLOWED_HOSTS` = `.run.app,nandyengineeringworks.com,www.nandyengineeringworks.com`
- `PROD_CSRF_TRUSTED_ORIGINS` = `https://*.run.app,https://nandyengineeringworks.com,https://www.nandyengineeringworks.com`

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
