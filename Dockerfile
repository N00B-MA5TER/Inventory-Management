FROM python:3.11-slim

# Without this, Python fully buffers stdout when it's not a terminal (which
# it never is in a container) — logs can sit in memory instead of reaching
# Cloud Logging until the buffer fills or the process exits. Confirmed this
# the hard way testing the new request-logging middleware locally.
ENV PYTHONUNBUFFERED=1

# libpq5: runtime lib psycopg2-binary needs to talk to Postgres
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic only needs settings.py to *import* successfully — it never
# connects to the database — so these placeholders are fine at build time.
# Cloud Run's real runtime env vars override all of this when the container
# actually starts serving traffic.
ENV SECRET_KEY=build-time-placeholder \
    DEBUG=False \
    DB_NAME=build \
    DB_USER=build \
    DB_PASSWORD=build \
    DB_HOST=build \
    ALLOWED_HOSTS=localhost

RUN python manage.py collectstatic --noinput

EXPOSE 8080

# Shell form (not exec-array) so $PORT expands; `exec` keeps gunicorn as PID 1
# for correct signal handling on Cloud Run's SIGTERM during shutdown/deploys.
CMD exec gunicorn config.wsgi:application --bind :$PORT --workers 2 --threads 2 --timeout 60
