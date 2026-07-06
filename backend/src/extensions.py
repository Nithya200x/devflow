import os
import functools
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from sqlalchemy import exc as sa_exc

logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'migrations'))
jwt = JWTManager()


def _is_ssl_disconnect(err: Exception) -> bool:
    keywords = [
        "ssl error", "bad record mac", "ssl_syscall",
        "eof detected", "connection has been closed unexpectedly",
        "connection closed", "broken pipe",
    ]
    for e in [err, getattr(err, "orig", None)]:
        if e is not None:
            msg = str(e).lower()
            if any(kw in msg for kw in keywords):
                return True
    return False


def retry_on_db_disconnect(max_retries: int = 1):
    """Decorator: retry the wrapped function once if the DB connection
    fails due to a transient SSL / stale-connection error."""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return f(*args, **kwargs)
                except sa_exc.OperationalError as e:
                    if attempt < max_retries and _is_ssl_disconnect(e):
                        logger.warning(
                            "DB SSL disconnect caught by decorator (attempt %d/%d): %s",
                            attempt + 1, max_retries + 1, e,
                        )
                        try:
                            db.session.rollback()
                            db.session.remove()
                        except RuntimeError:
                            pass
                        continue
                    raise
            return f(*args, **kwargs)
        return wrapper
    return decorator
