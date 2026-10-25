"""Rakit prototype klik-able dari opsi wireframe yang dipilih.

Jalankan ulang setelah wireframe sumber berubah:
    python3 wireframe/prototype/build.py
"""
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# slug file, judul, folder sumber, nomor opsi terpilih
PAGES = [
    ("dashboard", "Dashboard", "2310-dashboard", 1),
    ("live-chats", "Live Chats", "2310-live-chats", 2),
    ("prompt", "Prompt & Info RS", "2310-prompt-info-rs", 1),
    ("coba-bot", "Coba Bot", "2310-coba-bot", 2),
    ("perangkat", "Perangkat", "2310-perangkat", 4),
    ("log", "Log", "2310-log", 1),
    ("pengguna", "Pengguna", "2310-pengguna", 1),
]

# teks tautan di dalam konten → halaman tujuan
LINKS = {
    "dashboard": {"Hubungkan": "perangkat.html", "Lihat di Log →": "log.html"},
    "live-chats": {"Buka Perangkat": "perangkat.html"},
    "coba-bot": {},
}

def extract(folder, n):
    src = (ROOT / folder / "index.html").read_text(encoding="utf-8")
    start = src.index(f'id="frame-opt{n}"')
    start = src.index('<div class="browser-content">', start) + len('<div class="browser-content">')
    end = src.index('<div class="wf-annotations">', start)
    body = src[start:end]
    body = body[: body.rindex("</div>")]          # tutup .browser-frame
    body = body[: body.rindex("</div>")].strip()  # tutup .browser-content
    # navigasi bawaan tiap opsi diganti shell prototype
    body = re.sub(r'<div class="topnav">.*?</div>', "", body, flags=re.S)
    body = re.sub(r'<div class="appbar">.*?</div>', "", body, flags=re.S)
    body = re.sub(r'<nav class="side">.*?</nav>', "", body, flags=re.S)
    return body


def relink(body, slug):
    for text, target in LINKS.get(slug, {}).items():
        body = re.sub(r'<a href="#"([^>]*)>' + re.escape(text) + "</a>",
                      lambda m: f'<a href="{target}"{m.group(1)}>{text}</a>', body)
    return body


def nav(active):
    items = "".join(
        f'<a href="{s}.html" class="{"on" if s == active else ""}">{html.escape(t)}</a>' for s, t, _, _ in PAGES
    )
    return f'''<header class="px-top"><div class="px-brand">drDarsoBot<small>Admin Console</small></div><nav>{items}</nav>
  <span class="px-user">Sari</span><a href="#">Ganti Password</a><a href="index.html">Logout</a></header>'''


def page(slug, title, folder, n):
    body = relink(extract(folder, n), slug)
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} — drDarsoBot</title>
<link rel="stylesheet" href="app.css">
<link rel="stylesheet" href="prototype.css">
</head>
<body class="px" data-mode="clean">
{nav(slug)}
<div class="px-main">
  <div id="frame-opt{n}" class="px-frame clean"><div class="browser-content">
{body}
  </div></div>
</div>
</body>
</html>
"""


LOGIN = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Masuk — drDarsoBot</title>
<link rel="stylesheet" href="prototype.css">
</head>
<body class="px px-login-page" data-mode="clean">
<form class="px-login" action="dashboard.html">
  <div class="px-brand">drDarsoBot<small>Admin Console · RSUD dr. Darsono Pacitan</small></div>
  <label>Username<input type="text" value="sari" autocomplete="username"></label>
  <label>Password<input type="password" value="rahasia123" autocomplete="current-password"></label>
  <button type="submit">Masuk</button>
  <p class="px-note">Prototype — klik Masuk untuk membuka Dashboard. Akun terkunci 15 menit setelah 5× salah password.</p>
</form>
</body>
</html>
"""


def main():
    (HERE / "index.html").write_text(LOGIN, encoding="utf-8")
    for slug, title, folder, n in PAGES:
        (HERE / f"{slug}.html").write_text(page(slug, title, folder, n), encoding="utf-8")
        print(f"{slug}.html  ← {folder} opsi {n}")


if __name__ == "__main__":
    main()
