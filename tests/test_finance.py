import tempfile
import unittest
from datetime import date
from pathlib import Path

import finance as fin


class FinanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "test.sqlite3"
        fin.initialize(self.path)

    def test_empty_totals_and_plan(self):
        self.assertEqual(fin.totals(fin.transactions(self.path)), (0, 0, 0))
        self.assertEqual(fin.get_plan(self.path, "2026-11"), (0, 0))
        self.assertTrue(fin.month_data(fin.transactions(self.path), "2026-11").empty)

    def test_transaction_lifecycle_and_month_filter(self):
        identity = fin.save_transaction(self.path, "2026-11-01", "Pengeluaran", "Makanan", 500, "Makan")
        fin.save_transaction(self.path, "2026-10-01", "Pemasukan", "Beasiswa", 20000)
        fin.save_transaction(self.path, "2026-11-02", "Pengeluaran", "Transportasi", 800, "Kereta", identity)
        selected = fin.month_data(fin.transactions(self.path), "2026-11")
        self.assertEqual(fin.totals(selected), (0, 800, -800))
        self.assertEqual(selected.iloc[0]["note"], "Kereta")
        fin.delete_transaction(self.path, identity)
        self.assertTrue(fin.month_data(fin.transactions(self.path), "2026-11").empty)

    def test_amount_and_category_validation(self):
        for amount in [0, -1, 1.5, True, fin.MAX_AMOUNT + 1]:
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                fin.save_transaction(self.path, "2026-11-01", "Pengeluaran", "Makanan", amount)
        with self.assertRaises(ValueError):
            fin.save_transaction(self.path, "2026-11-01", "Pemasukan", "Makanan", 100)
        with self.assertRaises(ValueError):
            fin.save_transaction(self.path, "2026-11-01", "Pengeluaran", "Makanan", 100, "x" * 121)

    def test_missing_record_does_not_succeed(self):
        with self.assertRaises(ValueError):
            fin.delete_transaction(self.path, 999)
        with self.assertRaises(ValueError):
            fin.save_transaction(self.path, "2026-11-01", "Pengeluaran", "Makanan", 100, transaction_id=999)

    def test_plan_persists_by_month(self):
        fin.save_plan(self.path, "2026-11", 90000, 30000)
        fin.save_plan(self.path, "2026-11", 80000, 40000)
        self.assertEqual(fin.get_plan(self.path, "2026-11"), (80000, 40000))
        self.assertEqual(fin.get_plan(self.path, "2026-10"), (0, 0))
        with self.assertRaises(ValueError):
            fin.save_plan(self.path, "2026-11", -1, 0)

    def test_demo_isolated_repeatable_and_never_future_dated(self):
        fin.seed_demo(self.path, date(2026, 1, 1))
        fin.seed_demo(self.path, date(2026, 1, 1))
        frame = fin.transactions(self.path)
        self.assertEqual(len(frame), 54)
        self.assertLessEqual(frame["date"].max(), "2026-01-01")
        self.assertEqual(fin.totals(fin.month_data(frame, "2026-01")), (120000, 85000, 35000))
        fin.delete_transaction(self.path, int(frame.iloc[0]["id"]))
        fin.seed_demo(self.path, date(2026, 1, 1))
        self.assertEqual(len(fin.transactions(self.path)), 53)
        private_path = Path(self.directory.name) / "private.sqlite3"
        fin.initialize(private_path)
        self.assertTrue(fin.transactions(private_path).empty)


if __name__ == "__main__":
    unittest.main()
