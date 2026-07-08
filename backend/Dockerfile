FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=5000 \
    FLASK_APP=src/app.py

WORKDIR /app

RUN addgroup --system devflow \
    && adduser --system --ingroup devflow devflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=devflow:devflow . .
RUN chown devflow:devflow /app

USER devflow

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

LABEL org.opencontainers.image.title="DevFlow Backend" \
      org.opencontainers.image.description="DevFlow SaaS Backend API" \
      org.opencontainers.image.version="2.0.0"

CMD ["sh", "-c", "python init_db.py && gunicorn \"wsgi:app\" --bind 0.0.0.0:${PORT:-5000} --workers 3 --timeout 300 --access-logfile - --error-logfile -"]
