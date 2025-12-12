"""
Utility functions
LOW: Uses MD5 for file checksums (non-security use case)
"""
import hashlib


def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate MD5 checksum of a file
    LOW severity: MD5 used for checksums (non-security), marked with usedforsecurity=False
    """
    md5_hash = hashlib.md5(usedforsecurity=False)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


def verify_file_integrity(file_path: str, expected_checksum: str) -> bool:
    """Verify file integrity using checksum"""
    actual_checksum = calculate_file_checksum(file_path)
    return actual_checksum == expected_checksum
