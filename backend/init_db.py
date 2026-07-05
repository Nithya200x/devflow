from app import create_app
from models import db

app = create_app()

with app.app_context():
    print("Creating production tables")
    db.create_all()
    db.session.commit()
    print("Done")
