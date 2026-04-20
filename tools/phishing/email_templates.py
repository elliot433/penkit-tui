"""
Email-Templates für Phishing-Kampagnen.

Jedes Template:
  - Sieht aus wie eine echte Benachrichtigung (Google/Microsoft/Bank/IT-Abteilung)
  - Enthält einen überzeugenden Grund zu klicken
  - {{PHISH_URL}} wird durch den echten Link ersetzt
  - {{NAME}} optional personalisierbar
"""

from __future__ import annotations


TEMPLATES: dict[str, dict] = {

    "google_security": {
        "subject": "Sicherheitswarnung: Neuer Anmeldeversuch bei Ihrem Google-Konto",
        "from_name": "Google",
        "body_html": """\
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px">
  <div style="text-align:center;margin-bottom:24px">
    <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_160x56dp.png" height="30" alt="Google">
  </div>
  <div style="background:#fff;border:1px solid #e0e0e0;padding:32px;border-radius:4px">
    <h2 style="color:#202124;font-weight:400">Sicherheitswarnung</h2>
    <p style="color:#5f6368;line-height:1.6">
      Hallo {{NAME}},<br><br>
      Wir haben einen neuen Anmeldeversuch bei Ihrem Google-Konto festgestellt.
    </p>
    <div style="background:#f8f9fa;border:1px solid #e0e0e0;padding:16px;margin:20px 0;border-radius:4px">
      <p style="margin:4px 0;color:#333"><strong>Gerät:</strong> Windows-PC</p>
      <p style="margin:4px 0;color:#333"><strong>Standort:</strong> Deutschland</p>
      <p style="margin:4px 0;color:#333"><strong>Zeit:</strong> Heute, {{TIME}} Uhr</p>
    </div>
    <p style="color:#5f6368">Wenn Sie das nicht waren, sichern Sie sofort Ihr Konto:</p>
    <div style="text-align:center;margin:28px 0">
      <a href="{{PHISH_URL}}" style="background:#1a73e8;color:#fff;padding:12px 28px;border-radius:4px;text-decoration:none;font-weight:500">
        Konto jetzt sichern
      </a>
    </div>
    <p style="color:#9aa0a6;font-size:12px">
      Wenn Sie sich selbst angemeldet haben, können Sie diese E-Mail ignorieren.
    </p>
  </div>
  <p style="text-align:center;color:#9aa0a6;font-size:11px;margin-top:20px">
    © 2024 Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA 94043
  </p>
</body></html>""",
    },

    "microsoft_mfa": {
        "subject": "Aktion erforderlich: Verifizieren Sie Ihr Microsoft-Konto",
        "from_name": "Microsoft-Kontoteam",
        "body_html": """\
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:auto">
  <div style="background:#0067b8;padding:16px 24px">
    <img src="https://c.s-microsoft.com/en-us/CMSImages/mslogo.png" height="20" alt="Microsoft">
  </div>
  <div style="padding:32px;background:#fff;border:1px solid #e0e0e0">
    <h1 style="font-size:22px;color:#1b1b1b;font-weight:600">Konto-Verifizierung erforderlich</h1>
    <p style="color:#333;line-height:1.6;margin:16px 0">
      Liebe/r {{NAME}},<br><br>
      Zur Sicherheit Ihres Microsoft-Kontos müssen Sie Ihre Identität bestätigen.
      Ihr Konto wird in <strong>24 Stunden gesperrt</strong>, wenn Sie keine Aktion durchführen.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{{PHISH_URL}}" style="background:#0067b8;color:#fff;padding:13px 32px;text-decoration:none;font-size:15px;font-weight:600">
        Jetzt verifizieren
      </a>
    </div>
    <p style="color:#666;font-size:13px">
      Falls Sie diese E-Mail nicht angefordert haben, wenden Sie sich an den Support.
    </p>
  </div>
  <div style="padding:16px;background:#f4f4f4;font-size:11px;color:#888;text-align:center">
    Microsoft Corporation · One Microsoft Way · Redmond, WA 98052
  </div>
</body></html>""",
    },

    "instagram_login": {
        "subject": "Jemand hat versucht, sich bei Instagram anzumelden",
        "from_name": "Instagram",
        "body_html": """\
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,Arial,sans-serif;max-width:500px;margin:auto;padding:20px">
  <div style="text-align:center;padding:28px 0">
    <span style="font-family:Billabong,cursive;font-size:36px">Instagram</span>
  </div>
  <div style="border:1px solid #dbdbdb;padding:32px;text-align:center">
    <p style="font-size:18px;font-weight:600;margin-bottom:16px">Haben Sie versucht, sich anzumelden?</p>
    <p style="color:#555;font-size:14px;line-height:1.6;margin-bottom:24px">
      Wir haben einen Anmeldeversuch von einem unbekannten Gerät festgestellt.<br>
      Wenn Sie das nicht waren, sichern Sie Ihr Konto jetzt.
    </p>
    <a href="{{PHISH_URL}}" style="background:#0095f6;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
      Konto sichern
    </a>
    <p style="margin-top:24px;font-size:13px;color:#888">
      Wenn Sie das waren, können Sie diese E-Mail ignorieren.
    </p>
  </div>
  <p style="text-align:center;font-size:11px;color:#aaa;margin-top:16px">
    Meta Platforms, Inc. · 1 Meta Way, Menlo Park, CA 94025
  </p>
</body></html>""",
    },

    "it_department": {
        "subject": "IT-Abteilung: Ihr Passwort läuft in 24h ab — jetzt erneuern",
        "from_name": "IT-Support",
        "body_html": """\
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
  <div style="background:#2c3e50;padding:16px 24px">
    <span style="color:#fff;font-size:18px;font-weight:bold">🔒 IT-Sicherheitsabteilung</span>
  </div>
  <div style="padding:32px;background:#fff;border:1px solid #ddd">
    <h2 style="color:#c0392b">⚠️ Passwort läuft ab</h2>
    <p style="color:#333;line-height:1.6;margin:16px 0">
      Sehr geehrte/r {{NAME}},<br><br>
      Ihr Unternehmens-Passwort läuft in <strong>24 Stunden</strong> ab.
      Bitte erneuern Sie es umgehend, um einen Zugriffsverlust zu vermeiden.
    </p>
    <div style="background:#fff3cd;border:1px solid #ffc107;padding:12px;border-radius:4px;margin:16px 0">
      <strong>Wichtig:</strong> Nach Ablauf müssen Sie sich persönlich beim IT-Support melden.
    </div>
    <div style="text-align:center;margin:28px 0">
      <a href="{{PHISH_URL}}" style="background:#2c3e50;color:#fff;padding:13px 32px;text-decoration:none;font-weight:bold;border-radius:3px">
        Passwort jetzt erneuern
      </a>
    </div>
    <p style="color:#888;font-size:12px">
      Bei Fragen wenden Sie sich an it-support@{{DOMAIN}} oder rufen Sie 0800-IT-HELP an.
    </p>
  </div>
</body></html>""",
    },

    "bank_suspicious": {
        "subject": "Dringlich: Ungewöhnliche Aktivität auf Ihrem Konto festgestellt",
        "from_name": "SecureBank Sicherheitsteam",
        "body_html": """\
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
  <div style="background:#004a97;padding:16px 24px">
    <span style="color:#fff;font-size:20px;font-weight:bold">SecureBank</span>
    <span style="color:#aad4ff;font-size:12px;margin-left:12px">Sicherheitsteam</span>
  </div>
  <div style="padding:32px;background:#fff;border:1px solid #ddd">
    <h2 style="color:#c0392b">⚠️ Sicherheitswarnung</h2>
    <p style="color:#333;line-height:1.6">
      Sehr geehrte/r Kunde/in,<br><br>
      Auf Ihrem Konto wurde eine verdächtige Transaktion festgestellt.
      Zur Sicherheit wurde Ihr Konto vorübergehend eingeschränkt.
    </p>
    <div style="background:#f8f9fa;border:1px solid #dee2e6;padding:16px;margin:20px 0">
      <p style="margin:4px 0"><strong>Betrag:</strong> 1.247,50 €</p>
      <p style="margin:4px 0"><strong>Empfänger:</strong> Unbekanntes Konto</p>
      <p style="margin:4px 0"><strong>Status:</strong> <span style="color:#c0392b">Ausstehend — Verifizierung erforderlich</span></p>
    </div>
    <div style="text-align:center;margin:28px 0">
      <a href="{{PHISH_URL}}" style="background:#004a97;color:#fff;padding:13px 32px;text-decoration:none;font-weight:bold;border-radius:3px">
        Konto jetzt verifizieren
      </a>
    </div>
    <p style="color:#888;font-size:12px">
      Ohne Verifizierung innerhalb von 48h wird Ihr Konto gesperrt.
    </p>
  </div>
</body></html>""",
    },
}


def render_template(
    name: str,
    phish_url: str,
    target_name: str = "Nutzer",
    domain: str = "example.com",
) -> tuple[str, str, str]:
    """
    Returns (subject, from_name, html_body) with placeholders replaced.
    """
    import datetime
    t = TEMPLATES.get(name, TEMPLATES["google_security"])
    now = datetime.datetime.now().strftime("%H:%M")
    html = (
        t["body_html"]
        .replace("{{PHISH_URL}}", phish_url)
        .replace("{{NAME}}", target_name)
        .replace("{{TIME}}", now)
        .replace("{{DOMAIN}}", domain)
    )
    return t["subject"], t["from_name"], html
