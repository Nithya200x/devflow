import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'migrations'))
jwt = JWTManager()
