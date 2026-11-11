# Menjalankan dashboard online

Versi online memakai Auth0 Universal Login untuk pendaftaran, verifikasi email,
dan reset kata sandi. Alamat email menjadi identitas login. Pengguna yang lupa
email perlu menemukan pesan pendaftaran dari Auth0 di kotak masuknya atau
menghubungi pengelola. Data keuangan disimpan per akun berdasarkan ID Auth0.

## Siapkan Render Free, Neon Free, dan Auth0

1. Buat proyek PostgreSQL di Neon pada paket **Free**, khusus untuk dashboard.
   Di Render, buat Python Web Service dari repo GitHub dan pilih **Free**.
   Salin URL koneksi langsung dari Neon ke variabel rahasia Render bernama
   `DASHBOARD_DATABASE_URL`. Aplikasi membuat skema saat akun pertama kali
   memakai dashboard, jadi role database perlu izin `CREATE` pada database.
   Transaksi, anggaran, dan profil online disimpan di Neon.
2. Di Auth0, buat aplikasi **Regular Web Application** dan aktifkan database
   connection dengan pendaftaran email terbuka. Konfigurasikan pengiriman email
   produksi untuk verifikasi dan reset kata sandi sebelum membagikan link.
   Untuk uji coba terbatas, Auth0 menyediakan pengirim email bawaan.
   Gunakan alamat Render
   sebagai Allowed Logout URL, dan tambahkan `/oauth2callback` pada alamat itu
   untuk Allowed Callback URL.
3. Di Render, tambahkan secret file bernama `secrets.toml` dengan isi berikut.
   Ganti semua placeholder. Buat `cookie_secret` acak, misalnya dengan
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

   ```toml
   [auth]
   redirect_uri = "https://YOUR-SERVICE.onrender.com/oauth2callback"
   cookie_secret = "YOUR_RANDOM_COOKIE_SECRET"
   client_id = "YOUR_AUTH0_CLIENT_ID"
   client_secret = "YOUR_AUTH0_CLIENT_SECRET"
   server_metadata_url = "https://YOUR_AUTH0_DOMAIN/.well-known/openid-configuration"
   ```

4. Gunakan Build Command `pip install -r requirements-hosted.txt` dan
   Start Command berikut.

   ```sh
   python start_hosted.py
   ```

   Atur `PYTHON_VERSION` ke `3.14.10` dan health check ke `/_stcore/health`.
   Perintah ini meminta Auth0 menampilkan formulir setiap kali pengguna
   menekan tombol daftar atau masuk, termasuk saat sesi Auth0 lama masih aktif.
5. Sebelum membagikan link, uji dua akun dengan alamat email yang berbeda.
   Pastikan verifikasi email dan reset kata sandi sampai ke kotak masuk.
   Buat transaksi di akun pertama, pastikan akun kedua tidak melihatnya,
   lalu periksa bahwa transaksi masih ada setelah reset kata sandi dan redeploy.
   Siapkan cadangan PostgreSQL untuk pemulihan data.

Akun online dibuat dari awal. Folder database lokal dan file rahasia tetap
dikecualikan oleh Git. Jika ingin memindahkan data lokal, lakukan sebagai
migrasi terpisah dengan persetujuan pemilik data.

- [Konfigurasi autentikasi Streamlit](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [Konfigurasi email produksi Auth0](https://auth0.com/docs/customize/email/smtp-email-providers)
- [Batas paket Render Free](https://render.com/docs/free)
- [Paket Neon Free](https://neon.com/docs/introduction/plans)
