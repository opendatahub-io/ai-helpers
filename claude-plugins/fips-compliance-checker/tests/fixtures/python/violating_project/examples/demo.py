"""
Demo code showing crypto usage
MEDIUM: Uses deprecated crypto in example code
"""
import hashlib


def demonstrate_hashing():
    """
    Demonstrate hash functions
    MEDIUM severity: Example code using deprecated algorithms
    """
    sample_data = b"Hello, World!"

    # MEDIUM: SHA-1 usage in example code
    sha1_hash = hashlib.sha1(sample_data).hexdigest()
    print(f"SHA-1: {sha1_hash}")

    # MEDIUM: MD5 usage in example
    md5_hash = hashlib.md5(sample_data).hexdigest()
    print(f"MD5: {md5_hash}")

    # This is better but examples should demonstrate best practices
    sha256_hash = hashlib.sha256(sample_data).hexdigest()
    print(f"SHA-256: {sha256_hash}")


if __name__ == "__main__":
    demonstrate_hashing()
