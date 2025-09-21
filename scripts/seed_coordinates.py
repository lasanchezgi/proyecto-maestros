"""Seed minimal coordinates for iconic obras in Medellín."""
from __future__ import annotations

import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from contextlib import closing

from app.utils.database import get_connection

OBRAS_COORDS = [
    {"nombre": "cacique nutibara - cerro nutibara", "lat": 6.2447, "lon": -75.5794},
    {"nombre": "el cacique nutibara - plazuela nutibara", "lat": 6.2470, "lon": -75.5750},
    {"nombre": "antonio nariño", "lat": 6.282458, "lon": -75.5611601},
    {"nombre": "atanasio girardot", "lat": 6.2500, "lon": -75.5700},
    {"nombre": "carlos castro saavedra", "lat": 6.2600, "lon": -75.5650},
    {"nombre": "el desafio de la raza", "lat": 6.2455, "lon": -75.5747},
    {"nombre": "andres escobar", "lat": 6.2520, "lon": -75.5680},
]


def update_coordinates() -> None:
    update_sql = """
        UPDATE obras
        SET ubicacion = ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::GEOGRAPHY
        WHERE nombre = %(nombre)s
    """

    updated = 0
    missing: list[str] = []

    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        for obra in OBRAS_COORDS:
            cur.execute(update_sql, obra)
            if cur.rowcount == 0:
                missing.append(obra["nombre"])
            else:
                updated += cur.rowcount
        conn.commit()

    print("✅ Coordenadas aplicadas.")
    print(f"   Obras actualizadas: {updated}")
    if missing:
        print("   No se encontró registro para:")
        for nombre in missing:
            print(f"     • {nombre}")


if __name__ == "__main__":
    update_coordinates()
