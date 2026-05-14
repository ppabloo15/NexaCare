"""
NexaCare — Buscador de centros sanitarios públicos
Solo hospitales públicos y centros de salud oficiales.
Geocoding: Nominatim con addressdetails para mayor precisión.
Datos: Overpass API (OSM). Sin API key.
"""
import math
import json
import urllib.request
import urllib.parse
import urllib.error

_HEADERS = {"User-Agent": "NexaCare-TFG-SMR/2.0 (proyecto academico TFG)"}

# Términos que indican centro PRIVADO → excluir siempre
_EXCLUIR = [
    "sanitas", "quirón", "quiron", "hm hospitals", "hm ",
    "vithas", "ruber", "teknon", "cemtro", "juaneda",
    "asisa", "adeslas", "imogas", "cuidados paliativos",
    "psicotécnico", "psicotecnico", "dental", "dentista",
    "veterinari", "farmacia", "óptica", "optica",
    "estética", "estetica", "venerable orden tercera",
    "especialidades", "privado", "privada",
]

# Términos que confirman que es PÚBLICO
_PUBLICO_KEYWORDS = [
    "hospital universitario", "hospital general",
    "centro de salud", "ambulatorio", "sermas",
]

# Operadores SNS conocidos
_OPERADORES_PUBLICOS = [
    "sermas", "comunidad de madrid", "insalud", "sns",
    "salud madrid", "gobierno de españa",
]


def _es_valido(nombre: str, tags: dict) -> bool:
    n = nombre.lower()
    # Excluir privados por nombre
    if any(p in n for p in _EXCLUIR):
        return False
    # Excluir por operador privado
    op = tags.get("operator", "").lower()
    if any(p in op for p in ["sanitas", "quirón", "quiron", "hm ", "vithas", "ruber"]):
        return False
    # Aceptar si el operador es claramente público
    if any(p in op for p in _OPERADORES_PUBLICOS):
        return True
    # Aceptar hospitales y centros de salud sin nombre privado
    amenity = tags.get("amenity", "")
    if amenity in ("hospital", "health_post"):
        return True
    return False


def geocodificar(direccion: str) -> tuple[float, float] | None:
    """
    Geocodifica con Nominatim. Si la dirección no contiene coma
    (sin ciudad explícita), añade ', España' para reducir ambigüedad.
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
    Busca hospitales y centros de salud públicos cercanos.
    Usa out center para obtener el centroide de ways/relations.
    Filtra privados y ordena por distancia real al centroide.
    Si el nivel es rojo/naranja, prioriza hospitales con urgencias.
    """
    urgente = nivel_color in ("red", "orange")

    # Query: hospitales + centros de salud en radio amplio
    query = f"""[out:json][timeout:30];
(
  node["amenity"="hospital"](around:{radio_m},{lat},{lon});
  way["amenity"="hospital"](around:{radio_m},{lat},{lon});
  relation["amenity"="hospital"](around:{radio_m},{lat},{lon});
  node["amenity"="health_post"](around:{radio_m},{lat},{lon});
  way["amenity"="health_post"](around:{radio_m},{lat},{lon});
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
        if not nombre or len(nombre) < 2:
            continue
        if not _es_valido(nombre, tags):
            continue

        # Obtener coordenadas del centroide (center para ways/relations)
        if el["type"] == "node":
            clat = el.get("lat", lat)
            clon = el.get("lon", lon)
        else:
            centro = el.get("center", {})
            clat = centro.get("lat")
            clon = centro.get("lon")
            if clat is None or clon is None:
                continue  # Saltar elementos sin centroide

        try:
            clat, clon = float(clat), float(clon)
            if not (-90 <= clat <= 90 and -180 <= clon <= 180):
                continue
        except (ValueError, TypeError):
            continue

        dist = _haversine(lat, lon, clat, clon)
        amenity     = tags.get("amenity", "")
        es_hospital = amenity == "hospital"
        tiene_urg   = (
            es_hospital
            or tags.get("emergency") == "yes"
            or "urgencia" in nombre.lower()
        )

        centros.append({
            "nombre":      nombre,
            "tipo":        "Hospital" if es_hospital else "Centro de Salud",
            "icono":       "🏥" if es_hospital else "🏠",
            "distancia_m": dist,
            "urgencias":   tiene_urg,
            "es_hospital": es_hospital,
            "maps_url":    f"https://www.google.com/maps/dir/?api=1&destination={clat},{clon}",
        })

    if not centros:
        return []

    # Ordenar siempre por distancia; si urgente: hospitales primero dentro del mismo rango
    if urgente:
        centros.sort(key=lambda x: (not x["es_hospital"], x["distancia_m"]))
    else:
        centros.sort(key=lambda x: x["distancia_m"])

    # Deduplicar por nombre completo normalizado
    vistos: set[str] = set()
    resultado: list[dict] = []
    for c in centros:
        key = c["nombre"].lower().strip()
        if key not in vistos:
            vistos.add(key)
            resultado.append(c)
        if len(resultado) >= 4:
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
