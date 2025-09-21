"""Repository layer for obra queries."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


ObraRow = Tuple[
    int,
    str,
    int,
    str,
    Optional[int],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[float],
    Optional[float],
]


def _build_filters(
    autor: Optional[str],
    comuna: Optional[str],
    tipo: Optional[str],
    anio: Optional[int],
    autor_id: Optional[int],
    near: Optional[Dict[str, float]],
) -> Tuple[str, List[Any]]:
    """Build WHERE clause and parameter list."""
    clauses: List[str] = []
    params: List[Any] = []

    if autor_id is not None:
        clauses.append("o.autor_id = %s")
        params.append(autor_id)
    if autor:
        clauses.append("a.nombre ILIKE %s")
        params.append(f"%{autor}%")
    if comuna:
        clauses.append("o.comuna = %s")
        params.append(comuna)
    if tipo:
        clauses.append("o.tipo = %s")
        params.append(tipo)
    if anio is not None:
        clauses.append("o.anio = %s")
        params.append(anio)
    if near:
        clauses.append(
            "ST_DWithin(o.ubicacion::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)"
        )
        params.extend([near["lon"], near["lat"], near["radius"]])

    where_sql = ""
    if clauses:
        where_sql = " WHERE " + " AND ".join(clauses)

    return where_sql, params


def list_obras(
    conn,
    *,
    autor: Optional[str] = None,
    comuna: Optional[str] = None,
    tipo: Optional[str] = None,
    anio: Optional[int] = None,
    near: Optional[Dict[str, float]] = None,
    limit: int,
    offset: int,
) -> Tuple[List[ObraRow], int]:
    """Return obras rows and total count applying filters and pagination."""
    where_sql, params = _build_filters(autor, comuna, tipo, anio, None, near)

    with conn.cursor() as cur:
        count_sql = (
            "SELECT COUNT(*) FROM obras o JOIN autores a ON o.autor_id = a.id"
            f"{where_sql}"
        )
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        data_sql = (
            "SELECT o.id, o.nombre, o.autor_id, a.nombre, o.anio, o.tipo, o.comuna, "
            "o.barrio, o.direccion, o.descripcion, "
            "CASE WHEN o.ubicacion IS NOT NULL THEN ST_Y(o.ubicacion::geometry) END AS lat, "
            "CASE WHEN o.ubicacion IS NOT NULL THEN ST_X(o.ubicacion::geometry) END AS lon "
            "FROM obras o JOIN autores a ON o.autor_id = a.id "
            f"{where_sql} "
            "ORDER BY o.anio DESC NULLS LAST, o.id ASC "
            "LIMIT %s OFFSET %s"
        )
        cur.execute(data_sql, [*params, limit, offset])
        rows: List[ObraRow] = cur.fetchall()

    return rows, total


def list_obras_by_autor(
    conn,
    autor_id: int,
    *,
    comuna: Optional[str] = None,
    tipo: Optional[str] = None,
    anio: Optional[int] = None,
    limit: int,
    offset: int,
) -> Tuple[List[ObraRow], int]:
    """Return obras for a given author with optional filters."""
    where_sql, params = _build_filters(None, comuna, tipo, anio, autor_id, None)

    with conn.cursor() as cur:
        count_sql = (
            "SELECT COUNT(*) FROM obras o JOIN autores a ON o.autor_id = a.id"
            f"{where_sql}"
        )
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        data_sql = (
            "SELECT o.id, o.nombre, o.autor_id, a.nombre, o.anio, o.tipo, o.comuna, "
            "o.barrio, o.direccion, o.descripcion, "
            "CASE WHEN o.ubicacion IS NOT NULL THEN ST_Y(o.ubicacion::geometry) END AS lat, "
            "CASE WHEN o.ubicacion IS NOT NULL THEN ST_X(o.ubicacion::geometry) END AS lon "
            "FROM obras o JOIN autores a ON o.autor_id = a.id "
            f"{where_sql} "
            "ORDER BY o.anio DESC NULLS LAST, o.id ASC "
            "LIMIT %s OFFSET %s"
        )
        cur.execute(data_sql, [*params, limit, offset])
        rows: List[ObraRow] = cur.fetchall()

    return rows, total
