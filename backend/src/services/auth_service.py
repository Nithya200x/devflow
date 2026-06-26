from models import User
from extensions import db
from flask_jwt_extended import create_access_token
import logging

logger = logging.getLogger(__name__)

class AuthService:

    @staticmethod
    def login(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            access_token = create_access_token(
                identity=user.username,
                additional_claims={'role': user.role}
            )
            logger.info(f"User {username} logged in successfully")
            return {
                'access_token': access_token,
                'user': {'username': user.username, 'role': user.role}
            }
        logger.warning(f"Failed login attempt for username: {username}")
        return None

    @staticmethod
    def get_all_users():
        return User.query.all()
