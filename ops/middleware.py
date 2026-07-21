import json
import logging
import time
import uuid

from django.db import connection

request_logger = logging.getLogger('ops.requests')
db_logger = logging.getLogger('ops.db')


class RequestLoggingMiddleware:
    """Logs the full lifecycle of every request as structured JSON lines,
    written to stdout so Cloud Run/Cloud Logging picks them up automatically.

    - One 'request_start' line when a request comes in.
    - One 'db_query' line per SQL query (DEBUG level only — opt in via
      LOG_LEVEL=DEBUG when you need to see individual slow queries; the SQL
      text is logged, never the parameter values, to avoid leaking data like
      password hashes into logs).
    - One 'request_end' line with total duration, query count, and total DB
      time — so at a glance you can see how much of a slow request was spent
      waiting on Neon vs. everything else.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4().hex[:12]
        request.request_id = request_id
        start = time.monotonic()

        request_logger.info(json.dumps({
            'event': 'request_start',
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
        }))

        query_count = 0
        query_time = 0.0

        def log_query(execute, sql, params, many, context):
            nonlocal query_count, query_time
            query_start = time.monotonic()
            try:
                return execute(sql, params, many, context)
            finally:
                duration = time.monotonic() - query_start
                query_count += 1
                query_time += duration
                db_logger.debug(json.dumps({
                    'event': 'db_query',
                    'request_id': request_id,
                    'duration_ms': round(duration * 1000, 2),
                    'sql': sql[:500],
                }))

        with connection.execute_wrapper(log_query):
            response = self.get_response(request)

        total_duration = time.monotonic() - start
        request_logger.info(json.dumps({
            'event': 'request_end',
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(total_duration * 1000, 2),
            'db_queries': query_count,
            'db_time_ms': round(query_time * 1000, 2),
        }))

        return response
