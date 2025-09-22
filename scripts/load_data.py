"""Load obras and autores data into PostGIS database."""
from __future__ import annotations

import csv
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.utils.database import get_connection

load_dotenv()

DATA_PATH = PROJECT_ROOT / "data" / "esculturas-publicas-medellin-limpio.csv"


def _parse_year(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_data() -> None:
    """Load authors and obras from CSV into the database."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"No se encontró el CSV en {DATA_PATH}")

    inserted_obras = 0
    updated_obras = 0
    missing_coords = 0

    with closing(get_connection()) as conn:
        with conn.cursor() as cur, DATA_PATH.open(encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                autor_nombre = row.get("author") or "Autor desconocido"
                cur.execute(
                    (
                        "INSERT INTO autores (nombre) VALUES (%s) "
                        "ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre RETURNING id"
                    ),
                    (autor_nombre,),
                )
                autor_id = cur.fetchone()[0]

                nombre = row.get("name")
                anio = _parse_year(row.get("year"))
                tipo = row.get("type")
                comuna = row.get("area")
                direccion = row.get("general-direction")
                lat = _parse_float(row.get("latitude"))
                lon = _parse_float(row.get("longitude"))

                if lat is None or lon is None:
                    missing_coords += 1
                    lat_db = None
                    lon_db = None
                else:
                    lat_db = lat
                    lon_db = lon

                cur.execute(
                    "SELECT id FROM obras WHERE nombre = %s AND autor_id = %s LIMIT 1",
                    (nombre, autor_id),
                )
                existing = cur.fetchone()

                ubicacion_args = (lon_db, lat_db, lon_db, lat_db)

                if existing:
                    obra_id = existing[0]
                    cur.execute(
                        """
                        UPDATE obras
                        SET
                            anio = %s,
                            tipo = %s,
                            comuna = %s,
                            direccion = %s,
                            lat = %s,
                            lon = %s,
                            ubicacion = CASE
                                WHEN %s IS NOT NULL AND %s IS NOT NULL
                                    THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                                ELSE NULL
                            END
                        WHERE id = %s
                        """,
                        (
                            anio,
                            tipo,
                            comuna,
                            direccion,
                            lat_db,
                            lon_db,
                            *ubicacion_args,
                            obra_id,
                        ),
                    )
                    if cur.rowcount:
                        updated_obras += 1
                else:
                    cur.execute(
                        """
                        INSERT INTO obras (
                            nombre,
                            autor_id,
                            anio,
                            tipo,
                            comuna,
                            barrio,
                            direccion,
                            descripcion,
                            lat,
                            lon,
                            ubicacion
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            NULL,
                            %s,
                            NULL,
                            %s,
                            %s,
                            CASE
                                WHEN %s IS NOT NULL AND %s IS NOT NULL
                                    THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                                ELSE NULL
                            END
                        )
                        """,
                        (
                            nombre,
                            autor_id,
                            anio,
                            tipo,
                            comuna,
                            direccion,
                            lat_db,
                            lon_db,
                            *ubicacion_args,
                        ),
                    )
                    inserted_obras += 1

        conn.commit()

    print("✅ Carga completada")
    print(f"Obras insertadas: {inserted_obras}")
    print(f"Obras actualizadas: {updated_obras}")
    print(f"Obras sin coordenadas: {missing_coords}")


if __name__ == "__main__":
    load_data()
