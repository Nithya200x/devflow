import re
from models import User
from extensions import db
from flask_jwt_extended import create_access_token
import logging

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def login(username, password):
        if not username or not password:
            return {"msg": "Username and password are required"}, None
        user = User.query.filter_by(username=username).first()
        if not user:
            logger.warning(f"Failed login attempt: user '{username}' not found")
            return {"msg": "User not found"}, None
        if not user.check_password(password):
            logger.warning(f"Failed login attempt: invalid password for '{username}'")
            return {"msg": "Invalid password"}, None
        access_token = create_access_token(
            identity=user.username,
            additional_claims={'role': user.role}
        )
        logger.info(f"User {username} logged in successfully")
        return None, {
            'access_token': access_token,
            'user': user.to_dict()
        }

    @staticmethod
    def register(name, email, username, password):
        if not name or not name.strip():
            return {"msg": "Name is required"}, None
        if not email or not email.strip():
            return {"msg": "Email is required"}, None
        if not username or not username.strip():
            return {"msg": "Username is required"}, None
        if not password or not password.strip():
            return {"msg": "Password is required"}, None

        email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        if not re.match(email_regex, email.strip()):
            return {"msg": "Invalid email format"}, None

        if len(password) < 8:
            return {"msg": "Password must be at least 8 characters"}, None

        username = username.strip()
        email = email.strip()
        name = name.strip()

        try:
            if User.query.filter_by(username=username).first():
                return {"msg": "Username already taken"}, None
            if User.query.filter_by(email=email).first():
                return {"msg": "Email already registered"}, None

            user = User(name=name, email=email, username=username, role="developer")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed for '{username}': {e}")
            return {"msg": "Registration failed due to a server error. Please try again."}, None

        access_token = create_access_token(
            identity=user.username,
            additional_claims={'role': user.role}
        )
        logger.info(f"New user registered: {username} ({email})")
        return None, {
            'access_token': access_token,
            'user': user.to_dict()
        }

    @staticmethod
    def get_all_users():
        return User.query.all()
