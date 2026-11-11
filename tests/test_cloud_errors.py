import unittest
from unittest.mock import patch

try:
    import psycopg
except ImportError:
    psycopg = None

from cloud_database import CloudDatabase


@unittest.skipIf(psycopg is None, "Hosted dependencies are optional for local use")
class CloudErrorTests(unittest.TestCase):
    def test_connection_failure_redacts_credentials(self):
        secret = "postgresql://owner:private-password@example.invalid/neondb"
        error = psycopg.OperationalError(f"password authentication failed: {secret}")
        with patch("psycopg.connect", side_effect=error):
            with self.assertRaises(OSError) as caught:
                with CloudDatabase(secret).connect():
                    self.fail("A failed connection must not be used")
        message = str(caught.exception)
        self.assertIn("connect:AUTHENTICATION", message)
        self.assertNotIn(secret, message)
        self.assertNotIn("private-password", message)
