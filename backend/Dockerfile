FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=5000 \
    FLASK_APP=src/app.py

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system devflow \
    && adduser --system --ingroup devflow devflow

COPY . .

# Run migrations and then start the server
CMD ["sh", "-c", "flask db upgrade && gunicorn \"src.app:create_app()\" --bind 0.0.0.0:${PORT:-5000} --workers 2"]
