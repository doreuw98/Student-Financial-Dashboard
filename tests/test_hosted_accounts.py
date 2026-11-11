import tempfile
import time
import unittest
from pathlib import Path

import hosted_accounts
from cloud_database import CloudDatabase


class HostedAccountsTests(unittest.TestCase):
    def test_verified_identity_is_stable_and_profiles_are_isolated(self):
        claims = {
            "iss": "https://identity.example/",
            "sub": "auth0|first",
            "email_verified": True,
            "email": "old@example.com",
            "exp": int(time.time()) + 300,
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "profiles.sqlite3"
            self.assertIsNone(hosted_accounts.profile(path, dict(claims, email_verified=False), "ja"))
            self.assertIsNone(hosted_accounts.profile(path, dict(claims, exp=0), "ja"))
            self.assertFalse(path.exists())
            first = hosted_accounts.profile(path, claims, "ja")
            hosted_accounts.set_language(path, first["id"], "id")
            renamed = hosted_accounts.profile(path, dict(claims, email="new@example.com"), "ja")
            second = hosted_accounts.profile(path, dict(claims, sub="auth0|second"), "ja")
            self.assertEqual((renamed["id"], renamed["language"]), (first["id"], "id"))
            self.assertNotEqual(first["id"], second["id"])
            self.assertEqual(second["language"], "ja")
            cloud = CloudDatabase("postgresql://example.invalid/dashboard")
            schemas = {
                cloud.ledger(user["id"], mode).schema
                for user in (first, second)
                for mode in ("personal", "demo")
            }
            self.assertEqual(len(schemas), 4)
            self.assertTrue(all(len(schema) <= 63 for schema in schemas))
