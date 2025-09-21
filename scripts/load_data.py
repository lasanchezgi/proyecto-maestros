"""Load obras and autores data into PostGIS database."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from app.utils.database import get_connection

load_dotenv()

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "esculturas-publicas-medellin-limpio.csv"


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

    conn = get_connection()
    inserted_obras = 0
    skipped_obras = 0

    try:
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

                # Try insert avoiding duplicates by (nombre, autor, anio)
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
                        ubicacion
                    )
                    SELECT
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NULL,
                        %s,
                        NULL,
                        CASE
                            WHEN %s IS NOT NULL AND %s IS NOT NULL
                                THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                            ELSE NULL
                        END
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM obras o
                        WHERE
                            o.nombre = %s
                            AND o.autor_id = %s
                            AND (
                                (o.anio = %s) OR (o.anio IS NULL AND %s IS NULL)
                            )
                    )
                    RETURNING id
                    """,
                    (
                        nombre,
                        autor_id,
                        anio,
                        tipo,
                        comuna,
                        direccion,
                        lon,
                        lat,
                        lon,
                        lat,
                        nombre,
                        autor_id,
                        anio,
                        anio,
                    ),
                )
                if cur.fetchone():
                    inserted_obras += 1
                else:
                    skipped_obras += 1

        conn.commit()
    finally:
        conn.close()

    print(
        "✅ Carga completada. Obras insertadas: {0}, duplicados omitidos: {1}.".format(
            inserted_obras, skipped_obras
        )
    )


if __name__ == "__main__":
    load_data()
