"""
NexaCare — Email profesional con PDF adjunto.
Variables: NEXACARE_GMAIL_USER / NEXACARE_GMAIL_PASS
"""
import os, re, smtplib, math
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

GMAIL_USER = os.environ.get("NEXACARE_GMAIL_USER", "")
GMAIL_PASS = os.environ.get("NEXACARE_GMAIL_PASS", "")

_NK = {
    "ROJO":     {"bg":"#1a0404","bdr":"#c0392b","txt":"#ff6b6b"},
    "NARANJA":  {"bg":"#1a0d04","bdr":"#c0621a","txt":"#ff9f5c"},
    "AMARILLO": {"bg":"#181404","bdr":"#b8860b","txt":"#f0c040"},
    "VERDE":    {"bg":"#04160a","bdr":"#1a8a4a","txt":"#5dd898"},
}

def _nk(nivel):
    for k in _NK:
        if k in nivel.upper(): return k
    return "VERDE"

def _barra(porcentaje, color):
    w = max(4, int(460 * porcentaje / 100))
    return (
        '<table cellpadding="0" cellspacing="0" width="100%">'
        '<tr><td style="height:7px;background:#0a1220;border-radius:4px;overflow:hidden;">'
        '<table cellpadding="0" cellspacing="0"><tr>'
        f'<td style="height:7px;width:{w}px;background:linear-gradient(90deg,#28b86e,{color});border-radius:4px;"></td>'
        '</tr></table></td></tr>'
        '<tr>'
        f'<td style="font-size:9px;color:#28b86e;text-align:left;padding-top:4px;">LEVE</td>'
        f'<td style="font-size:9px;color:#d4a020;text-align:center;padding-top:4px;">MODERADO</td>'
        f'<td style="font-size:9px;color:#e87228;text-align:center;padding-top:4px;">URGENTE</td>'
        f'<td style="font-size:9px;color:#e84040;text-align:right;padding-top:4px;">EMERGENCIA</td>'
        '</tr></table>'
    )

def _html(sintoma, nivel, emoji, porcentaje, recomendacion, que_hacer, informe_ai):
    nk  = _nk(nivel)
    col = _NK[nk]
    barra = _barra(porcentaje, col["txt"])

    pasos = ""
    for i, p in enumerate(que_hacer, 1):
        pasos += (
            f'<tr><td style="padding:6px 0;">'
            f'<table cellpadding="0" cellspacing="0"><tr>'
            f'<td style="width:26px;vertical-align:top;">'
            f'<span style="display:inline-block;width:20px;height:20px;border-radius:50%;'
            f'background:{col["bdr"]};text-align:center;line-height:20px;font-size:10px;'
            f'font-weight:800;color:#fff;">{i}</span></td>'
            f'<td style="font-size:13px;color:#b8cce0;line-height:1.6;padding-top:2px;">{p}</td>'
            f'</tr></table></td></tr>'
        )

    ia = ""
    if informe_ai:
        txt = informe_ai.replace("*","").replace("#","").strip()
        ia = (
            '<tr><td style="padding:0 0 20px;">'
            '<table cellpadding="0" cellspacing="0" width="100%"'
            ' style="background:#04101e;border-radius:10px;border:1px solid rgba(61,142,248,0.2);'
            'border-left:4px solid #3d8ef8;">'
            '<tr><td style="padding:14px 18px;">'
            '<div style="font-size:9px;font-weight:800;color:#3d8ef8;text-transform:uppercase;'
            'letter-spacing:2px;margin-bottom:10px;">Análisis NexaCare IA</div>'
            f'<div style="font-size:13px;color:#8aaccc;line-height:1.75;">{txt}</div>'
            '</td></tr></table></td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#030810;font-family:Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#030810;padding:20px 10px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
 style="max-width:600px;width:100%;border-radius:16px;overflow:hidden;border:1px solid #0e1e30;background:#0a1120;">

  <tr><td style="background:#0d1829;padding:18px 28px;border-bottom:1px solid #0e1e30;">
    <table cellpadding="0" cellspacing="0" width="100%"><tr>
      <td><div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
        Nexa<span style="color:#3d8ef8;">Care</span></div>
        <div style="font-size:9px;color:#1e3a58;margin-top:2px;letter-spacing:1.5px;">
        SISTEMA DE TRIAJE MÉDICO CON IA · TFG SMR 2025-2026</div></td>
      <td align="right"><span style="background:rgba(61,142,248,0.12);border:1px solid rgba(61,142,248,0.25);
        color:#3d8ef8;border-radius:20px;padding:5px 12px;font-size:9px;font-weight:700;letter-spacing:1px;">
        INFORME DE TRIAJE</span></td>
    </tr></table>
  </td></tr>

  <tr><td style="background:{col['bg']};padding:28px;text-align:center;border-bottom:4px solid {col['bdr']};">
    <div style="font-size:46px;line-height:1;margin-bottom:10px;">{emoji}</div>
    <div style="font-size:24px;font-weight:800;color:{col['txt']};letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">{nivel}</div>
    <div style="font-size:11px;color:{col['txt']};opacity:0.6;margin-bottom:18px;">Nivel de urgencia · {porcentaje}% de gravedad</div>
    <div style="padding:0 16px;">{barra}</div>
  </td></tr>

  <tr><td style="background:#060e1a;padding:22px 28px 0;">
    <table cellpadding="0" cellspacing="0" width="100%">

      <tr><td style="padding-bottom:18px;">
        <table cellpadding="0" cellspacing="0" width="100%"
         style="background:#0a1829;border-radius:10px;border:1px solid #0e1e30;border-left:4px solid {col['bdr']};">
          <tr><td style="padding:14px 18px;">
            <div style="font-size:8px;font-weight:800;color:#1e3a58;text-transform:uppercase;letter-spacing:2px;margin-bottom:5px;">SÍNTOMA PRINCIPAL</div>
            <div style="font-size:16px;font-weight:700;color:#dce8f6;">{sintoma}</div>
          </td></tr>
        </table>
      </td></tr>

      {ia}

      <tr><td style="padding-bottom:18px;">
        <div style="font-size:8px;font-weight:800;color:#1e3a58;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">RECOMENDACIÓN</div>
        <table cellpadding="0" cellspacing="0" width="100%"
         style="background:#0a1829;border-radius:10px;border:1px solid #0e1e30;">
          <tr><td style="padding:13px 18px;font-size:13px;color:#8aaccc;line-height:1.7;">{recomendacion}</td></tr>
        </table>
      </td></tr>

      <tr><td style="padding-bottom:18px;">
        <div style="font-size:8px;font-weight:800;color:#1e3a58;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">QUÉ HACER AHORA</div>
        <table cellpadding="0" cellspacing="0" width="100%">{pasos}</table>
      </td></tr>

      <tr><td style="padding-bottom:22px;">
        <table cellpadding="0" cellspacing="0" width="100%"
         style="background:#04101e;border:1px solid rgba(61,142,248,0.12);border-radius:10px;">
          <tr><td style="padding:12px 18px;font-size:12px;color:#2e4a66;line-height:1.6;">
            Se adjunta el <strong style="color:#3d8ef8;">informe completo en PDF</strong>. Puedes mostrárselo directamente a tu médico.
          </td></tr>
        </table>
      </td></tr>

    </table>
  </td></tr>

  <tr><td style="background:#030810;border-top:1px solid #0e1e30;padding:14px 28px;text-align:center;">
    <div style="font-size:10px;color:#1a3048;line-height:1.8;">
      NexaCare · Proyecto TFG/SMR · Pablo Esteban<br>
      Informe orientativo. No sustituye valoración médica.<br>
      <strong style="color:#6b1515;">Emergencias: 112</strong>
    </div>
  </td></tr>

</table>
</td></tr></table>
</body></html>"""

def _credenciales():
    # Leer secrets.toml directamente del disco (sin depender de st.secrets)
    _base = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_base, ".streamlit", "secrets.toml")
    if os.path.exists(_path):
        try:
            data = {}
            with open(_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, _, val = line.partition("=")
                        val = val.strip().strip('"').strip("'")
                        data[key.strip()] = val
            u = data.get("NEXACARE_GMAIL_USER", "").strip()
            p = data.get("NEXACARE_GMAIL_PASS", "").replace(" ", "").strip()
            if u and p:
                return u, p
        except Exception:
            pass
    # Fallback: variables de entorno
    u = os.environ.get("NEXACARE_GMAIL_USER", GMAIL_USER).strip()
    p = os.environ.get("NEXACARE_GMAIL_PASS", GMAIL_PASS).replace(" ", "").strip()
    return u, p

def enviar_informe(destinatario, sintoma, nivel, emoji, porcentaje, recomendacion, que_hacer, pdf_bytes, informe_ai=None):
    if not destinatario or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", destinatario.strip()):
        return False, "Dirección de correo no válida"

    gmail_user, gmail_pass = _credenciales()

    if not gmail_user or not gmail_pass:
        return False, "Credenciales no configuradas (NEXACARE_GMAIL_USER / NEXACARE_GMAIL_PASS)"

    safe_sintoma = re.sub(r"[^\w\s-]", "", sintoma)[:40].strip().replace(" ", "_")

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"NexaCare · Tu informe — {nivel}"
        msg["From"]    = f"NexaCare <{gmail_user}>"
        msg["To"]      = destinatario
        msg.attach(MIMEText(_html(sintoma, nivel, emoji, porcentaje, recomendacion, que_hacer, informe_ai), "html", "utf-8"))
        a = MIMEBase("application","pdf")
        a.set_payload(pdf_bytes)
        encoders.encode_base64(a)
        a.add_header("Content-Disposition", f'attachment; filename="NexaCare_{safe_sintoma}.pdf"')
        msg.attach(a)
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as s:
                s.login(gmail_user, gmail_pass)
                s.sendmail(gmail_user, destinatario, msg.as_string())
        except smtplib.SMTPAuthenticationError:
            raise
        except (smtplib.SMTPException, OSError):
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=12) as s:
                s.ehlo(); s.starttls(); s.login(gmail_user, gmail_pass)
                s.sendmail(gmail_user, destinatario, msg.as_string())
        return True, "OK"
    except smtplib.SMTPAuthenticationError as e:
        err = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        return False, f"Error de autenticación Gmail ({e.smtp_code}): {err}"
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {e}"
    except OSError as e:
        return False, f"Error de red: {e}"
