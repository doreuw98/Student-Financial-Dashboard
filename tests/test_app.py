"""Uji alur UI dengan data sementara; tidak mengubah database pengguna."""

import shutil
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

import finance as fin
import accounts


class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ["app.py", "style.css"]:
            shutil.copy(Path(__file__).parents[1] / name, self.root / name)
        self.account_path = self.root / "data/private/accounts.sqlite3"
        accounts.initialize(self.account_path)
        self.user_id = accounts.register(
            self.account_path, "test_student", "テスト学生", "Test-only password 2026"
        )
        self.app = AppTest.from_file(str(self.root / "app.py")).run(timeout=20)
        self.app.session_state["user_id"] = self.user_id
        self.app.session_state["language"] = "ja"
        self.app.run()
        self.clean()

    def personal_path(self):
        return self.root / "data/private/users" / str(self.user_id) / "finance.sqlite3"

    def clean(self):
        self.assertFalse(list(self.app.exception))
        self.assertFalse(list(self.app.error))

    def test_demo_and_empty_private_pages(self):
        self.clean()
        self.assertEqual(self.app.metric[0].value, "¥120,000")
        for page in ["transactions", "budget", "overview"]:
            self.app.radio[1].set_value(page).run()
            self.clean()
        self.app.radio[0].set_value("personal").run()
        self.clean()
        self.assertEqual(self.app.metric[0].value, "¥0")
        for page in ["transactions", "budget"]:
            self.app.radio[1].set_value(page).run()
            self.clean()

    def test_add_edit_delete_and_save_plan(self):
        self.app.radio[0].set_value("personal").run()
        self.app.radio[1].set_value("transactions").run()
        self.app.number_input[0].set_value(1500)
        self.app.text_input[1].set_value("Makan siang")
        next(
            button for button in self.app.button if button.label == "記録を追加"
        ).click().run()
        self.clean()
        path = self.personal_path()
        self.assertEqual(fin.transactions(path).iloc[0]["amount"], 1500)
        self.app.number_input[1].set_value(2000)
        next(
            button for button in self.app.button if button.label == "変更を保存"
        ).click().run()
        self.clean()
        self.assertEqual(fin.transactions(path).iloc[0]["amount"], 2000)
        self.app.checkbox[0].check().run()
        next(
            button for button in self.app.button if button.label == "完全に削除"
        ).click().run()
        self.clean()
        self.assertTrue(fin.transactions(path).empty)
        self.app.radio[1].set_value("budget").run()
        self.app.number_input[0].set_value(50000)
        self.app.number_input[1].set_value(10000)
        next(
            button for button in self.app.button if button.label == "予算・目標を保存"
        ).click().run()
        self.clean()
        self.assertIn(
            "予算と目標を保存しました。", [item.value for item in self.app.success]
        )

    def test_deficit_is_included_in_distance_to_goal(self):
        self.app.radio[0].set_value("personal").run()
        month = self.app.selectbox[0].value
        path = self.personal_path()
        fin.save_transaction(path, month + "-01", "Pengeluaran", "Makanan", 5000)
        fin.save_plan(path, month, 10000, 10000)
        self.app.run()
        self.clean()
        self.assertEqual(self.app.metric[4].value, "−¥5,000 / ¥10,000")
        self.assertTrue(
            any("目標達成まであと¥15,000" in item.value for item in self.app.markdown)
        )

    def test_japanese_display_keeps_stored_values_and_searches_categories(self):
        view = self.app.dataframe[0].value
        self.assertEqual(
            list(view.columns), ["日付", "区分", "カテゴリー", "メモ", "金額（円）"]
        )
        self.assertEqual(set(view["区分"]), {"支出"})
        self.assertIn("その他の日用品", list(view["メモ"]))
        stored = fin.transactions(
            self.root / "data/private/users" / str(self.user_id) / "demo.sqlite3"
        )
        self.assertIn("Pengeluaran", set(stored["kind"]))
        self.assertIn("Gaji arubaito", set(stored["note"]))
        self.app.radio[1].set_value("transactions").run()
        self.app.text_input[0].set_value("食費").run()
        self.clean()
        filtered = self.app.dataframe[0].value
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered.iloc[0]["カテゴリー"], "食費")

    def test_language_settings_and_all_localized_pages(self):
        self.app.radio[0].set_value("personal").run()
        for language, settings, save, back, income in [
            ("en", "設定", "設定を保存", "Back to dashboard", "Income"),
            ("id", "Settings", "Save settings", "Kembali ke ringkasan", "Pemasukan"),
            ("ja", "Pengaturan", "Simpan pengaturan", "ダッシュボードに戻る", "収入"),
        ]:
            next(
                item for item in self.app.button if item.label == settings
            ).click().run()
            self.app.selectbox[0].set_value(language)
            next(item for item in self.app.button if item.label == save).click().run()
            self.clean()
            self.assertEqual(
                accounts.get_user(self.account_path, self.user_id)["language"], language
            )
            next(item for item in self.app.button if item.label == back).click().run()
            self.clean()
            self.assertEqual(self.app.metric[0].label, income)
            self.assertEqual(self.app.radio[0].value, "personal")
            self.assertEqual(self.app.metric[0].value, "¥0")
            for page in ["transactions", "budget", "overview"]:
                self.app.radio[1].set_value(page).run()
                self.clean()

    def test_login_gate_registration_logout_and_account_isolation(self):
        legacy = self.root / "data/private/finance.sqlite3"
        fin.initialize(legacy)
        fin.save_transaction(
            legacy, "2026-11-01", "Pengeluaran", "Makanan", 321, "Legacy private note"
        )
        original_bytes = legacy.read_bytes()
        fin.initialize(self.personal_path())
        fin.save_transaction(
            self.personal_path(),
            "2026-11-01",
            "Pengeluaran",
            "Makanan",
            777,
            "Account A private note",
        )
        next(
            item for item in self.app.button if item.label == "ログアウト"
        ).click().run()
        self.assertFalse(list(self.app.metric))
        self.assertFalse(list(self.app.radio))
        self.app.text_input[0].set_value("test_student")
        self.app.text_input[1].set_value("incorrect password")
        next(item for item in self.app.button if item.label == "ログイン").click().run()
        self.assertTrue(list(self.app.error))
        self.assertFalse(list(self.app.metric))
        self.app.text_input[2].set_value("Student B")
        self.app.text_input[3].set_value("student_b")
        self.app.text_input[4].set_value("Test-only second password")
        self.app.text_input[5].set_value("Test-only second password")
        next(
            item for item in self.app.button if item.label == "アカウントを作成"
        ).click().run()
        self.assertTrue(list(self.app.success))
        self.app.text_input[0].set_value("student_b")
        self.app.text_input[1].set_value("Test-only second password")
        next(item for item in self.app.button if item.label == "ログイン").click().run()
        self.clean()
        self.assertNotEqual(self.app.session_state["user_id"], self.user_id)
        self.app.radio[0].set_value("personal").run()
        self.clean()
        self.assertEqual(self.app.metric[1].value, "¥0")
        self.assertFalse(list(self.app.dataframe))
        self.assertEqual(fin.transactions(self.personal_path()).iloc[0]["amount"], 777)
        self.assertEqual(legacy.read_bytes(), original_bytes)

    def test_same_account_keeps_records_and_budget_when_logging_in_each_language(self):
        month = self.app.selectbox[0].value
        path = self.personal_path()
        fin.initialize(path)
        fin.save_transaction(
            path, month + "-01", "Pemasukan", "Beasiswa", 12345, "My scholarship"
        )
        fin.save_transaction(
            path, month + "-01", "Pengeluaran", "Makanan", 678, "Catatan saya・私のメモ"
        )
        fin.save_plan(path, month, 9000, 3000)
        original = path.read_bytes()
        for language, login, income in [
            ("en", "Log in", "Income"),
            ("id", "Masuk", "Pemasukan"),
            ("ja", "ログイン", "収入"),
        ]:
            next(
                button
                for button in self.app.button
                if button.label in {"ログアウト", "Log out", "Keluar"}
            ).click().run()
            self.app.selectbox[0].set_value(language).run()
            self.app.text_input[0].set_value("test_student")
            self.app.text_input[1].set_value("Test-only password 2026")
            next(
                button for button in self.app.button if button.label == login
            ).click().run()
            self.clean()
            self.assertEqual(self.app.session_state["user_id"], self.user_id)
            self.assertEqual(self.app.session_state["language"], language)
            self.assertEqual(
                accounts.get_user(self.account_path, self.user_id)["language"], language
            )
            self.assertEqual(self.app.radio[0].value, "personal")
            self.assertEqual(self.app.metric[0].label, income)
            self.assertEqual(
                [item.value for item in self.app.metric[:3]],
                ["¥12,345", "¥678", "¥11,667"],
            )
            self.assertIn(
                "Catatan saya・私のメモ", list(self.app.dataframe[0].value.iloc[:, 3])
            )
            self.assertEqual(fin.get_plan(path, month), (9000, 3000))
            self.assertEqual(path.read_bytes(), original)

    def test_signup_language_is_used_after_login(self):
        next(
            button for button in self.app.button if button.label == "ログアウト"
        ).click().run()
        self.app.selectbox[0].set_value("en").run()
        self.app.text_input[2].set_value("English student")
        self.app.text_input[3].set_value("english_student")
        self.app.text_input[4].set_value("Test-only English password")
        self.app.text_input[5].set_value("Test-only English password")
        next(
            button for button in self.app.button if button.label == "Create account"
        ).click().run()
        self.assertTrue(list(self.app.success))
        user = accounts.authenticate(
            self.account_path, "english_student", "Test-only English password"
        )
        self.assertEqual(user["language"], "en")
        self.app.text_input[0].set_value("english_student")
        self.app.text_input[1].set_value("Test-only English password")
        next(
            button for button in self.app.button if button.label == "Log in"
        ).click().run()
        self.clean()
        self.assertEqual(self.app.session_state["user_id"], user["id"])
        self.assertEqual(self.app.metric[0].label, "Income")
        self.assertEqual(self.app.metric[0].value, "¥0")
