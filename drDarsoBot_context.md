# drDarsoBot — Context Aplikasi
Chatbot Layanan Informasi RSUD dr. Darsono Pacitan Berbasis WhatsApp

> Versi sederhana (revisi). Prototype klik-able admin console ada di `wireframe/prototype/` (mulai dari `index.html` = halaman Login); isinya dirakit dari opsi wireframe terpilih dan menjadi acuan bagian 7.
> Seluruh contoh data (nama dokter, ruang, tarif, lokasi, nomor telepon) adalah **data dummy** dan wajib diganti data resmi RSUD.

---

## 1. Ringkasan & Tujuan Aplikasi

**drDarsoBot** adalah chatbot berbasis WhatsApp yang memberikan informasi layanan RSUD dr. Darsono Pacitan secara otomatis kepada masyarakat umum, tanpa syarat kepesertaan tertentu (berbeda dari jadwal dokter yang saat ini hanya bisa dicek lewat Mobile JKN) dan tanpa perlu instalasi aplikasi tambahan.

Tujuan utama aplikasi:
1. Menyediakan informasi umum rumah sakit (profil, layanan, fasilitas, jam operasional) secara otomatis 24 jam.
2. Menyediakan informasi jadwal praktik dokter yang dapat diakses publik secara langsung via WhatsApp.
3. Menyediakan informasi ketersediaan kamar rawat inap yang lebih mendekati kondisi realtime dibanding website saat ini.
4. Mengurangi ketergantungan terhadap ketersediaan petugas dalam melayani pertanyaan repetitif, dengan tetap memungkinkan petugas mengambil alih percakapan (takeover) lewat web tanpa harus memegang HP.

---

## 2. Ruang Lingkup (Scope) & Batasan

**Termasuk dalam scope:**
- Informasi umum rumah sakit dari file Knowledge Base (Markdown)
- Informasi jadwal praktik dokter (nama dokter, poli, hari, jam praktik) dari SIMRS
- Informasi ketersediaan kamar rawat inap (kelas, ruangan, tersedia, total) secara agregat dari SIMRS
- Pemahaman maksud pertanyaan oleh LLM melalui **function calling** (termasuk 2 tool sekaligus dan pertanyaan lanjutan multi-turn)
- Lebih dari satu nomor WhatsApp; **semua nomor diperlakukan sama** (prompt, tool, dan aturan yang sama)
- Live Chats berbasis web: operator membaca percakapan, mengambil alih (takeover), membalas, dan mengembalikan ke bot
- Admin console sederhana (lihat bagian 7)

**Di luar scope (batasan):**
- Tidak melayani diagnosa medis, vonis penyakit, maupun rekomendasi/resep obat
- Tidak menangani kegawatdaruratan langsung (diarahkan ke IGD 24 Jam)
- Tidak menangani transaksi (booking kamar, pendaftaran, pembayaran) maupun pengaduan
- Tidak menggantikan Mobile JKN untuk pendaftaran resmi BPJS
- Tidak menampilkan data rekam medis atau data pribadi pasien
- Hanya Bahasa Indonesia (dengan tutur santun lokal Pacitan) dan hanya WhatsApp
- Tidak ada pembagian role, pengaturan per nomor, maupun pengaturan sistem lewat web

---

## 3. Arsitektur Sistem

```
Pasien (WhatsApp, nomor A/B/C)
      │
      ▼
GOWA (go-whatsapp-web-multidevice, Docker, multi-device)
      │  webhook POST + X-Hub-Signature-256 (HMAC-SHA256)
      ▼
Backend drDarsoBot (Python/FastAPI)
      │
      ├─ Kata kunci darurat? ──► balasan IGD langsung (tanpa LLM)
      ├─ Sedang di-takeover?  ──► simpan saja, tampil di Live Chats
      ▼
LLM (API kompatibel OpenAI, default Gemini) + function calling
      │                 │                        │
      ▼                 ▼                        ▼
get_jadwal_dokter  get_ketersediaan_kamar   get_info_rs
(API SIMRS)        (API SIMRS)              (file kb/info_rs.md)
      └─────────────────┴──── hasil tool ───────┘
                          │
                          ▼
     LLM menyusun jawaban → GOWA REST API (X-Device-Id) → Pasien
```

Balasan selalu dikirim lewat perangkat (nomor) yang menerima pesan. Data jadwal & kamar diambil dari API SIMRS dengan cache singkat di memori; info umum diambil dari file Markdown.

> **Catatan risiko platform:** GOWA bukan API resmi Meta, sehingga ada risiko nomor diblokir. Alternatif resmi adalah WhatsApp Business Cloud API. GOWA dipilih karena mendukung banyak nomor, tanpa biaya per percakapan, dan dapat di-host mandiri; risiko ini dicatat sebagai batasan penelitian.

---

## 4. Tech Stack

| Komponen | Pilihan | Keterangan |
| --- | --- | --- |
| Bahasa | Python 3.11+ | |
| Backend | FastAPI | Async, webhook & panggilan API |
| Gateway WhatsApp | GOWA | Multi-device, webhook HMAC |
| LLM | API kompatibel OpenAI, default `gemini-2.5-flash` | Function calling, temperature 0.1–0.3 |
| Knowledge Base | File Markdown (`kb/info_rs.md`) | Dibagi per heading `##`; **tanpa RAG/embedding** |
| Database | SQLite | Users, percakapan, takeover, log (bagian 8) |
| Cache | Dict di memori + TTL | Hilang saat restart, tidak masalah |
| Konfigurasi sistem | File `.env` | Tidak bisa diubah lewat web |
| Admin console | FastAPI + Jinja2 (+ HTMX untuk Live Chats) | Halaman minimal |
| Deployment | Docker Compose (backend + GOWA) + Nginx HTTPS | GOWA hanya di jaringan internal Docker |

---

## 5. Alur Percakapan

```
Pesan masuk (webhook GOWA)
   │
   ├─ Verifikasi signature, buang duplikat (payload.id), abaikan is_from_me
   ├─ Nomor ada di BLOCKED_NUMBERS / melebihi rate limit? → abaikan
   ├─ Simpan ke tabel percakapan
   ├─ Mengandung kata kunci darurat? → kirim template IGD 24 Jam (tanpa LLM)
   ├─ Percakapan sedang di-takeover? → berhenti (operator yang membalas)
   ▼
LLM + system prompt + KB topik + riwayat N pesan terakhir
   │
   ├─ Minta obat/diagnosa atau transaksi → tolak santun, arahkan ke poli/admisi
   └─ Pertanyaan informasi → panggil tool (1 atau 2 sekaligus)
           ▼
   Hasil tool → LLM menyusun jawaban → kirim via GOWA → catat message_log
```

**Penanganan gagal:**
- API SIMRS gagal/timeout → pakai cache terakhir bila ada (dengan catatan "data mungkin belum terbaru"), jika tidak ada arahkan ke loket pendaftaran (jadwal) atau admisi (kamar).
- API LLM gagal/timeout → kirim pesan cadangan tetap (mohon maaf + kontak bagian informasi RS), status `error` di log.

**Takeover:**
- Operator menekan "Ambil alih" di Live Chats → bot berhenti membalas nomor tersebut, operator membalas dari web (dikirim lewat nomor/perangkat yang sama).
- Operator menekan "Kembalikan ke bot", atau otomatis dilepas setelah `TAKEOVER_TIMEOUT_MENIT` tanpa aktivitas operator.

---

## 6. Tool LLM & Integrasi API SIMRS

| Tool | Sumber | Parameter |
| --- | --- | --- |
| `get_jadwal_dokter(poli?, dokter?, hari?)` | `GET /api/jadwal-dokter` | semua opsional |
| `get_ketersediaan_kamar(kelas_kamar?)` | `GET /api/kamar/ketersediaan` | opsional |
| `get_info_rs(topik)` | Bagian `## <topik>` di `kb/info_rs.md` | `topik` wajib, enum dari daftar heading |

Daftar tool ditulis langsung di kode (bukan di database).

Contoh response SIMRS (usulan):
- Jadwal: `{"dokter":"dr. X", "poli":"Anak", "hari":"Senin", "jam":"08:00-12:00"}`
- Kamar: `{"kelas":"VIP", "ruang":"...", "tersedia":2, "total":5}`

**Catatan teknis:**
- Format JSON; otentikasi `X-API-KEY`/Bearer dari `.env`.
- Timeout 5 detik. Cache di memori: jadwal 5 menit, kamar 2 menit.
- Hanya data publik/agregat.
- Selama endpoint SIMRS belum tersedia, backend memakai **mock SIMRS** (data dummy tetap) yang dipilih lewat `SIMRS_MODE=mock|live`. Pengujian otomatis selalu memakai mock.

---

## 7. Admin Console (Minimal)

Semua pengguna punya hak akses yang sama (tanpa role).

Halaman **Login** (username + password, tombol Masuk → Dashboard) berada di luar menu; akun terkunci 15 menit setelah 5× salah password.

Tata letak: **menu horizontal di bar atas** (bukan sidebar) — logo "drDarsoBot · Admin Console" di kiri, tujuh menu di tengah (menu aktif bergaris bawah), lalu nama user, **Ganti Password**, **Logout** di kanan. Konten tiap menu memenuhi sisa layar.

| # | Menu (file prototype) | Desain terpilih | Fungsi |
| --- | --- | --- | --- |
| 0 | **Dashboard** (halaman awal) `dashboard.html` | Opsi 1 — Kartu & Grafik | Filter rentang (Hari ini / 7 hari / 30 hari) & perangkat, keterangan "Diperbarui HH:MM · otomatis tiap 30 dtk". **Kartu angka:** Pesan masuk (dengan perbandingan vs hari yang sama minggu lalu), Dijawab bot (dengan persentase), Dibalas operator, Takeover aktif (nama operatornya), Error (rincian per sumber, mis. "3 SIMRS · 1 LLM"; kartu merah). **Grafik batang** pesan per hari (7 hari, hari ini disorot). **Pemakaian tool** per tool termasuk "tanpa tool" + rata-rata latency. **Status perangkat** (label, nomor, Terhubung/Terputus, pesan terakhir / terputus sejak; tombol **Hubungkan** → menu Perangkat). **Error terakhir** (jam, sumber, penyebab + tool, nomor disamarkan `0857-****-2231`; tautan **Lihat di Log →**). Dihitung dari tabel yang ada; data `simulasi` tidak dihitung |
| 1 | **Live Chats** `live-chats.html` | Opsi 2 — Antrean Prioritas | Dua panel: daftar chat (kiri) dan percakapan (kanan). **Daftar:** cari nomor WA, toggle **🔔 Suara** (bunyi saat ada chat darurat), dikelompokkan **Perlu perhatian** (badge Darurat / Bot gagal) → **Ditangani operator** (badge "Anda" atau nama operator) → **Bot menangani** (dilipat, "tampilkan"). Tiap item: nomor, jam, cuplikan pesan terakhir, badge perangkat, lama menunggu ("menunggu 2 mnt"), jumlah belum dibaca. **Header chat:** nomor, badge perangkat & status, alasan perhatian (mis. `Kata kunci: "sesak nafas" · template IGD terkirim 10:40`). **Bar status:** saat bot aktif → "Bot sedang menangani" + **Tandai sudah dicek** + **Ambil alih**; saat diambil alih → "Anda mengambil alih · lepas otomatis dalam 29:41" + **Kembalikan ke bot**, dan baris sistem "Sari (Anda) mengambil alih · 10:43" di percakapan. Pesan bot menampilkan chip tool (`get_info_rs(topik: "BPJS")` atau `filter darurat · tanpa LLM`). Kotak balas terkunci selama bot menangani; saat diambil alih muncul **template balasan cepat** (Salam pembuka, Arahkan ke IGD, Arahkan ke admisi, Penutup) dan input + Kirim (Enter) |
| 2 | **Prompt & Info RS** `prompt.html` | Opsi 1 — Editor Tab | Tab **System Prompt** (`prompts/system.md`, heading `#` Persona/Aturan/Batasan/Contoh) dan **Info RS** (`kb/info_rs.md`, heading `##` = topik `get_info_rs`): editor monospace + Batal/Simpan. Baris status: terakhir disimpan (tanggal, jam, oleh siapa) + jumlah karakter (System Prompt) atau jumlah topik (Info RS). Panel kanan **Cadangan** (`*.YYYYMMDD-HHMMSS.bak`, terbaru di atas, 3 ditampilkan + "Tampilkan N lainnya"): waktu, pengguna, nama file, **Lihat** & **Pulihkan** (isi saat ini dicadangkan dulu). Simpan & pulihkan dicatat di activity log; berlaku untuk pesan berikutnya tanpa restart |
| 3 | **Coba Bot** `coba-bot.html` | Opsi 2 — Chat + Inspektur | **Bar lingkungan:** mode SIMRS (mock/live), model + temperature, versi `system.md` & `info_rs.md`, keterangan "Tercatat di Log sebagai simulasi". **Chat simulasi** (alur bot yang sama, tanpa kirim WA, mendukung pertanyaan lanjutan) dengan tombol **Mulai ulang**; tiap jawaban bot menampilkan chip tool, waktu, dan "klik untuk detail". Klik jawaban → panel **inspektur** "Proses jawaban" (total waktu & token): filter darurat → LLM #1 pilih tool + argumen → SIMRS (endpoint, waktu, cache hit/miss, hasil JSON dapat dibuka) → LLM #2 susun jawaban, dengan waktu & token per langkah. **Cek data** otomatis (nama dokter/jam/jumlah bed ada di hasil tool) atau **Cek guardrail** untuk jawaban tanpa tool (tidak menyebut obat, mengarahkan ke poli/IGD). Tombol **Jadikan kasus uji** (menambah ke `tests/kasus_uji.yaml`) dan **Salin JSON**. Tercatat di `message_log` dengan `device_id = "simulasi"` |
| 4 | **Perangkat** `perangkat.html` | Opsi 4 — Daftar + Detail | Daftar perangkat di kiri (titik status, label, nomor) + **+ Tambah perangkat**. Detail di kanan: label, nomor, `device_id`, status (Terhubung/Terputus) + tombol **Hubungkan** (QR); angka **Pesan hari ini**, **Pesan terakhir**, **Terputus N× / 7 hari**; **Riwayat koneksi** (waktu, terhubung/terputus, keterangan mis. "logout dari HP", "HP mati", atau "Terhubung oleh Sari"); zona bahaya **Putuskan perangkat…** (dengan konfirmasi; nomor harus dipindai ulang) |
| 5 | **Log** `log.html` | Opsi 1 — Tabel | Tab **Log Pesan** dan **Log Aktivitas** (dengan jumlah baris), label "🔒 hanya baca · retensi N hari". **Log Pesan:** filter tanggal, perangkat, status (OK/Error/Cache), tool; kolom Waktu, Perangkat, Nomor (potongan hash, mis. `#a91f`), Pesan, Tool + argumen (atau "filter darurat" / "—"), Status, Latency; tabel berhalaman. **Log Aktivitas:** kolom Waktu, Pengguna, Aksi, Detail (mis. nomor disamarkan + perangkat untuk takeover, nama file + ringkasan untuk simpan prompt/KB, alamat IP untuk login). **Hanya baca** — tidak ada tombol hapus/edit |
| 6 | **Pengguna** `pengguna.html` | Opsi 1 — Tabel + Modal | Ringkasan "N pengguna · N aktif". Tabel (nama, username, status Aktif/Baru/Terkunci/Nonaktif, login terakhir); baris akun sendiri ditandai "(Anda)", baris nonaktif diredupkan. **+ Tambah pengguna** lewat modal: nama lengkap, username (huruf kecil, tanpa spasi), password (min. 8 karakter), ulangi password. Aksi per baris: **Reset password**, **Nonaktifkan** / **Aktifkan**. Tidak ada hapus (agar activity log tetap utuh); akun sendiri tidak bisa dinonaktifkan (hanya Reset password) |

Tidak ada menu Pengaturan; semua konfigurasi di `.env`.

---

## 8. Struktur Data

### Database (SQLite)

| Tabel | Kolom Utama | Fungsi |
| --- | --- | --- |
| `users` | id, nama, username, password_hash, aktif, gagal_login, terkunci_sampai, login_terakhir, created_at | Akun admin console; status Baru = belum pernah login, Terkunci = `terkunci_sampai` > sekarang |
| `percakapan` | id, device_id, nomor_wa, pesan, arah (masuk/keluar), pengirim (pasien/bot/operator), user_id?, timestamp | Riwayat chat & Live Chats |
| `takeover` | id, device_id, nomor_wa, user_id, mulai, selesai | Status pengambilalihan |
| `perhatian` | id, device_id, nomor_wa, jenis (darurat/bot_gagal), message_log_id, dibuat, dicek_oleh?, dicek_at? | Kelompok "Perlu perhatian" di Live Chats; selesai saat diambil alih atau ditandai sudah dicek |
| `message_log` | id, device_id, nomor_wa_hash, pesan, jawaban, model, tools, tokens, latency_ms, status (ok/error/cache), detail_json, timestamp | Evaluasi bot (append-only). `detail_json` = langkah proses, argumen & hasil tool, waktu per langkah, versi prompt — dipakai inspektur Coba Bot |
| `device_events` | id, device_id, event (terhubung/terputus), keterangan, user_id?, timestamp | Riwayat koneksi di menu Perangkat (append-only) |
| `activity_log` | id, user_id, aksi, detail, timestamp | Login (detail berisi alamat IP), takeover, tandai dicek, simpan/pulihkan prompt & KB, hubungkan/putuskan perangkat, kelola user (append-only) |

`message_log` dan `activity_log` tidak bisa dihapus/diubah dari frontend; penghapusan hanya oleh job retensi otomatis sesuai `LOG_RETENSI_HARI` (0 = tidak pernah dihapus).

Sesi login memakai cookie bertanda tangan (`SECRET_KEY`), tanpa tabel sesi.

### File

| File | Isi |
| --- | --- |
| `prompts/system.md` | System prompt (persona, aturan, guardrail) — editable via web |
| `kb/info_rs.md` | Info umum RS, dipisah per heading `##` — editable via web |
| `tests/kasus_uji.yaml` | Bank kasus uji (pesan, riwayat, tool & argumen yang diharapkan) — bisa ditambah dari Coba Bot |
| `prompts/balasan_cepat.yaml` | Template balasan cepat operator di Live Chats (diedit langsung di file) |
| `.env` | Konfigurasi sistem |

### Variabel `.env` (utama)

| Kelompok | Variabel |
| --- | --- |
| LLM | `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_TIMEOUT`, `RIWAYAT_N_PESAN` |
| SIMRS | `SIMRS_MODE`, `SIMRS_BASE_URL`, `SIMRS_API_KEY`, `CACHE_JADWAL_DETIK`, `CACHE_KAMAR_DETIK` |
| GOWA | `GOWA_BASE_URL`, `GOWA_BASIC_AUTH`, `WHATSAPP_WEBHOOK_SECRET`, `DEVICE_LABELS` (mis. `info:Info Publik,igd:Hotline IGD`) |
| Bot | `RATE_LIMIT_PER_MENIT`, `BLOCKED_NUMBERS`, `TAKEOVER_TIMEOUT_MENIT`, `HOTLINE_IGD`, `KATA_KUNCI_DARURAT` |
| Aplikasi | `SECRET_KEY`, `LOG_RETENSI_HARI`, `ADMIN_AWAL_USERNAME`, `ADMIN_AWAL_PASSWORD` |

---

## 9. Rencana Pengembangan

1. **Dasar** — Webhook GOWA (HMAC, dedup), simpan percakapan, balas via GOWA, multi-nomor
2. **Bot** — System prompt, 3 tool, mock SIMRS, cache, filter darurat, pesan cadangan
3. **Admin console** — Login, Dashboard, Live Chats + takeover, Prompt & Info RS (cadangan/pulihkan), Coba Bot, Perangkat, Log, Pengguna
4. **Pengujian** — Script bank kasus uji, black box, UAT
5. **Integrasi & Deployment** — Hubungkan ke API SIMRS asli (jika tersedia), Docker Compose + Nginx

---

## 10. Rencana Pengujian

| Jenis | Metode | Fokus |
| --- | --- | --- |
| Black Box | Skenario input-output per fitur | Info RS, jadwal, kamar, takeover, admin console |
| Ketepatan Pemilihan Tool | Script menjalankan `kasus_uji.yaml`; confusion matrix, precision, recall, F1 | Termasuk multi-tool & pertanyaan lanjutan; juga cek kesesuaian nama dokter/jam/jumlah bed dengan data mock (anti-halusinasi) |
| Guardrail & Triase IGD | Kasus minta obat/diagnosa, keluhan darurat, transaksi, API gagal | Nol diagnosa, hotline IGD muncul pada kasus darurat |
| UAT | Uji coba oleh staf/pasien terbatas + kuesioner | Kemudahan & kepuasan, termasuk penilaian gaya tutur |

Bank kasus uji dijalankan ulang setiap kali prompt atau model diubah.

---

## 11. Keamanan & Privasi

- Webhook diverifikasi `X-Hub-Signature-256` (HMAC-SHA256, constant-time); salah → `401`. Duplikat diabaikan berdasarkan `payload.id`.
- REST API GOWA dilindungi Basic Auth dan hanya diakses dari jaringan internal Docker.
- Semua kredensial di `.env`, tidak di-hardcode dan tidak pernah dicatat di log.
- Nomor WA di `message_log` di-hash; nomor lengkap hanya di `percakapan` (dibutuhkan untuk membalas).
- Password di-hash (bcrypt/argon2); akun terkunci 15 menit setelah 5 kali gagal login (`gagal_login`, `terkunci_sampai`).
- Rate limit per nomor (default 10 pesan/menit) dan daftar nomor diblokir di `.env`.

---

## 12. Etika Medis, Guardrail & Gaya Komunikasi

1. **Dilarang Diagnosa Medis:** tidak menebak penyakit, memvonis keluhan, atau menyarankan obat; keluhan gejala diarahkan ke Poliklinik Rawat Jalan / periksa ke dokter.
2. **Protokol Darurat IGD 24 Jam:** kata kunci darurat (sesak nafas, nyeri dada hebat, pendarahan, penurunan kesadaran, luka bakar parah) dideteksi **sebelum LLM** dan langsung dibalas template berisi `HOTLINE_IGD` dan lokasi IGD.
3. **Gaya Natural CS Pacitan (Tanpa Menu Angka):** tidak ada format "ketik 1/2"; percakapan ramah, empatik, santun (*ngajeni*, "Bapak/Ibu", "nggih", "matur nuwun").
4. **Anti-Halusinasi:** nama dokter, jam praktik, dan jumlah bed hanya dari hasil tool; contoh dialog di prompt memakai placeholder. Bila tidak ditemukan, sampaikan belum tersedia dan arahkan ke bagian informasi RS.
