"""
FIPS-compliant cryptographic operations
"""
import hashlib
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    Uses secrets module (FIPS-compliant when system is in FIPS mode)
    """
    return secrets.token_hex(length)


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file (FIPS-approved algorithm)
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def encrypt_data(data: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
    """
    Encrypt data using AES-256-GCM (FIPS-approved AEAD cipher)
    Returns: (nonce, ciphertext, tag)
    """
    # Use secrets for nonce generation
    nonce = secrets.token_bytes(12)  # GCM recommended nonce size

    # Create AES-GCM cipher (FIPS-approved)
    cipher = Cipher(
        algorithms.AES(key),  # AES with 256-bit key
        modes.GCM(nonce),
        backend=default_backend()
    )

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()

    return nonce, ciphertext, encryptor.tag


def decrypt_data(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES-256-GCM
    """
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce, tag),
        backend=default_backend()
    )

    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    return plaintext
