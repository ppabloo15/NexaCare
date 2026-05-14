"""
NexaCare — Base de datos SQLite
Gestiona el almacenamiento persistente de consultas de triaje.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexacare.db")


def init_db() -> None:
    """Crea la tabla de consultas si no existe y aplica migraciones de columnas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp         TEXT    NOT NULL,
            sintoma           TEXT    NOT NULL,
            respuestas        TEXT    NOT NULL,
            puntuacion        INTEGER NOT NULL,
            puntuacion_maxima INTEGER NOT NULL,
            porcentaje        INTEGER NOT NULL,
            nivel             TEXT    NOT NULL,
            informe_ai        TEXT,
            email             TEXT,
            token_informe     TEXT    UNIQUE
        )
    """)
    # Migraciones seguras por si la tabla ya existía sin estas columnas
    for col, typedef in [("email", "TEXT"), ("token_informe", "TEXT UNIQUE")]:
        try:
            conn.execute(f"ALTER TABLE consultas ADD COLUMN {col} {typedef}")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                print(f"[NexaCare DB] Aviso en migración de columna '{col}': {e}")
    conn.commit()
    conn.close()


def guardar_consulta(
    sintoma: str,
    respuestas: list[tuple[str, bool]],
    puntuacion: int,
    puntuacion_maxima: int,
    nivel: str,
    informe_ai: str | None = None,
    email: str | None = None,
    token_informe: str | None = None,
) -> None:
    """Guarda una consulta de triaje completa en la base de datos."""
    if not sintoma or not nivel:
        raise ValueError("sintoma y nivel no pueden estar vacíos")
    if puntuacion < 0 or puntuacion_maxima <= 0:
        raise ValueError(f"Puntuación inválida: {puntuacion}/{puntuacion_maxima}")
    porcentaje = int((puntuacion / puntuacion_maxima) * 100)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO consultas
           (timestamp, sintoma, respuestas, puntuacion, puntuacion_maxima,
            porcentaje, nivel, informe_ai, email, token_informe)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            sintoma,
            json.dumps(respuestas, ensure_ascii=False),
            puntuacion,
            puntuacion_maxima,
            porcentaje,
            nivel,
            informe_ai,
            email,
            token_informe,
        ),
    )
    conn.commit()
    conn.close()


def obtener_consultas(limit: int = 100) -> list[dict]:
    """Devuelve las últimas `limit` consultas ordenadas por fecha descendente."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """SELECT timestamp, sintoma, puntuacion, puntuacion_maxima, porcentaje, nivel
           FROM consultas ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "timestamp": r[0], "sintoma": r[1], "puntuacion": r[2],
            "maximo": r[3], "porcentaje": r[4], "nivel": r[5],
        }
        for r in rows
    ]


def obtener_consulta_por_token(token: str) -> dict | None:
    """Busca y devuelve una consulta por su token único, o None si no existe."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        """SELECT timestamp, sintoma, respuestas, puntuacion, puntuacion_maxima,
                  porcentaje, nivel, informe_ai, email
           FROM consultas WHERE token_informe = ?""",
        (token,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "timestamp": row[0], "sintoma": row[1],
        "respuestas": json.loads(row[2]),
        "puntuacion": row[3], "puntuacion_maxima": row[4],
        "porcentaje": row[5], "nivel": row[6],
        "informe_ai": row[7], "email": row[8],
    }


def obtener_stats() -> dict:
    """Devuelve estadísticas agregadas: total, distribución por nivel y por síntoma."""
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM consultas").fetchone()[0]
    nivel_rows = conn.execute(
        "SELECT nivel, COUNT(*) FROM consultas GROUP BY nivel"
    ).fetchall()
    sintoma_rows = conn.execute(
        "SELECT sintoma, COUNT(*) as n FROM consultas GROUP BY sintoma ORDER BY n DESC"
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "niveles_raw": dict(nivel_rows),
        "sintomas": dict(sintoma_rows),
    }
