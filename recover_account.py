"""Recover an account from the trusted local computer terminal."""

from getpass import GetPassWarning, getpass
from pathlib import Path
import warnings

import accounts


def main():
    database = Path(__file__).resolve().parent / "data/private/accounts.sqlite3"
    if not database.is_file():
        print("Database akun tidak ditemukan. Buka folder aplikasi yang dipakai saat mendaftar.")
        return 1
    try:
        users = accounts.list_local_users(database)
        if not users:
            print("Belum ada akun di database ini.")
            return 1
        for user in users:
            print(f'{user["id"]}. {user["display_name"]!r} (@{user["username"]})')
        selection = input("Masukkan nomor akun, atau Enter untuk selesai: ").strip()
        if not selection:
            return 0
        user = next((user for user in users if str(user["id"]) == selection), None)
        if user is None:
            print("Nomor akun tidak ditemukan.")
            return 1
        username = input("Username baru (Enter untuk tetap): ").strip() or None
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            password = getpass("Kata sandi baru (12–128 karakter, Enter untuk tetap): ") or None
            if password is not None and getpass("Ulangi kata sandi baru: ") != password:
                print("Konfirmasi kata sandi tidak cocok.")
                return 1
        if username is None and password is None:
            print("Tidak ada kredensial yang diubah.")
            return 0
        accounts.recover_local_user(database, user["id"], username, password)
    except GetPassWarning:
        print("Buka terminal interaktif di VS Code agar input kata sandi tersembunyi.")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nPemulihan dibatalkan.")
        return 1
    except ValueError as error:
        print(error)
        return 1
    print("Kredensial akun diperbarui. Silakan masuk kembali.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
