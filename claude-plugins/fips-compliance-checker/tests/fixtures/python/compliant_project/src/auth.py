"""
FIPS-compliant authentication module
Uses approved algorithms via cryptography library
"""
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 (FIPS-approved)
    """
    # Use secrets module for cryptographically secure random salt
    salt = secrets.token_bytes(16)

    # Use FIPS-approved PBKDF2 with SHA-256
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # NIST recommended minimum
    )

    password_hash = kdf.derive(password.encode())
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash"""
    try:
        salt_hex, expected_hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hash_hex)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        password_hash = kdf.derive(password.encode())
        return password_hash == expected_hash
    except (ValueError, Exception):
        return False


class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)
