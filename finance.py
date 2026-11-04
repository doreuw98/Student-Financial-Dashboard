"""Penyimpanan lokal dan perhitungan, terpisah dari antarmuka."""

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pandas as pd

CATEGORIES = {
    "Pengeluaran": ["Tempat tinggal", "Makanan", "Transportasi", "Pendidikan", "Hiburan", "Lainnya"],
    "Pemasukan": ["Kerja paruh waktu", "Beasiswa", "Kiriman keluarga", "Lainnya"],
}
MAX_AMOUNT = 1_000_000_000


@contextmanager
def database(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path):
    with database(path) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY, date TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('Pemasukan', 'Pengeluaran')),
                category TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0 AND amount <= 1000000000),
                note TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS plans (
                month TEXT PRIMARY KEY,
                budget INTEGER NOT NULL CHECK(budget >= 0 AND budget <= 1000000000),
                goal INTEGER NOT NULL CHECK(goal >= 0 AND goal <= 1000000000)
            );
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
        """)


def save_transaction(path, day, kind, category, amount, note="", transaction_id=None):
    day = date.fromisoformat(str(day))
    note = note.strip()
    if kind not in CATEGORIES or category not in CATEGORIES[kind]:
        raise ValueError("Kategori tidak sesuai dengan jenis transaksi.")
    if isinstance(amount, bool) or not isinstance(amount, int) or not 0 < amount <= MAX_AMOUNT:
        raise ValueError("Nominal harus berupa yen bulat, antara 1 dan 1.000.000.000.")
    if len(note) > 120:
        raise ValueError("Catatan maksimal 120 karakter.")
    values = (day.isoformat(), kind, category, amount, note)
    with database(path) as connection:
        if transaction_id is None:
            return connection.execute(
                "INSERT INTO transactions(date,kind,category,amount,note) VALUES(?,?,?,?,?)", values
            ).lastrowid
        cursor = connection.execute(
            "UPDATE transactions SET date=?,kind=?,category=?,amount=?,note=? WHERE id=?",
            (*values, int(transaction_id)),
        )
        if not cursor.rowcount:
            raise ValueError("Transaksi sudah tidak tersedia. Muat ulang halaman.")
        return transaction_id


def delete_transaction(path, transaction_id):
    with database(path) as connection:
        if not connection.execute("DELETE FROM transactions WHERE id=?", (int(transaction_id),)).rowcount:
            raise ValueError("Transaksi sudah tidak tersedia. Muat ulang halaman.")


def transactions(path):
    with database(path) as connection:
        return pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC, id DESC", connection)


def month_data(frame, month):
    return frame[frame["date"].str.startswith(month)].copy()


def totals(frame):
    sums = frame.groupby("kind")["amount"].sum()
    income, expenses = int(sums.get("Pemasukan", 0)), int(sums.get("Pengeluaran", 0))
    return income, expenses, income - expenses


def get_plan(path, month):
    with database(path) as connection:
        row = connection.execute("SELECT budget,goal FROM plans WHERE month=?", (month,)).fetchone()
        return (row["budget"], row["goal"]) if row else (0, 0)


def save_plan(path, month, budget, goal):
    date.fromisoformat(month + "-01")
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_AMOUNT for value in (budget, goal)):
        raise ValueError("Anggaran dan target harus antara 0 dan 1.000.000.000 yen.")
    with database(path) as connection:
        connection.execute(
            "INSERT INTO plans VALUES(?,?,?) ON CONFLICT(month) DO UPDATE SET budget=excluded.budget,goal=excluded.goal",
            (month, budget, goal),
        )


def seed_demo(path, today):
    """Isi demo sekali; demo tidak dipulihkan diam-diam setelah dihapus."""
    with database(path) as connection:
        if connection.execute("SELECT 1 FROM metadata WHERE key='seeded'").fetchone():
            return
        for offset in range(5, -1, -1):
            year, month = divmod(today.year * 12 + today.month - 1 - offset, 12)
            month += 1
            values = [
                ("Pemasukan", "Kerja paruh waktu", 70000, "Gaji arubaito"),
                ("Pemasukan", "Beasiswa", 30000, "Beasiswa bulanan"),
                ("Pemasukan", "Kiriman keluarga", 20000, "Dukungan keluarga"),
                ("Pengeluaran", "Tempat tinggal", 35000, "Sewa tempat tinggal"),
                ("Pengeluaran", "Makanan", 22000 + offset * 500, "Belanja dan makan"),
                ("Pengeluaran", "Transportasi", 8000, "Kartu transportasi"),
                ("Pengeluaran", "Pendidikan", 7000, "Buku dan alat kuliah"),
                ("Pengeluaran", "Hiburan", 8000 + offset * 300, "Waktu bersama teman"),
                ("Pengeluaran", "Lainnya", 5000, "Kebutuhan lain"),
            ]
            for number, (kind, category, amount, note) in enumerate(values):
                day = min(number * 3 + 1, today.day if offset == 0 else 28)
                connection.execute(
                    "INSERT INTO transactions(date,kind,category,amount,note) VALUES(?,?,?,?,?)",
                    (date(year, month, day).isoformat(), kind, category, amount, note),
                )
            connection.execute("INSERT OR IGNORE INTO plans VALUES(?,?,?)", (f"{year}-{month:02d}", 95000, 40000))
        connection.execute("INSERT INTO metadata VALUES('seeded', '1')")
