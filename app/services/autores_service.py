"""Business logic for autores endpoints."""
from __future__ import annotations

import math
from typing import Dict, Mapping, Optional

from app.repositories.autores_repository import get_autor, list_autores
from app.services.obras_service import get_obras_by_autor
from app.utils.database import get_connection

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


def _parse_int(value: Optional[str], *, field: str) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"El parámetro '{field}' debe ser numérico.") from exc


def _parse_limit(value: Optional[str]) -> int:
    limit = _parse_int(value, field="limit") if value is not None else DEFAULT_LIMIT
    if limit is None:
        limit = DEFAULT_LIMIT
    if limit <= 0:
        raise ValueError("El parámetro 'limit' debe ser mayor que 0.")
    return min(limit, MAX_LIMIT)


def _parse_offset(value: Optional[str]) -> int:
    offset = _parse_int(value, field="offset") if value is not None else 0
    if offset is None:
        offset = 0
    if offset < 0:
        raise ValueError("El parámetro 'offset' no puede ser negativo.")
    return offset


def _parse_non_negative(value: Optional[str], *, field: str) -> Optional[int]:
    parsed = _parse_int(value, field=field)
    if parsed is not None and parsed < 0:
        raise ValueError(f"El parámetro '{field}' no puede ser negativo.")
    return parsed


def _build_meta(total: int, limit: int, offset: int, page_items: int) -> Dict[str, object]:
    total_pages = max(1, math.ceil(total / limit)) if limit else 1
    page = 1
    if limit:
        page = (offset // limit) + 1
        page = min(max(1, page), total_pages)
    has_prev = page > 1
    has_next = page < total_pages
    prev_offset = (page - 2) * limit if has_prev else None
    next_offset = page * limit if has_next else None
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "count": page_items,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_offset": prev_offset,
        "next_offset": next_offset,
    }


def _build_filters(
    nombre: Optional[str],
    min_obras: Optional[int],
    max_obras: Optional[int],
    limit: int,
) -> Dict[str, object]:
    return {
        "nombre": nombre or "",
        "min_obras": "" if min_obras is None else str(min_obras),
        "max_obras": "" if max_obras is None else str(max_obras),
        "limit": limit,
    }


def get_autores(params: Mapping[str, str]) -> Dict[str, object]:
    """Return autores list with pagination metadata based on filters."""
    limit = _parse_limit(params.get("limit"))
    offset = _parse_offset(params.get("offset"))
    nombre = params.get("nombre")
    min_obras = _parse_non_negative(params.get("min_obras"), field="min_obras")
    max_obras = _parse_non_negative(params.get("max_obras"), field="max_obras")
    if min_obras is not None and max_obras is not None and min_obras > max_obras:
        raise ValueError("'min_obras' no puede ser mayor que 'max_obras'.")

    conn = get_connection()
    try:
        rows, total = list_autores(
            conn,
            nombre=nombre,
            min_obras=min_obras,
            max_obras=max_obras,
            limit=limit,
            offset=offset,
        )
    finally:
        conn.close()

    items = [
        {"id": autor_id, "nombre": nombre_row, "total_obras": total_obras}
        for autor_id, nombre_row, total_obras in rows
    ]
    meta = _build_meta(total, limit, offset, len(items))
    filters = _build_filters(nombre, min_obras, max_obras, limit)

    return {"items": items, "meta": meta, "filters": filters}


def get_autor_detail(autor_id: int, query_params: Mapping[str, str]) -> Dict[str, object]:
    """Return author metadata and paginated obras."""
    conn = get_connection()
    try:
        autor_row = get_autor(conn, autor_id)
    finally:
        conn.close()

    if not autor_row:
        raise LookupError("Autor no encontrado")

    obras = get_obras_by_autor(autor_id, query_params)

    return {
        "autor": {"id": autor_row[0], "nombre": autor_row[1]},
        "obras": obras,
    }
