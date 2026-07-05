"""
Production startup script for DevFlow backend.
Runs database migrations before gunicorn starts.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

os.environ.setdefault('FLASK_APP', 'src.app')

from app import create_app
from flask_migrate import upgrade

app = create_app()

with app.app_context():
    print("=== Running database migrations ===")
    upgrade()
    print("=== Database migrations completed ===")
