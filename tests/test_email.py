"""
NexaCare — Test de diagnóstico de email
Lee credenciales desde .streamlit/secrets.toml (igual que la app)
Ejecuta: python test_email.py
"""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _leer_secrets():
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, ".streamlit", "secrets.toml")
    if os.path.exists(path):
        data = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    val = val.strip().strip('"').strip("'")
                    data[key.strip()] = val
        u = data.get("NEXACARE_GMAIL_USER", "").strip()
        p = data.get("NEXACARE_GMAIL_PASS", "").replace(" ", "").strip()
        return u, p, path
    return "", "", path

print("=" * 55)
print("NexaCare — Diagnóstico de email (secrets.toml)")
print("=" * 55)

GMAIL_USER, GMAIL_PASS, secrets_path = _leer_secrets()

print(f"\n1. Leyendo .streamlit/secrets.toml:")
print(f"   Ruta: {secrets_path}")
print(f"   NEXACARE_GMAIL_USER: {'✓ ' + GMAIL_USER if GMAIL_USER else '✗ NO ENCONTRADO'}")
print(f"   NEXACARE_GMAIL_PASS: {'✓ ' + str(len(GMAIL_PASS)) + ' caracteres' if GMAIL_PASS else '✗ NO ENCONTRADO'}")

if not GMAIL_USER or not GMAIL_PASS:
    print("\n✗ No se encontraron credenciales en secrets.toml")
    exit(1)

print(f"\n2. Formato contraseña:")
if len(GMAIL_PASS) == 16:
    print(f"   ✓ 16 caracteres (correcto)")
    print(f"   Contraseña (primeros 4): {GMAIL_PASS[:4]}...")
else:
    print(f"   ✗ {len(GMAIL_PASS)} caracteres (se esperan 16)")

print(f"\n3. Probando SMTP SSL (puerto 465)...")
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        print("   ✓ Login correcto con SSL")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NexaCare — Test desde secrets.toml ✓"
        msg["From"] = f"NexaCare <{GMAIL_USER}>"
        msg["To"] = GMAIL_USER
        msg.attach(MIMEText(
            "<h2 style='color:#3d8ef8;'>NexaCare</h2>"
            "<p>✅ Email funcionando desde secrets.toml</p>",
            "html", "utf-8"
        ))
        s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"   ✓ Email enviado a {GMAIL_USER}")
        print("\n✅ TODO OK — El sistema de email funciona correctamente.")
except smtplib.SMTPAuthenticationError as e:
    print(f"   ✗ Error de autenticación: {e.smtp_code} {e.smtp_error}")
    print("\n   La contraseña en secrets.toml es incorrecta.")
    print("   Genera una nueva en: myaccount.google.com → Seguridad → Contraseñas de aplicación")
    print("   Y actualiza .streamlit/secrets.toml con los 16 caracteres exactos.")
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")
