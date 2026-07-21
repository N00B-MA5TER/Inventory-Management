# Reading the Detailed Request/Database Logs

Every request now logs structured JSON lines (via
`ops/middleware.py::RequestLoggingMiddleware`) to stdout, which Cloud Run
picks up automatically — no extra agent or config needed on the GCP side.

## What gets logged

- **`request_start`** — the moment a request comes in (method, path, a
  `request_id` that ties everything below together).
- **`db_query`** (DEBUG level only, see below) — one line per SQL query,
  with its own duration and the query text (parameter values are never
  logged, only the query template, so passwords/etc. never end up in logs).
- **`request_end`** — total request duration, how many DB queries ran, and
  their combined time. This is the line that answers "was this request slow
  because of Neon, or something else?" — compare `db_time_ms` to
  `duration_ms`.

## Viewing them in Cloud Logging

Cloud Run console → your service → **Logs** tab, or the standalone
[Logs Explorer](https://console.cloud.google.com/logs). Structured JSON
fields are queryable directly. Useful filters:

```
jsonPayload.event="request_end"
jsonPayload.duration_ms>500
```
(finds slow requests)

```
jsonPayload.request_id="<id from a request_end line>"
```
(pulls every line for one specific request — start, all its queries, and
the end summary, in order)

```
jsonPayload.event="db_query"
jsonPayload.duration_ms>100
```
(finds individually slow queries — only shows up if `LOG_LEVEL=DEBUG`, see
below)

## Turning on per-query logging

Default (`LOG_LEVEL=INFO`, set in `deploy.yml`) gives you `request_start`/
`request_end` with a DB time *total* per request — enough to tell whether
Neon is the bottleneck. To see *which specific query* is slow, temporarily
set `LOG_LEVEL: DEBUG` at the top of `.github/workflows/deploy.yml`, push,
look at what you need, then set it back to `INFO` and push again — DEBUG
logs every query on every request, which is a lot more log volume (still
nowhere near Cloud Logging's free tier at this app's traffic, just noisier
to read).

## What this doesn't cover

This measures time *inside Django* — from when Django's middleware stack
starts processing the request to when it hands back a response. It doesn't
include Cloud Run's own queueing/cold-start time before your code even
starts running. Cloud Run's built-in request logs (same Logs Explorer,
`httpRequest.latency`) cover that outer layer — the two are complementary,
not duplicates.
