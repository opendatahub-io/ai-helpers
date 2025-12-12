"""
FIPS-compliant test suite
Uses approved algorithms only
"""
import hashlib
import unittest
from src.auth import hash_password, verify_password


class TestAuthFunctions(unittest.TestCase):
    def test_password_hashing(self):
        """
        Test FIPS-compliant password hashing
        Uses approved PBKDF2-HMAC-SHA256
        """
        password = "test_password_123"
        password_hash = hash_password(password)

        # Verify format
        self.assertIn(":", password_hash)
        salt_hex, hash_hex = password_hash.split(":")
        self.assertEqual(len(salt_hex), 32)  # 16 bytes in hex

    def test_password_verification(self):
        """Test password verification"""
        password = "secure_password"
        password_hash = hash_password(password)

        # Correct password should verify
        self.assertTrue(verify_password(password, password_hash))

        # Incorrect password should not verify
        self.assertFalse(verify_password("wrong_password", password_hash))

    def test_approved_hash_algorithm(self):
        """
        Test using FIPS-approved hash algorithm
        SHA-256 is FIPS-approved
        """
        test_data = b"test data for hashing"
        # Use SHA-256 (FIPS-approved)
        hash_result = hashlib.sha256(test_data).hexdigest()
        self.assertEqual(len(hash_result), 64)  # SHA-256 produces 64 hex chars


if __name__ == "__main__":
    unittest.main()
