"""
Test suite for cryptographic functions
HIGH: Uses MD5 in test code (non-production but still flagged)
"""
import hashlib
import unittest


class TestCryptoFunctions(unittest.TestCase):
    def test_md5_hashing(self):
        """
        Test MD5 hashing functionality
        HIGH severity: MD5 usage in test code
        While this is test code, it demonstrates non-compliant patterns
        """
        test_data = b"test data"
        # HIGH: MD5 usage in tests - should use approved algorithms in tests too
        md5_hash = hashlib.md5(test_data).hexdigest()
        self.assertEqual(len(md5_hash), 32)

    def test_hash_comparison(self):
        """Test hash comparison logic"""
        data1 = b"identical data"
        data2 = b"identical data"

        # HIGH: MD5 usage
        hash1 = hashlib.md5(data1).hexdigest()
        hash2 = hashlib.md5(data2).hexdigest()

        self.assertEqual(hash1, hash2)


if __name__ == "__main__":
    unittest.main()
