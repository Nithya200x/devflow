import time

from flask import request
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST


request_count = Counter(
    "devflow_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "http_status"],
)

request_duration = Histogram(
    "devflow_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

error_count = Counter(
    "devflow_http_errors_total",
    "Total HTTP errors (status >= 400)",
    ["method", "path", "http_status"],
)

active_requests = Gauge(
    "devflow_active_requests",
    "Currently active HTTP requests",
)


def register_metrics(app):
    @app.before_request
    def before_request():
        request._prom_start_time = time.monotonic()
        active_requests.inc()

    @app.after_request
    def after_request(response):
        dt = time.monotonic() - request._prom_start_time
        method = request.method
        path = request.path
        status = response.status_code

        request_count.labels(method=method, path=path, http_status=status).inc()
        request_duration.labels(method=method, path=path).observe(dt)

        if status >= 400:
            error_count.labels(method=method, path=path, http_status=status).inc()

        active_requests.dec()
        return response

    @app.route("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
