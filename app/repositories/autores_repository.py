"""Repository layer for autores queries."""
from __future__ import annotations

from typing import Any, List, Optional, Tuple


AutorRow = Tuple[int, str]
AutorWithCountRow = Tuple[int, str, int]


_DEF_CTE = (
    "WITH agg AS ("
    "SELECT a.id, a.nombre, COUNT(o.id) AS total_obras "
    "FROM autores a "
    "LEFT JOIN obras o ON o.autor_id = a.id "
    "GROUP BY a.id"
    ") "
)


def _build_filters(
    nombre: Optional[str],
    min_obras: Optional[int],
    max_obras: Optional[int],
) -> Tuple[str, List[Any]]:
    clauses: List[str] = []
    params: List[Any] = []

    if nombre:
        clauses.append("agg.nombre ILIKE %s")
        params.append(f"%{nombre}%")
    if min_obras is not None:
        clauses.append("agg.total_obras >= %s")
        params.append(min_obras)
    if max_obras is not None:
        clauses.append("agg.total_obras <= %s")
        params.append(max_obras)

    where_sql = ""
    if clauses:
        where_sql = " WHERE " + " AND ".join(clauses)

    return where_sql, params


def list_autores(
    conn,
    *,
    nombre: Optional[str] = None,
    min_obras: Optional[int] = None,
    max_obras: Optional[int] = None,
    limit: int,
    offset: int,
) -> Tuple[List[AutorWithCountRow], int]:
    """Return autores rows and total count applying filters and pagination."""
    where_sql, params = _build_filters(nombre, min_obras, max_obras)

    with conn.cursor() as cur:
        count_sql = _DEF_CTE + f" SELECT COUNT(*) FROM agg{where_sql}"
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        data_sql = (
            _DEF_CTE
            + " SELECT agg.id, agg.nombre, agg.total_obras "
            + f" FROM agg{where_sql} "
            + "ORDER BY agg.nombre ASC "
            + "LIMIT %s OFFSET %s"
        )
        cur.execute(data_sql, [*params, limit, offset])
        rows = cur.fetchall()

    return rows, total


def get_autor(conn, autor_id: int) -> Optional[AutorRow]:
    """Return single author or None."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre FROM autores WHERE id = %s", (autor_id,))
        return cur.fetchone()
