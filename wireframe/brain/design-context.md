# Design Context — drDarsoBot

Generated: 2026-10-23

## App Overview
Admin console untuk drDarsoBot, chatbot WhatsApp layanan informasi RSUD dr. Darsono Pacitan. Bot menjawab jadwal dokter, ketersediaan kamar, dan info umum RS lewat LLM + function calling. Operator memantau percakapan dan dapat mengambil alih (takeover) dari web. Belum ada kode/tampilan existing; konteks diambil dari `drDarsoBot_context.md`.

## Target Platform
Desktop / Web (operator bekerja di PC/laptop meja informasi). Tidak dioptimalkan untuk HP.

## Layout Patterns
- Menu horizontal di bar atas (tinggi 52px): brand "drDarsoBot · Admin Console" kiri, menu tengah (aktif = teks teal + garis bawah), nama user + Ganti Password + Logout kanan
- Konten utama full-height di bawah bar; Live Chats memakai 2 panel (daftar | percakapan), Perangkat & Prompt memakai panel utama + panel samping
- Kepadatan tinggi (token Precision & Density): font 12–14px, padding 8–16px
- Login: kartu 320px di tengah layar

## Navigation
- Menu: Dashboard (halaman awal), Live Chats, Prompt & Info RS, Coba Bot, Perangkat, Log, Pengguna
- Tidak ada role: semua user melihat menu yang sama
- Tautan antar-halaman: Dashboard "Hubungkan" → Perangkat, "Lihat di Log →" → Log

## Page Types (sesuai prototype `wireframe/prototype/`)
### Dashboard — Opsi 1 Kartu & Grafik
- Toolbar: rentang Hari ini/7/30 hari, pilih perangkat, "Diperbarui HH:MM · otomatis tiap 30 dtk"
- 5 kartu angka (Pesan masuk, Dijawab bot, Dibalas operator, Takeover aktif, Error = kartu merah)
- Grafik batang pesan per hari (hari ini disorot) + bar horizontal pemakaian tool & rata-rata latency
- Tabel status perangkat (tombol Hubungkan bila terputus) + tabel error terakhir (nomor disamarkan)

### Live Chats — Opsi 2 Antrean Prioritas
- Daftar: cari nomor, toggle 🔔 Suara; grup Perlu perhatian (Darurat/Bot gagal + lama menunggu) → Ditangani operator → Bot menangani (dilipat)
- Header chat menjelaskan alasan perhatian (kata kunci, template IGD terkirim)
- Bar status: Tandai sudah dicek + Ambil alih; saat takeover: hitung mundur lepas otomatis + Kembalikan ke bot
- Template balasan cepat & input hanya muncul saat diambil alih; selain itu kotak balas terkunci

### Prompt & Info RS — Opsi 1 Editor Tab
- Tab System Prompt (`prompts/system.md`) / Info RS (`kb/info_rs.md`), editor monospace, Batal/Simpan
- Baris status: terakhir disimpan oleh siapa + jumlah karakter / topik
- Panel kanan Cadangan: Lihat / Pulihkan, "Tampilkan N lainnya"

### Coba Bot — Opsi 2 Chat + Inspektur
- Bar lingkungan: SIMRS mock/live, model + temperature, versi system.md & info_rs.md, "Tercatat di Log sebagai simulasi"
- Chat simulasi + Mulai ulang; klik jawaban bot → inspektur langkah (filter darurat → LLM #1 pilih tool → SIMRS + JSON → LLM #2), waktu & token per langkah
- Cek data (anti-halusinasi) atau Cek guardrail; Jadikan kasus uji, Salin JSON

### Perangkat — Opsi 4 Daftar + Detail
- Daftar perangkat kiri + "+ Tambah perangkat"; detail kanan: status + Hubungkan, KPI (pesan hari ini, pesan terakhir, terputus N×/7 hari), riwayat koneksi, zona bahaya Putuskan…

### Log — Opsi 1 Tabel
- Tab Log Pesan / Log Aktivitas (dengan jumlah), label "🔒 hanya baca · retensi 30 hari"
- Filter tanggal, perangkat, status, tool; tabel berhalaman; nomor tampil sebagai potongan hash (#a91f)
- Status pesan: OK = hijau, Error = merah, Cache = amber

### Pengguna — Opsi 1 Tabel + Modal
- Ringkasan jumlah pengguna/aktif; tabel nama, username, status (Aktif/Baru/Terkunci/Nonaktif), login terakhir
- Modal tambah: nama, username, password, ulangi password
- Aksi: Reset password, Nonaktifkan/Aktifkan; tanpa hapus; akun sendiri tidak bisa dinonaktifkan

## Interaction Patterns
- Live update (HTMX polling/SSE) untuk daftar chat dan pesan
- Takeover = toggle eksplisit; kotak balas terkunci selama bot aktif
- Log hanya baca

## Content Hierarchy
- Pengirim pesan dibedakan: pasien (kiri), bot (kanan, abu), operator (kanan, bergaris tegas + nama)
- Pesan bot menampilkan chip tool yang dipanggil (mis. `get_jadwal_dokter`)
- Badge perangkat (Info Publik / Hotline IGD / CS Poli) dan badge status

## Screenshot Observations
- Belum ada aplikasi; acuan visual = prototype klik-able di `wireframe/prototype/`

## UX Conventions
- Bahasa antarmuka: Indonesia
- Data contoh: dummy (nomor, nama operator Sari/Budi, perangkat Info Publik/Hotline IGD/CS Poli)
- Hotline IGD contoh: (0357) 881410 (dummy)

## Desain Terpilih (23 Okt 2026)
- Dashboard: Opsi 1 Kartu & Grafik
- Live Chats: Opsi 2 Antrean Prioritas
- Prompt & Info RS: Opsi 1 Editor Tab
- Coba Bot: Opsi 2 Chat + Inspektur
- Perangkat: Opsi 4 Daftar + Detail
- Log: Opsi 1 Tabel
- Pengguna: Opsi 1 Tabel + Modal
- Palet varian: teal (#0f766e) di atas slate, IBM Plex Sans/Mono

## Prototype (25 Okt 2026)
- Folder `wireframe/prototype/`, dibuka dari `index.html` (Login). File HTML kini menjadi sumber utama (folder wireframe `2310-*` sudah dihapus, jadi `build.py` tidak bisa dijalankan ulang)
- Shell prototype (bar atas, login) di `prototype.css`; tampilan konten semua halaman di `app.css`
