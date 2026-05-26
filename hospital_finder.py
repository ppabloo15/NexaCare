"""
NexaCare — Buscador de centros sanitarios públicos
Busca hospitales y ambulatorios/centros de salud públicos.
Geocoding: Nominatim. Datos: Overpass API (OSM). Sin API key.
"""
import math
import json
import urllib.request
import urllib.parse
import urllib.error

_HEADERS = {"User-Agent": "NexaCare-TFG-SMR/2.0 (proyecto academico TFG)"}

# Cadenas que indican centro PRIVADO → excluir siempre
_PRIVADO_NOMBRE = [
    "sanitas", "quirón", "quiron", "hm hospitals", "hm ",
    "vithas", "ruber", "teknon", "cemtro", "juaneda",
    "asisa", "adeslas", "imed",
    "dental", "dentista", "veterinari", "farmacia",
    "óptica", "optica", "estética", "estetica",
    "psicotécnico", "psicotecnico",
    "cuidados paliativos", "residencia", "geriátrico", "geriatrico",
]

_PRIVADO_OPERADOR = [
    "sanitas", "quirón", "quiron", "hm ", "vithas", "ruber",
    "teknon", "cemtro", "asisa", "adeslas",
]

# Palabras que confirman que es un centro PÚBLICO
_PUBLICO_NOMBRE = [
    "centro de salud", "ambulatorio", "consultorio",
    "hospital universitario", "hospital general", "hospital comarcal",
    "hospital regional", "hospital de día", "hospital público",
    "centro médico de urgencias", "urgencias de atención primaria",
    "pau ", "cs ", "cap ",
]

_PUBLICO_OPERADOR = [
    "sermas", "comunidad de madrid", "insalud", "sns",
    "salud madrid", "servicio madrileño", "servicio de salud",
    "junta de andalucía", "junta de andalucia",
    "generalitat", "xunta", "osakidetza", "sacyl",
    "gobierno de españa", "ministerio de sanidad",
    "diputación", "diputacion", "ayuntamiento",
]


def _es_valido(nombre: str, tags: dict) -> bool:
    n   = nombre.lower()
    op  = tags.get("operator", "").lower()
    amenity    = tags.get("amenity", "")
    healthcare = tags.get("healthcare", "")

    # 1. Excluir si el nombre contiene palabras de centro privado
    if any(p in n for p in _PRIVADO_NOMBRE):
        return False

    # 2. Excluir si el operador es claramente privado
    if any(p in op for p in _PRIVADO_OPERADOR):
        return False

    # 3. Aceptar si el operador es claramente público
    if any(p in op for p in _PUBLICO_OPERADOR):
        return True

    # 4. Aceptar si el nombre contiene palabras de centro público
    if any(p in n for p in _PUBLICO_NOMBRE):
        return True

    # 5. Aceptar hospitales sin señales de ser privado
    if amenity == "hospital" or healthcare == "hospital":
        return True

    # 6. Aceptar clínicas/centros de salud sin señales privadas
    if amenity == "clinic" or healthcare in ("clinic", "centre", "health_centre"):
        return True

    return False


def geocodificar(direccion: str) -> tuple[float, float] | None:
    """
    Geocodifica con Nominatim.
    Si no hay coma (sin ciudad explícita), añade ', España'.
    """
    addr = direccion.strip()
    if "," not in addr:
        addr = f"{addr}, España"

    q = urllib.parse.urlencode({
        "q": addr,
        "format": "json",
        "limit": "1",
        "countrycodes": "es",
        "addressdetails": "1",
    })
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{q}", headers=_HEADERS
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None
    except urllib.error.URLError as e:
        print(f"[NexaCare] Error Nominatim: {e}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[NexaCare] Respuesta inesperada de Nominatim: {e}")
        return None


def buscar_centros(
    lat: float,
    lon: float,
    radio_m: int = 10_000,
    nivel_color: str = "green",
) -> list[dict]:
    """
    Busca hospitales y centros de salud/ambulatorios públicos cercanos.
    Incluye: amenity=hospital, amenity=clinic, healthcare=clinic/centre/hospital.
    Si no hay resultados, amplía el radio a 20 km automáticamente.
    Si nivel es rojo/naranja, prioriza hospitales con urgencias.
    """
    urgente = nivel_color in ("red", "orange")

    for radio in (radio_m, radio_m * 2):
        centros = _query_centros(lat, lon, radio, urgente)
        if centros:
            return centros

    return []


def _query_centros(lat: float, lon: float, radio_m: int, urgente: bool) -> list[dict]:
    """Ejecuta la consulta Overpass y devuelve los centros filtrados y ordenados."""
    query = f"""[out:json][timeout:30];
(
  nwr["amenity"="hospital"](around:{radio_m},{lat},{lon});
  nwr["amenity"="clinic"](around:{radio_m},{lat},{lon});
  nwr["healthcare"="hospital"](around:{radio_m},{lat},{lon});
  nwr["healthcare"="clinic"](around:{radio_m},{lat},{lon});
  nwr["healthcare"="centre"](around:{radio_m},{lat},{lon});
  nwr["healthcare"="health_centre"](around:{radio_m},{lat},{lon});
);
out center tags;"""

    data_enc = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=data_enc,
        headers={**_HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
    except urllib.error.URLError as e:
        print(f"[NexaCare] Error Overpass API: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[NexaCare] Respuesta inválida de Overpass: {e}")
        return []

    centros: list[dict] = []

    for el in result.get("elements", []):
        tags   = el.get("tags", {})
        nombre = tags.get("name", "").strip()
        if not nombre or len(nombre) < 3:
            continue
        if not _es_valido(nombre, tags):
            continue

        # Coordenadas: nodes tienen lat/lon directo; ways/relations usan center
        if el["type"] == "node":
            clat = el.get("lat")
            clon = el.get("lon")
        else:
            centro = el.get("center", {})
            clat = centro.get("lat")
            clon = centro.get("lon")

        if clat is None or clon is None:
            continue
        try:
            clat, clon = float(clat), float(clon)
            if not (-90 <= clat <= 90 and -180 <= clon <= 180):
                continue
        except (ValueError, TypeError):
            continue

        dist       = _haversine(lat, lon, clat, clon)
        amenity    = tags.get("amenity", "")
        healthcare = tags.get("healthcare", "")
        es_hospital = amenity == "hospital" or healthcare == "hospital"
        tiene_urg   = (
            es_hospital
            or tags.get("emergency") == "yes"
            or "urgencia" in nombre.lower()
        )

        # Determinar tipo legible
        n_lower = nombre.lower()
        if es_hospital:
            tipo  = "Hospital"
            icono = "🏥"
        elif any(p in n_lower for p in ("ambulatorio", "centro de salud", "cs ", "cap ")):
            tipo  = "Ambulatorio"
            icono = "🏠"
        else:
            tipo  = "Centro de Salud"
            icono = "🏠"

        centros.append({
            "nombre":      nombre,
            "tipo":        tipo,
            "icono":       icono,
            "distancia_m": dist,
            "urgencias":   tiene_urg,
            "es_hospital": es_hospital,
            "lat":         clat,
            "lon":         clon,
            "maps_url":    f"https://www.google.com/maps/dir/?api=1&destination={clat},{clon}",
        })

    if not centros:
        return []

    # Ordenar: urgente → hospitales primero, luego distancia; normal → solo distancia
    if urgente:
        centros.sort(key=lambda x: (not x["es_hospital"], x["distancia_m"]))
    else:
        centros.sort(key=lambda x: x["distancia_m"])

    # Deduplicar por nombre normalizado (máx 5 resultados)
    vistos: set[str] = set()
    resultado: list[dict] = []
    for c in centros:
        key = c["nombre"].lower().strip()
        if key not in vistos:
            vistos.add(key)
            resultado.append(c)
        if len(resultado) >= 5:
            break

    return resultado


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def formatear_distancia(metros: int) -> str:
    return f"{metros} m" if metros < 1_000 else f"{metros / 1_000:.1f} km"
