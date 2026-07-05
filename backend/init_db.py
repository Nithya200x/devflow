from app import create_app
from models import db

app = create_app()

with app.app_context():
    print("Initializing production database...")
    db.create_all()
    print("Database initialization completed")
