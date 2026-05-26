"""
NexaCare — Informe PDF estilo informe médico profesional
Diseño inspirado en "Clínico y Profesional": fondo blanco, layout de clínica real.

Reglas fpdf2 aplicadas:
  - Todos los rects/fondos se dibujan ANTES del texto encima.
  - Para multi_cell con fondo: fill=True para dibujar fondo+texto a la vez.
  - Barras decorativas laterales DESPUÉS (cubren borde del fill, no el área de texto).
"""
from fpdf import FPDF
from datetime import datetime
import os

# ── Paleta ────────────────────────────────────────────────────────────────────
_C = {
    # Niveles
    "VERDE":    ( 22, 163,  74),
    "AMARILLO": (161,  98,   7),
    "NARANJA":  (194,  65,  12),
    "ROJO":     (185,  28,  28),
    # Tints (fondos suaves para nivel)
    "TINT_VERDE":    (240, 253, 244),
    "TINT_AMARILLO": (255, 251, 235),
    "TINT_NARANJA":  (255, 247, 237),
    "TINT_ROJO":     (254, 242, 242),
    # Layout
    "HDR_BG":   ( 15,  40,  80),   # azul marino
    "HDR_ACC":  ( 37,  99, 235),   # azul acento
    "BODY":     (255, 255, 255),
    "GRAY_LT":  (248, 250, 252),   # fondo secciones
    "GRAY_MD":  (241, 245, 249),   # fondo tabla alt
    "GRAY_BDR": (203, 213, 225),   # borde sutil
    "TXT_DK":   ( 15,  23,  42),   # casi negro
    "TXT_MD":   ( 55,  65,  81),   # texto cuerpo
    "TXT_LT":   (107, 114, 128),   # etiquetas
    "TXT_PALE": (156, 163, 175),   # muy suave
}

_NIVEL_FULL = {
    "VERDE":    "LEVE  -  Atencion no urgente",
    "AMARILLO": "MODERADO  -  Atencion preferente",
    "NARANJA":  "URGENTE  -  Atencion prioritaria",
    "ROJO":     "EMERGENCIA  -  Atencion inmediata",
}
_NIVEL_SHORT = {
    "VERDE": "LEVE", "AMARILLO": "MODERADO",
    "NARANJA": "URGENTE", "ROJO": "EMERGENCIA",
}

_FONTS_OK = False


# ── Font helpers ──────────────────────────────────────────────────────────────

def _setup(pdf: FPDF) -> bool:
    global _FONTS_OK
    # Candidatos: Windows (Arial) y Linux/Mac (DejaVu del sistema o de fpdf2)
    candidates = [
        # Windows
        (r"C:\Windows\Fonts\arial.ttf",       r"C:\Windows\Fonts\arialbd.ttf",    r"C:\Windows\Fonts\ariali.ttf"),
        (r"C:\Windows\Fonts\Arial.ttf",        r"C:\Windows\Fonts\ArialBD.ttf",    r"C:\Windows\Fonts\ArialI.ttf"),
        # Linux — DejaVu instalado en el sistema
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
        # Linux alternativo (Ubuntu/Streamlit Cloud)
        ("/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Oblique.ttf"),
    ]
    for reg, bold, ital in candidates:
        if os.path.exists(reg):
            try:
                pdf.add_font("F", "",  fname=reg)
                pdf.add_font("F", "B", fname=bold if os.path.exists(bold) else reg)
                pdf.add_font("F", "I", fname=ital if os.path.exists(ital) else reg)
                _FONTS_OK = True
                return True
            except Exception as e:
                print(f"[NexaCare PDF] Error cargando fuente {reg}: {e}")
    # Último recurso: DejaVu incluido en el paquete fpdf2
    try:
        import fpdf as _m
        p = os.path.dirname(_m.__file__)
        dv = os.path.join(p, "fonts", "DejaVuSans.ttf")
        if os.path.exists(dv):
            dvb = os.path.join(p, "fonts", "DejaVuSans-Bold.ttf")
            dvi = os.path.join(p, "fonts", "DejaVuSans-Oblique.ttf")
            pdf.add_font("F", "",  fname=dv)
            pdf.add_font("F", "B", fname=dvb if os.path.exists(dvb) else dv)
            pdf.add_font("F", "I", fname=dvi if os.path.exists(dvi) else dv)
            _FONTS_OK = True
            return True
    except Exception as e:
        print(f"[NexaCare PDF] Fuente DejaVu no disponible: {e}")
    return False


def _f(pdf: FPDF, style: str = "", size: int = 10):
    if _FONTS_OK and style.upper() in ("", "B", "I"):
        pdf.set_font("F", style, size)
    else:
        pdf.set_font("Helvetica", style, size)


def _c(t: str) -> str:
    """Normaliza caracteres especiales."""
    repl = {
        "–": "-", "—": "-",
        "‘": "'", "’": "'",
        "“": '"', "”": '"',
        "…": "...", "•": "-", "·": ".",
    }
    for o, s in repl.items():
        t = t.replace(o, s)
    if _FONTS_OK:
        return t
    # Sin fuente Unicode: eliminar emojis/símbolos y limpiar espacios dobles
    cleaned = "".join(ch if ord(ch) < 256 else "" for ch in t)
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()


def _nk(nivel: str) -> str:
    for k in ("ROJO", "NARANJA", "AMARILLO", "VERDE"):
        if k in nivel.upper():
            return k
    return "VERDE"


def formatear_distancia(m: int) -> str:
    return f"{m} m" if m < 1000 else f"{m/1000:.1f} km"


# ── Gráficos vectoriales ──────────────────────────────────────────────────────

def _cross_icon(pdf: FPDF, x: float, y: float, size: float = 10):
    """Icono de cruz médica: fondo azul, cruz blanca."""
    # Fondo cuadrado azul
    pdf.set_fill_color(*_C["HDR_ACC"])
    pdf.rect(x, y, size, size, "F")
    # Cruz blanca encima
    bw = size * 0.62
    bh = size * 0.26
    cx = x + (size - bw) / 2
    cy = y + (size - bh) / 2
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(cx, cy, bw, bh, "F")          # horizontal
    pdf.rect(cx + (bw - bh) / 2, y + (size - bw) / 2, bh, bw, "F")  # vertical


def _section_bar(pdf: FPDF, title: str, M: int, W: int):
    """
    Encabezado de sección: fondo azul marino + texto blanco.
    El fondo se dibuja ANTES del texto.
    """
    y = pdf.get_y()
    h = 8
    pdf.set_fill_color(*_C["HDR_BG"])
    pdf.rect(M, y, W, h, "F")
    # Acento de color izquierda (3px)
    pdf.set_fill_color(*_C["HDR_ACC"])
    pdf.rect(M, y, 3, h, "F")
    # Texto
    pdf.set_xy(M + 7, y + 1)
    _f(pdf, "B", 7.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W - 7, 6, title.upper(), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


def _section_line(pdf: FPDF, title: str, M: int, W: int):
    """Encabezado de sección: texto coloreado + línea separadora."""
    y = pdf.get_y()
    # Barra izquierda
    pdf.set_fill_color(*_C["HDR_ACC"])
    pdf.rect(M, y + 1, 3, 7, "F")
    # Texto
    pdf.set_xy(M + 6, y)
    _f(pdf, "B", 8)
    pdf.set_text_color(*_C["HDR_BG"])
    pdf.cell(W - 6, 9, title.upper(), new_x="LMARGIN", new_y="NEXT")
    # Línea
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.line(M, pdf.get_y(), M + W, pdf.get_y())
    pdf.ln(4)


# ── Clases PDF ────────────────────────────────────────────────────────────────

class _DocPaciente(FPDF):
    def __init__(self, nk: str, nrgb: tuple, consult_id: str = ""):
        super().__init__()
        self._nk       = nk
        self._nrgb     = nrgb
        self._cid      = consult_id

    def header(self):
        now = datetime.now()
        # Línea de acento superior (2mm)
        self.set_fill_color(*_C["HDR_ACC"])
        self.rect(0, 0, 210, 2, "F")
        # Fondo blanco cabecera
        self.set_fill_color(255, 255, 255)
        self.rect(0, 2, 210, 26, "F")

        # Cruz médica
        _cross_icon(self, 10, 6, 11)
        # "NexaCare"
        self.set_xy(24, 6)
        _f(self, "B", 15)
        self.set_text_color(*_C["HDR_BG"])
        self.cell(17, 7, "Nexa")
        self.set_text_color(*_C["HDR_ACC"])
        self.cell(17, 7, "Care")
        # Subtítulo
        self.set_xy(24, 14)
        _f(self, "", 6)
        self.set_text_color(*_C["TXT_LT"])
        self.cell(60, 4, "Informe de orientacion de triaje medico")

        # Título centrado
        self.set_xy(80, 8)
        _f(self, "B", 9)
        self.set_text_color(*_C["HDR_BG"])
        self.cell(0, 6, "INFORME DE ORIENTACION DE TRIAJE MEDICO", align="C")

        # Metadatos derecha
        self.set_xy(152, 6)
        _f(self, "", 6.5)
        self.set_text_color(*_C["TXT_LT"])
        self.cell(48, 4, f"Fecha:  {now.strftime('%d/%m/%Y')}", align="R")
        self.set_xy(152, 11)
        self.cell(48, 4, f"Hora:   {now.strftime('%H:%M')}", align="R")
        self.set_xy(152, 16)
        _f(self, "", 5.5)
        self.cell(48, 4, f"ID: {self._cid}", align="R")

        # Línea separadora
        self.set_draw_color(*_C["GRAY_BDR"])
        self.line(10, 28, 200, 28)
        self.set_y(32)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*_C["GRAY_BDR"])
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        _f(self, "", 6)
        self.set_text_color(*_C["TXT_PALE"])
        self.cell(
            0, 4,
            "Este informe no sustituye la valoracion de un profesional sanitario.  "
            f"|  NexaCare  TFG SMR 2025-2026  |  Pagina {self.page_no()}",
            align="C",
        )


class _DocAdmin(FPDF):
    def header(self):
        self.set_fill_color(*_C["HDR_ACC"])
        self.rect(0, 0, 210, 2, "F")
        self.set_fill_color(255, 255, 255)
        self.rect(0, 2, 210, 26, "F")
        _cross_icon(self, 10, 6, 11)
        self.set_xy(24, 6)
        _f(self, "B", 15)
        self.set_text_color(*_C["HDR_BG"])
        self.cell(17, 7, "Nexa")
        self.set_text_color(*_C["HDR_ACC"])
        self.cell(17, 7, "Care")
        self.set_xy(24, 14)
        _f(self, "", 6)
        self.set_text_color(*_C["TXT_LT"])
        self.cell(60, 4, "Informe administrativo  |  CONFIDENCIAL")
        self.set_xy(70, 8)
        _f(self, "B", 9)
        self.set_text_color(*_C["HDR_BG"])
        self.cell(0, 6, "PANEL ADMINISTRATIVO  -  SOLO PERSONAL AUTORIZADO", align="C")
        self.set_xy(152, 11)
        _f(self, "", 6.5)
        self.set_text_color(*_C["TXT_LT"])
        self.cell(48, 4, datetime.now().strftime("%d/%m/%Y  %H:%M"), align="R")
        self.set_draw_color(*_C["GRAY_BDR"])
        self.line(10, 28, 200, 28)
        self.set_y(32)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*_C["GRAY_BDR"])
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        _f(self, "", 6)
        self.set_text_color(*_C["TXT_PALE"])
        self.cell(
            0, 4,
            f"NexaCare  |  CONFIDENCIAL - Solo personal sanitario autorizado  |  Pagina {self.page_no()}",
            align="C",
        )


# ── Bloques visuales principales ──────────────────────────────────────────────

def _banner_nivel(pdf: FPDF, nk: str, nrgb: tuple, porcentaje: int, M: int, W: int):
    """
    Banner full-width del nivel de urgencia.
    Fondo de color, texto blanco, badge de porcentaje (caja blanca).
    Todo el fondo se dibuja ANTES de cualquier texto.
    """
    y = pdf.get_y()
    h = 18

    # 1. Fondo coloreado (PRIMERO)
    pdf.set_fill_color(*nrgb)
    pdf.rect(M, y, W, h, "F")

    # 2. Badge de porcentaje: caja blanca a la derecha (ANTES del texto)
    badge_w, badge_h = 36, 14
    bx = M + W - badge_w - 4
    by = y + (h - badge_h) / 2
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(bx, by, badge_w, badge_h, "F")

    # 3. Textos encima del fondo ya dibujado
    # Etiqueta pequeña
    pdf.set_xy(M + 7, y + 2)
    _f(pdf, "", 6.5)
    pdf.set_text_color(230, 240, 255)
    pdf.cell(W - badge_w - 15, 4, "NIVEL ASIGNADO:")
    # Nivel principal
    pdf.set_xy(M + 7, y + 7)
    _f(pdf, "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W - badge_w - 15, 9, f"  {_NIVEL_FULL[nk]}")
    # Porcentaje en la caja blanca
    pdf.set_xy(bx, by)
    _f(pdf, "B", 16)
    pdf.set_text_color(*nrgb)
    pdf.cell(badge_w, 9, f"{porcentaje}%", align="C")
    pdf.set_xy(bx, by + 9)
    _f(pdf, "", 5.5)
    pdf.set_text_color(*_C["TXT_LT"])
    pdf.cell(badge_w, 4, "gravedad", align="C")

    pdf.set_y(y + h + 6)


def _stat_boxes(pdf: FPDF, nk: str, nrgb: tuple,
                porcentaje: int, puntuacion: int, puntuacion_maxima: int,
                sintoma: str, M: int, W: int):
    """
    3 cajas de estadísticas: Gravedad | Puntuación | Síntoma.
    Fondos dibujados ANTES del texto.
    """
    y0   = pdf.get_y()
    gap  = 5
    bw   = (W - gap * 2) / 3
    bh   = 28

    boxes = [
        (nrgb,          "GRAVEDAD ESTIMADA", f"{porcentaje}%", 16, nrgb),
        (_C["HDR_ACC"], "PUNTUACION",        f"{puntuacion} / {puntuacion_maxima}", 14, _C["TXT_DK"]),
        (_C["HDR_ACC"], "SINTOMA PRINCIPAL", _c(sintoma[:16] + ("…" if len(sintoma) > 16 else "")), 11, _C["TXT_DK"]),
    ]

    for i, (accent, lbl, val, val_sz, val_col) in enumerate(boxes):
        x = M + i * (bw + gap)

        # 1. Fondo gris claro (PRIMERO)
        pdf.set_fill_color(*_C["GRAY_LT"])
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.rect(x, y0, bw, bh, "FD")
        # 2. Barra de acento superior (PRIMERO, antes del texto)
        pdf.set_fill_color(*accent)
        pdf.rect(x, y0, bw, 2.5, "F")

        # 3. Etiqueta
        pdf.set_xy(x, y0 + 4)
        _f(pdf, "B", 6.5)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(bw, 4, lbl, align="C")

        # 4. Valor grande
        pdf.set_xy(x, y0 + 9)
        _f(pdf, "B", val_sz)
        pdf.set_text_color(*val_col)
        pdf.cell(bw, bh - 11, val, align="C")

    pdf.set_y(y0 + bh + 8)


def _reco_box(pdf: FPDF, nk: str, nrgb: tuple, tint: tuple,
              recomendacion: str, M: int, W: int):
    """
    Caja de recomendación con fondo tintado y borde izquierdo de color.
    fill=True en multi_cell dibuja fondo+texto juntos (correcto).
    La barra lateral se dibuja DESPUÉS.
    """
    _section_line(pdf, "Recomendacion inmediata", M, W)
    y0 = pdf.get_y()
    # Padding izquierdo para dejar espacio a la barra lateral
    pdf.set_x(M + 6)
    _f(pdf, "B", 9.5)
    pdf.set_fill_color(*tint)
    pdf.set_text_color(*nrgb)
    pdf.multi_cell(W - 8, 6.5, _c(recomendacion), fill=True,
                   new_x="LMARGIN", new_y="NEXT")
    y1 = pdf.get_y()
    # Barra lateral de color DESPUÉS (cubre borde izquierdo del fill)
    pdf.set_fill_color(*nrgb)
    pdf.rect(M, y0, 4, y1 - y0, "F")
    # Borde exterior sutil
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.rect(M, y0, W, y1 - y0, "D")
    pdf.ln(6)


def _info_cols(pdf: FPDF, datos_paciente: dict | None,
               sintoma: str, puntuacion: int, puntuacion_maxima: int,
               porcentaje: int, nk: str, nrgb: tuple, M: int, W: int):
    """
    Dos columnas: Datos del paciente | Resumen de evaluación.
    Fondos dibujados ANTES del texto.
    """
    _section_line(pdf, "Datos generales", M, W)
    dp = datos_paciente or {}
    col_w = (W - 6) // 2
    y0    = pdf.get_y()

    items_izq = []
    if dp.get("edad"):   items_izq.append(("Edad",   dp["edad"]))
    if dp.get("sexo"):   items_izq.append(("Sexo",   dp["sexo"]))
    if dp.get("altura"): items_izq.append(("Altura", f"{dp['altura']} cm"))
    if dp.get("peso"):   items_izq.append(("Peso",   f"{dp['peso']} kg"))
    if dp.get("imc"):    items_izq.append(("IMC",    f"{dp['imc']} kg/m2"))
    if not items_izq:    items_izq.append(("Paciente", "Datos no proporcionados"))

    items_dch = [
        ("Sintoma",    _c(sintoma)),
        ("Puntuacion", f"{puntuacion} / {puntuacion_maxima}"),
        ("Gravedad",   f"{porcentaje}%  ({_NIVEL_SHORT.get(nk, nk)})"),
        ("Fecha",      datetime.now().strftime("%d/%m/%Y %H:%M")),
    ]

    row_h = 6.5
    pad   = 4
    h_izq = len(items_izq) * row_h + pad * 2 + 8
    h_dch = len(items_dch) * row_h + pad * 2 + 8
    box_h = max(h_izq, h_dch)

    # 1. Fondos (PRIMERO)
    pdf.set_fill_color(*_C["GRAY_LT"])
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.rect(M,             y0, col_w,     box_h, "FD")
    pdf.rect(M + col_w + 6, y0, col_w,     box_h, "FD")

    # 2. Cabeceras de columna (fondo + texto)
    pdf.set_fill_color(*_C["HDR_BG"])
    pdf.rect(M,             y0, col_w, 8, "F")
    pdf.rect(M + col_w + 6, y0, col_w, 8, "F")
    _f(pdf, "B", 7)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(M + 4, y0 + 1)
    pdf.cell(col_w - 4, 6, "DATOS DEL PACIENTE")
    pdf.set_xy(M + col_w + 10, y0 + 1)
    pdf.cell(col_w - 4, 6, "RESUMEN DE EVALUACION")

    # 3. Datos columna izquierda
    for i, (lbl, val) in enumerate(items_izq):
        ry = y0 + 8 + pad + i * row_h
        pdf.set_xy(M + 4, ry)
        _f(pdf, "B", 7.5)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(28, row_h, _c(lbl) + ":")
        _f(pdf, "", 8.5)
        pdf.set_text_color(*_C["TXT_DK"])
        pdf.cell(col_w - 32, row_h, _c(str(val)))

    # 4. Datos columna derecha
    for i, (lbl, val) in enumerate(items_dch):
        ry = y0 + 8 + pad + i * row_h
        pdf.set_xy(M + col_w + 10, ry)
        _f(pdf, "B", 7.5)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(28, row_h, _c(lbl) + ":")
        _f(pdf, "B" if lbl == "Gravedad" else "", 8.5)
        pdf.set_text_color(*nrgb if lbl == "Gravedad" else _C["TXT_DK"])
        pdf.cell(col_w - 32, row_h, _c(str(val)))

    pdf.set_y(y0 + box_h + 6)


def _ai_box(pdf: FPDF, informe_ai: str, M: int, W: int):
    """
    Sección del informe IA con fondo gris y borde azul izquierdo.
    fill=True en multi_cell: fondo+texto juntos (correcto).
    Barra lateral DESPUÉS.
    """
    _section_line(pdf, "Resumen del caso  -  Analisis NexaCare IA", M, W)
    y0 = pdf.get_y()
    pdf.set_x(M + 5)
    _f(pdf, "", 9)
    pdf.set_fill_color(*_C["GRAY_LT"])
    pdf.set_text_color(*_C["TXT_MD"])
    pdf.multi_cell(W - 5, 5.5, _c(informe_ai.strip()), fill=True,
                   new_x="LMARGIN", new_y="NEXT")
    y1 = pdf.get_y()
    # Barra azul izquierda DESPUÉS
    pdf.set_fill_color(*_C["HDR_ACC"])
    pdf.rect(M, y0, 3, y1 - y0, "F")
    # Borde exterior
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.rect(M, y0, W, y1 - y0, "D")
    pdf.ln(6)


def _gravity_bar(pdf: FPDF, porcentaje: int, nk: str, nrgb: tuple, M: int, W: int):
    """
    Barra de indicador de gravedad con 4 segmentos de color y marcador.
    Segmentos dibujados ANTES del marcador y etiquetas.
    """
    _section_line(pdf, "Indicador de gravedad", M, W)

    bar_y  = pdf.get_y()
    bar_h  = 8
    seg_w  = (W) / 4
    segs   = [
        (_C["VERDE"],    "Leve"),
        (_C["AMARILLO"], "Moderado"),
        (_C["NARANJA"],  "Urgente"),
        (_C["ROJO"],     "Emergencia"),
    ]

    # 1. Segmentos de color (PRIMERO — todo el fondo)
    for i, (col, _) in enumerate(segs):
        # Versión pastel (mezcla con blanco)
        pastel = tuple(int(c + (255 - c) * 0.5) for c in col)
        pdf.set_fill_color(*pastel)
        rx = M + i * seg_w
        # Esquinas redondeadas en primer y último segmento
        pdf.rect(rx, bar_y, seg_w, bar_h, "F")

    # Borde exterior de la barra
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.rect(M, bar_y, W, bar_h, "D")

    # 2. Marcador de posición (círculo blanco con borde de color)
    pct_clamp = max(2, min(porcentaje, 98))
    mx = M + W * pct_clamp / 100
    pdf.set_fill_color(*nrgb)
    pdf.ellipse(mx - 4, bar_y - 2, 8, bar_h + 4, "F")
    pdf.set_fill_color(255, 255, 255)
    pdf.ellipse(mx - 2.5, bar_y - 0.5, 5, bar_h + 1, "F")

    # Porcentaje encima del marcador
    pdf.set_xy(mx - 12, bar_y - 6)
    _f(pdf, "B", 7.5)
    pdf.set_text_color(*nrgb)
    pdf.cell(24, 5, f"{porcentaje}%", align="C")

    # 3. Etiquetas debajo de cada segmento
    for i, (_, lbl) in enumerate(segs):
        pdf.set_xy(M + i * seg_w, bar_y + bar_h + 2)
        _f(pdf, "", 6.5)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(seg_w, 4, lbl, align="C")
    pdf.ln(8)


def _patient_chips(pdf: FPDF, datos_paciente: dict | None,
                   nk: str, nrgb: tuple, M: int, W: int):
    """
    Fila de chips de datos del paciente al pie de página 1.
    Fondos dibujados ANTES del texto.
    """
    dp   = datos_paciente or {}
    now  = datetime.now()
    chips = [
        ("Edad",           dp.get("edad") or "No indicada"),
        ("Sexo",           dp.get("sexo") or "No indicado"),
        ("Codigo postal",  "No indicado"),
        ("Fecha consulta", now.strftime("%d/%m/%Y  %H:%M")),
    ]
    y0   = pdf.get_y()
    cw   = (W - 9) / 4
    h    = 18

    for i, (lbl, val) in enumerate(chips):
        x = M + i * (cw + 3)
        # 1. Fondo (PRIMERO)
        pdf.set_fill_color(*_C["GRAY_LT"])
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.rect(x, y0, cw, h, "FD")
        # Acento superior
        pdf.set_fill_color(*_C["HDR_ACC"])
        pdf.rect(x, y0, cw, 2, "F")
        # 2. Etiqueta
        pdf.set_xy(x, y0 + 3)
        _f(pdf, "", 7)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(cw, 4, lbl, align="C")
        # 3. Valor
        pdf.set_xy(x, y0 + 8)
        _f(pdf, "B", 8)
        pdf.set_text_color(*_C["TXT_DK"])
        val_disp = _c(str(val))
        if len(val_disp) > 16:
            val_disp = val_disp[:14] + "..."
        pdf.cell(cw, 6, val_disp, align="C")

    pdf.set_y(y0 + h + 6)


# ── Pasos y tabla ─────────────────────────────────────────────────────────────

def _steps_list(pdf: FPDF, que_hacer: list, nk: str, nrgb: tuple, tint: tuple,
                M: int, W: int):
    """
    Lista numerada de pasos.
    Badge de número dibujado ANTES del texto del paso.
    """
    _section_line(pdf, "Pasos a seguir", M, W)
    for i, paso in enumerate(que_hacer, 1):
        if pdf.get_y() > 268:
            pdf.add_page()

        y0    = pdf.get_y()
        badge = 8

        # 1. Badge fondo (PRIMERO)
        pdf.set_fill_color(*nrgb)
        pdf.rect(M, y0, badge, badge, "F")
        # 2. Número en el badge
        pdf.set_xy(M, y0)
        _f(pdf, "B", 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(badge, badge, str(i), align="C")
        # 3. Fondo del texto
        pdf.set_fill_color(*_C["GRAY_LT"])
        x_txt = M + badge + 3
        w_txt = W - badge - 3
        # Estimar altura: multi_cell calcula sola con fill=True
        pdf.set_xy(x_txt, y0)
        _f(pdf, "", 9)
        pdf.set_text_color(*_C["TXT_MD"])
        pdf.multi_cell(w_txt, 5.5, _c(paso), fill=True,
                       new_x="LMARGIN", new_y="NEXT")
        # Alinear Y al máximo de badge y texto
        if pdf.get_y() < y0 + badge:
            pdf.set_y(y0 + badge)
        pdf.ln(3)


def _answers_table(pdf: FPDF, respuestas: list, nk: str, nrgb: tuple, M: int, W: int):
    """
    Tabla de respuestas al cuestionario.
    Fondo de cada fila dibujado ANTES del texto.
    """
    _section_line(pdf, "Detalle de respuestas al cuestionario", M, W)

    # Cabecera (fondo PRIMERO)
    y0 = pdf.get_y()
    pdf.set_fill_color(*_C["HDR_BG"])
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.set_x(M)
    pdf.rect(M, y0, 22, 8, "FD")
    pdf.rect(M + 22, y0, W - 22, 8, "FD")
    # Texto cabecera
    _f(pdf, "B", 7.5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(M, y0)
    pdf.cell(22, 8, "Respuesta", align="C")
    pdf.cell(W - 22, 8, "Pregunta evaluada")
    pdf.ln()

    row_h = 7
    for idx, (preg, si) in enumerate(respuestas):
        if pdf.get_y() > 268:
            pdf.add_page()

        bg    = _C["GRAY_LT"] if idx % 2 == 0 else _C["BODY"]
        row_y = pdf.get_y()

        # 1. Fondo de la fila (PRIMERO)
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.rect(M, row_y, W, row_h, "FD")

        # 2. Badge SI/NO (fondo de color ANTES del texto del badge)
        badge_col = _C["VERDE"] if si else _C["ROJO"]
        bx = M + 2
        by = row_y + (row_h - 5.5) / 2
        pdf.set_fill_color(*badge_col)
        pdf.rect(bx, by, 17, 5.5, "F")

        # 3. Texto del badge
        _f(pdf, "B", 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(bx, by)
        pdf.cell(17, 5.5, "SI" if si else "NO", align="C")

        # 4. Separador vertical
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.line(M + 22, row_y, M + 22, row_y + row_h)

        # 5. Texto pregunta
        _f(pdf, "", 8)
        pdf.set_text_color(*_C["TXT_MD"])
        pdf.set_xy(M + 24, row_y + (row_h - 5) / 2)
        pdf.cell(W - 24, 5, _c(preg[:85]))

        pdf.set_y(row_y + row_h)

    pdf.ln(5)


def _centros_section(pdf: FPDF, centros: list, M: int, W: int):
    """Lista de centros sanitarios cercanos."""
    _section_line(pdf, "Centros sanitarios publicos cercanos", M, W)
    for c in centros[:4]:
        if pdf.get_y() > 265:
            pdf.add_page()
        y0 = pdf.get_y()
        # Fondo fila
        pdf.set_fill_color(*_C["GRAY_LT"])
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.rect(M, y0, W, 14, "FD")
        # Icono
        pdf.set_xy(M + 3, y0 + 2)
        _f(pdf, "B", 10)
        pdf.set_text_color(*_C["HDR_ACC"])
        pdf.cell(8, 6, _c(c.get("icono", "+")))
        # Nombre
        pdf.set_xy(M + 14, y0 + 2)
        _f(pdf, "B", 9)
        pdf.set_text_color(*_C["TXT_DK"])
        pdf.cell(W - 55, 6, _c(c["nombre"]))
        # Distancia badge
        dist_txt = formatear_distancia(c.get("distancia_m", 0))
        pdf.set_fill_color(*_C["HDR_ACC"])
        pdf.rect(M + W - 38, y0 + 2, 30, 5.5, "F")
        _f(pdf, "B", 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(M + W - 38, y0 + 2)
        pdf.cell(30, 5.5, dist_txt, align="C")
        # Tipo
        pdf.set_xy(M + 14, y0 + 8)
        _f(pdf, "I", 7.5)
        pdf.set_text_color(*_C["TXT_LT"])
        urg = "  · Con urgencias 24h" if c.get("urgencias") else ""
        pdf.cell(W - 55, 5, _c(c.get("tipo", "") + urg))
        pdf.set_y(y0 + 16)
    pdf.ln(2)


# ── PDF PACIENTE (función principal) ─────────────────────────────────────────

def generar_pdf(
    sintoma: str,
    respuestas: list,
    puntuacion: int,
    puntuacion_maxima: int,
    porcentaje: int,
    nivel: str,
    emoji: str,
    recomendacion: str,
    que_hacer: list,
    informe_ai: str | None = None,
    centros: list | None = None,
    datos_paciente: dict | None = None,
) -> bytes:
    nk   = _nk(nivel)
    nrgb = _C[nk]
    tint = _C[f"TINT_{nk}"]

    now = datetime.now()
    sint_abbr = "".join(w[0].upper() for w in sintoma.split()[:3]) if sintoma else "GEN"
    consult_id = f"NC-{now.strftime('%Y%m%d-%H%M')}-{sint_abbr}-001"

    pdf = _DocPaciente(nk=nk, nrgb=nrgb, consult_id=consult_id)
    _setup(pdf)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_left_margin(15)

    M, W = 15, 180

    # ── 1. BANNER NIVEL DE URGENCIA ───────────────────────────────────────────
    _banner_nivel(pdf, nk, nrgb, porcentaje, M, W)

    # ── 2. TRES CAJAS DE ESTADÍSTICAS ─────────────────────────────────────────
    _stat_boxes(pdf, nk, nrgb, porcentaje, puntuacion, puntuacion_maxima,
                sintoma, M, W)

    # ── 3. RECOMENDACIÓN INMEDIATA ────────────────────────────────────────────
    _reco_box(pdf, nk, nrgb, tint, recomendacion, M, W)

    # ── 4. DATOS DEL PACIENTE / RESUMEN EVALUACIÓN ───────────────────────────
    _info_cols(pdf, datos_paciente, sintoma, puntuacion, puntuacion_maxima,
               porcentaje, nk, nrgb, M, W)

    # ── 5. RESUMEN DEL CASO (IA) ──────────────────────────────────────────────
    if informe_ai:
        _ai_box(pdf, informe_ai, M, W)

    # ── 6. INDICADOR DE GRAVEDAD ──────────────────────────────────────────────
    _gravity_bar(pdf, porcentaje, nk, nrgb, M, W)

    # ── 7. CHIPS DE DATOS DEL PACIENTE ───────────────────────────────────────
    _patient_chips(pdf, datos_paciente, nk, nrgb, M, W)

    # ── PÁGINA 2: PASOS Y RESPUESTAS ─────────────────────────────────────────
    pdf.add_page()
    _steps_list(pdf, que_hacer, nk, nrgb, tint, M, W)

    pdf.ln(4)
    _answers_table(pdf, respuestas, nk, nrgb, M, W)

    if centros:
        if pdf.get_y() > 240:
            pdf.add_page()
        _centros_section(pdf, centros, M, W)

    # ── AVISO LEGAL FINAL ─────────────────────────────────────────────────────
    if pdf.get_y() > 255:
        pdf.add_page()
    pdf.ln(4)
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.line(M, pdf.get_y(), M + W, pdf.get_y())
    pdf.ln(3)
    _f(pdf, "I", 7.5)
    pdf.set_text_color(*_C["TXT_PALE"])
    pdf.set_x(M)
    pdf.multi_cell(
        W, 4.5,
        "AVISO IMPORTANTE: Este documento ha sido generado por NexaCare, un sistema de apoyo "
        "al triaje medico desarrollado como Trabajo de Fin de Grado (TFG SMR 2025-2026). "
        "Su finalidad es orientativa y no constituye un diagnostico medico. Ante cualquier "
        "duda o empeoramiento, consulte a un profesional sanitario o llame al 112.",
    )

    return bytes(pdf.output())


# ── PDF ADMIN ─────────────────────────────────────────────────────────────────

def generar_pdf_admin(stats: dict, consultas: list) -> bytes:
    total    = stats.get("total", 0)
    niv_raw  = stats.get("niveles_raw", {})
    sint_map = stats.get("sintomas", {})

    niveles = {"VERDE": 0, "AMARILLO": 0, "NARANJA": 0, "ROJO": 0}
    for ns, cnt in niv_raw.items():
        for k in niveles:
            if k in ns:
                niveles[k] += cnt
                break

    pdf = _DocAdmin()
    _setup(pdf)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_left_margin(15)
    M, W = 15, 180

    # ── Métricas principales ───────────────────────────────────────────────────
    _section_bar(pdf, "Resumen ejecutivo", M, W)

    y0  = pdf.get_y()
    cw  = (W - 9) / 4
    bh  = 26
    metrics = [
        (_C["HDR_ACC"], "TOTAL CONSULTAS",    str(total),             "historico completo"),
        (_C["ROJO"],    "EMERGENCIAS ROJO",   str(niveles["ROJO"]),   "requirieron 112"),
        (_C["NARANJA"], "URGENTES NARANJA",   str(niveles["NARANJA"]), "urgencias hosp."),
        (_C["VERDE"],   "CASOS LEVES",        str(niveles["VERDE"]),  "atencion diferida"),
    ]
    for i, (col, lbl, val, sub) in enumerate(metrics):
        x = M + i * (cw + 3)
        pdf.set_fill_color(*_C["GRAY_LT"])
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.rect(x, y0, cw, bh, "FD")
        pdf.set_fill_color(*col)
        pdf.rect(x, y0, cw, 2.5, "F")
        pdf.set_xy(x, y0 + 4)
        _f(pdf, "B", 6.5)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(cw, 4, lbl, align="C")
        pdf.set_xy(x, y0 + 9)
        _f(pdf, "B", 16)
        pdf.set_text_color(*col)
        pdf.cell(cw, 10, val, align="C")
        pdf.set_xy(x, y0 + 20)
        _f(pdf, "", 6.5)
        pdf.set_text_color(*_C["TXT_LT"])
        pdf.cell(cw, 4, sub, align="C")

    pdf.set_y(y0 + bh + 8)

    # ── Distribución por nivel ─────────────────────────────────────────────────
    _section_line(pdf, "Distribucion por nivel de urgencia", M, W)
    max_n = max(niveles.values()) or 1
    for nombre, key, col in [
        ("Verde – Leve",         "VERDE",    _C["VERDE"]),
        ("Amarillo – Moderado",  "AMARILLO", _C["AMARILLO"]),
        ("Naranja – Urgente",    "NARANJA",  _C["NARANJA"]),
        ("Rojo – Emergencia",    "ROJO",     _C["ROJO"]),
    ]:
        val  = niveles[key]
        pct  = int(val / max_n * 100)
        y_r  = pdf.get_y()
        # Fondo barra
        pdf.set_fill_color(*_C["GRAY_LT"])
        pdf.rect(M + 52, y_r + 1, W - 65, 5, "F")
        # Relleno
        bar_fill_w = max(1, int((W - 65) * pct / 100))
        pastel = tuple(int(c + (255 - c) * 0.45) for c in col)
        pdf.set_fill_color(*pastel)
        pdf.rect(M + 52, y_r + 1, bar_fill_w, 5, "F")
        # Texto
        pdf.set_xy(M, y_r)
        _f(pdf, "", 8.5)
        pdf.set_text_color(*_C["TXT_MD"])
        pdf.cell(50, 7, _c(nombre))
        pdf.set_xy(M + W - 12, y_r)
        _f(pdf, "B", 8.5)
        pdf.set_text_color(*col)
        pdf.cell(12, 7, str(val), align="R")
        pdf.ln()

    pdf.ln(4)

    # ── Síntomas más consultados ───────────────────────────────────────────────
    _section_line(pdf, "Sintomas mas consultados", M, W)
    if sint_map:
        max_s = max(sint_map.values()) or 1
        for s, n in sorted(sint_map.items(), key=lambda x: -x[1])[:10]:
            pct = int(n / max_s * 100)
            y_r = pdf.get_y()
            pdf.set_fill_color(*_C["GRAY_LT"])
            pdf.rect(M + 62, y_r + 1, W - 75, 5, "F")
            bar_fill_w = max(1, int((W - 75) * pct / 100))
            pdf.set_fill_color(*_C["HDR_ACC"])
            # Pastel azul
            pdf.set_fill_color(185, 210, 252)
            pdf.rect(M + 62, y_r + 1, bar_fill_w, 5, "F")
            pdf.set_xy(M, y_r)
            _f(pdf, "", 8.5)
            pdf.set_text_color(*_C["TXT_MD"])
            pdf.cell(60, 7, _c(s))
            pdf.set_xy(M + W - 12, y_r)
            _f(pdf, "B", 8.5)
            pdf.set_text_color(*_C["HDR_ACC"])
            pdf.cell(12, 7, str(n), align="R")
            pdf.ln()
    pdf.ln(4)

    # ── Tabla últimas consultas ────────────────────────────────────────────────
    if pdf.get_y() > 230:
        pdf.add_page()
    _section_line(pdf, "Ultimas consultas registradas", M, W)

    # Cabecera tabla
    y0 = pdf.get_y()
    pdf.set_fill_color(*_C["HDR_BG"])
    col_widths = [32, 52, 26, 26, 44]
    col_names  = ["Fecha", "Sintoma", "Punt.", "Grav.", "Nivel"]
    pdf.set_draw_color(*_C["GRAY_BDR"])
    x = M
    for w, name in zip(col_widths, col_names):
        pdf.rect(x, y0, w, 8, "FD")
        pdf.set_xy(x + 2, y0 + 1)
        _f(pdf, "B", 7.5)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w - 2, 6, name)
        x += w
    pdf.ln(8)

    row_h = 7
    for idx, c in enumerate(consultas[:20]):
        if pdf.get_y() > 270:
            pdf.add_page()
        row_y = pdf.get_y()
        bg = _C["GRAY_LT"] if idx % 2 == 0 else _C["BODY"]
        # Fondo fila (PRIMERO)
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*_C["GRAY_BDR"])
        pdf.rect(M, row_y, W, row_h, "FD")
        # Nivel color badge
        cnk = _nk(c["nivel"])
        col_n = _C[cnk]
        # Badge nivel
        bx = M + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + 2
        by = row_y + (row_h - 5) / 2
        pdf.set_fill_color(*col_n)
        pdf.rect(bx, by, 38, 5, "F")
        _f(pdf, "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(bx, by)
        pdf.cell(38, 5, cnk, align="C")
        # Separadores verticales
        x = M
        for w in col_widths:
            x += w
            pdf.line(x, row_y, x, row_y + row_h)
        # Datos
        x = M
        vals = [
            c["timestamp"],
            _c(c["sintoma"]),
            f"{c['puntuacion']}/{c['maximo']}",
            f"{c['porcentaje']}%",
            "",  # nivel (ya tiene badge)
        ]
        for w, v in zip(col_widths, vals):
            pdf.set_xy(x + 2, row_y + (row_h - 5) / 2)
            _f(pdf, "", 8)
            pdf.set_text_color(*_C["TXT_MD"])
            pdf.cell(w - 2, 5, _c(str(v))[:24])
            x += w
        pdf.set_y(row_y + row_h)

    pdf.ln(4)
    pdf.set_draw_color(*_C["GRAY_BDR"])
    pdf.line(M, pdf.get_y(), M + W, pdf.get_y())
    pdf.ln(3)
    _f(pdf, "I", 7.5)
    pdf.set_text_color(*_C["TXT_PALE"])
    pdf.set_x(M)
    pdf.cell(W, 5, f"Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}  -  NexaCare TFG SMR 2025-2026", align="C")

    return bytes(pdf.output())
