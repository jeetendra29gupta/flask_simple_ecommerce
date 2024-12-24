from functools import wraps

import bcrypt
from flask import redirect, session, url_for


# Utility functions for password hashing and verification
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password (str): The password to verify.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password is valid, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function
