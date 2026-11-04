"""Uji alur UI dengan data sementara; tidak mengubah database pengguna."""

import shutil
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

import finance as fin


class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ["app.py", "style.css"]:
            shutil.copy(Path(__file__).parents[1] / name, self.root / name)
        self.app = AppTest.from_file(str(self.root / "app.py")).run(timeout=20)
        self.clean()

    def clean(self):
        self.assertFalse(list(self.app.exception))
        self.assertFalse(list(self.app.error))

    def test_demo_and_empty_private_pages(self):
        self.clean()
        self.assertEqual(self.app.metric[0].value, "¥120,000")
        for page in ["収支記録", "予算・目標", "ダッシュボード"]:
            self.app.radio[1].set_value(page).run()
            self.clean()
        self.app.radio[0].set_value("自分のデータ").run()
        self.clean()
        self.assertEqual(self.app.metric[0].value, "¥0")
        for page in ["収支記録", "予算・目標"]:
            self.app.radio[1].set_value(page).run()
            self.clean()

    def test_add_edit_delete_and_save_plan(self):
        self.app.radio[0].set_value("自分のデータ").run()
        self.app.radio[1].set_value("収支記録").run()
        self.app.number_input[0].set_value(1500)
        self.app.text_input[1].set_value("Makan siang")
        self.app.button[0].click().run()
        self.clean()
        path = self.root / "data/private/finance.sqlite3"
        self.assertEqual(fin.transactions(path).iloc[0]["amount"], 1500)
        self.app.number_input[1].set_value(2000)
        next(button for button in self.app.button if button.label == "変更を保存").click().run()
        self.clean()
        self.assertEqual(fin.transactions(path).iloc[0]["amount"], 2000)
        self.app.checkbox[0].check().run()
        next(button for button in self.app.button if button.label == "完全に削除").click().run()
        self.clean()
        self.assertTrue(fin.transactions(path).empty)
        self.app.radio[1].set_value("予算・目標").run()
        self.app.number_input[0].set_value(50000)
        self.app.number_input[1].set_value(10000)
        self.app.button[0].click().run()
        self.clean()
        self.assertIn("予算と目標を保存しました。", [item.value for item in self.app.success])

    def test_deficit_is_included_in_distance_to_goal(self):
        self.app.radio[0].set_value("自分のデータ").run()
        month = self.app.selectbox[0].value
        path = self.root / "data/private/finance.sqlite3"
        fin.save_transaction(path, month + "-01", "Pengeluaran", "Makanan", 5000)
        fin.save_plan(path, month, 10000, 10000)
        self.app.run()
        self.clean()
        self.assertEqual(self.app.metric[4].value, "−¥5,000 / ¥10,000")
        self.assertTrue(any("目標達成まであと¥15,000" in item.value for item in self.app.markdown))

    def test_japanese_display_keeps_stored_values_and_searches_categories(self):
        view = self.app.dataframe[0].value
        self.assertEqual(list(view.columns), ["日付", "区分", "カテゴリー", "メモ", "金額（円）"])
        self.assertEqual(set(view["区分"]), {"支出"})
        self.assertIn("その他の日用品", list(view["メモ"]))
        stored = fin.transactions(self.root / "data/private/demo.sqlite3")
        self.assertIn("Pengeluaran", set(stored["kind"]))
        self.assertIn("Gaji arubaito", set(stored["note"]))
        self.app.radio[1].set_value("収支記録").run()
        self.app.text_input[0].set_value("食費").run()
        self.clean()
        filtered = self.app.dataframe[0].value
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered.iloc[0]["カテゴリー"], "食費")
