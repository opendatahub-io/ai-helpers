"""
Authentication module with FIPS violations
CRITICAL: Uses MD5 for password hashing
"""
import hashlib
import os


def hash_password(password: str) -> str:
    """
    Hash a password using MD5 (CRITICAL VIOLATION)
    This is a FIPS compliance violation - MD5 should not be used for passwords
    """
    salt = os.urandom(16)
    # CRITICAL: MD5 is not approved for password hashing
    password_hash = hashlib.md5(password.encode() + salt).hexdigest()
    return f"{salt.hex()}:{password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash"""
    try:
        salt_hex, expected_hash = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        # CRITICAL: MD5 is not approved for password verification
        password_hash = hashlib.md5(password.encode() + salt).hexdigest()
        return password_hash == expected_hash
    except ValueError:
        return False


class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)
