import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import accounts
import finance as fin

PASSWORD = "Only for automated tests 2026"


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "accounts.sqlite3"
        accounts.initialize(self.path)

    def test_local_recovery_preserves_identity_and_rejects_duplicate_username(self):
        first = accounts.register(self.path, "student_a", "学生A", PASSWORD, "id")
        accounts.register(self.path, "student_b", "学生B", PASSWORD)
        replacement = "New local recovery password"
        self.assertEqual(accounts.list_local_users(self.path)[0]["username"], "student_a")
        with self.assertRaises(ValueError):
            accounts.recover_local_user(self.path, first, "student_b", replacement)
        self.assertEqual(accounts.authenticate(self.path, "student_a", PASSWORD)["id"], first)
        with fin.database(self.path) as connection:
            connection.execute(
                "UPDATE users SET failed_attempts=5, locked_until=? WHERE id=?",
                (accounts.time.time() + 300, first),
            )
        accounts.recover_local_user(self.path, first, "New_Student", replacement)
        user = accounts.authenticate(self.path, "new_student", replacement)
        self.assertEqual((user["id"], user["language"]), (first, "id"))
        with self.assertRaises(ValueError):
            accounts.authenticate(self.path, "new_student", PASSWORD)

    def test_registration_login_unique_names_and_no_plaintext_passwords(self):
        first = accounts.register(self.path, " Student_A ", "学生A", PASSWORD)
        second = accounts.register(self.path, "student_b", "学生B", PASSWORD)
        self.assertEqual(
            accounts.authenticate(self.path, "STUDENT_A", PASSWORD)["id"], first
        )
        with fin.database(self.path) as connection:
            rows = connection.execute(
                "SELECT password_hash FROM users ORDER BY id"
            ).fetchall()
        self.assertNotEqual(rows[0][0], rows[1][0])
        self.assertNotIn(PASSWORD, self.path.read_bytes().decode("latin1"))
        self.assertNotIn("password_hash", accounts.get_user(self.path, second))
        with self.assertRaises(ValueError):
            accounts.register(self.path, "student_a", "Duplicate", PASSWORD)
        with self.assertRaises(ValueError):
            accounts.authenticate(self.path, "student_a", "wrong password")
        with self.assertRaises(ValueError):
            accounts.authenticate(self.path, "missing_user", PASSWORD)

    def test_validation_and_account_specific_language(self):
        for username, name, password in [
            ("..", "Name", PASSWORD),
            ("valid", "", PASSWORD),
            ("valid", "Name", "short"),
        ]:
            with self.subTest(username=username), self.assertRaises(ValueError):
                accounts.register(self.path, username, name, password)
        first = accounts.register(self.path, "first", "First", PASSWORD)
        second = accounts.register(self.path, "second", "Second", PASSWORD)
        accounts.set_language(self.path, first, "en")
        self.assertEqual(
            accounts.authenticate(self.path, "first", PASSWORD)["language"], "en"
        )
        self.assertEqual(accounts.get_user(self.path, second)["language"], "ja")
        with self.assertRaises(ValueError):
            accounts.set_language(self.path, first, "unsupported")

    def test_lockout_is_persisted_and_expires(self):
        identity = accounts.register(self.path, "student", "Student", PASSWORD)
        with patch("accounts.time.time", return_value=1000):
            for _ in range(5):
                with self.assertRaises(ValueError):
                    accounts.authenticate(self.path, "student", "incorrect")
            with self.assertRaisesRegex(ValueError, "5分"):
                accounts.authenticate(self.path, "student", PASSWORD)
        with patch("accounts.time.time", return_value=1301):
            self.assertEqual(
                accounts.authenticate(self.path, "student", PASSWORD)["id"], identity
            )
        with fin.database(self.path) as connection:
            row = connection.execute(
                "SELECT failed_attempts,locked_until FROM users"
            ).fetchone()
        self.assertEqual(tuple(row), (0, 0))
