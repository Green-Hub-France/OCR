import hashlib
from .config import USERS


def check_credentials(username: str, password: str) -> bool:
    """Vérifie que le couple username/password correspond."""
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    return USERS.get(username) == pw_hash