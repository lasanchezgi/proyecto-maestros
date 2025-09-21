"""Business logic for obras endpoints."""
from __future__ import annotations

import math
from typing import Dict, Iterable, Mapping, Optional, Tuple

from app.repositories.obras_repository import list_obras, list_obras_by_autor
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


def _parse_float(value: Optional[str], *, field: str) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"El parámetro '{field}' debe ser numérico.") from exc


def _parse_geolocation(params: Mapping[str, str]) -> Tuple[Optional[Dict[str, float]], Optional[float], Optional[float], Optional[float]]:
    lat_raw = params.get("lat")
    lon_raw = params.get("lon")
    radius_raw = params.get("radius")
    provided = [value for value in (lat_raw, lon_raw, radius_raw) if value not in (None, "")]
    if not provided:
        return None, None, None, None
    if None in (lat_raw, lon_raw, radius_raw) or "" in (lat_raw or "", lon_raw or "", radius_raw or ""):
        raise ValueError("Debe proporcionar 'lat', 'lon' y 'radius' juntos.")

    lat = _parse_float(lat_raw, field="lat")
    lon = _parse_float(lon_raw, field="lon")
    radius = _parse_float(radius_raw, field="radius")

    if lat is None or lon is None or radius is None:
        raise ValueError("Debe proporcionar 'lat', 'lon' y 'radius'.")
    if not -90 <= lat <= 90:
        raise ValueError("El parámetro 'lat' debe estar entre -90 y 90.")
    if not -180 <= lon <= 180:
        raise ValueError("El parámetro 'lon' debe estar entre -180 y 180.")
    if radius <= 0:
        raise ValueError("El parámetro 'radius' debe ser mayor que 0.")

    near = {"lat": lat, "lon": lon, "radius": radius}
    return near, lat, lon, radius


def _rows_to_dicts(rows: Iterable) -> list[Dict[str, object]]:
    obras = []
    for row in rows:
        (
            obra_id,
            nombre,
            autor_id,
            autor_nombre,
            anio,
            tipo,
            comuna,
            barrio,
            direccion,
            descripcion,
            lat,
            lon,
        ) = row
        obras.append(
            {
                "id": obra_id,
                "nombre": nombre,
                "autor_id": autor_id,
                "autor": autor_nombre,
                "anio": anio,
                "tipo": tipo,
                "comuna": comuna,
                "barrio": barrio,
                "direccion": direccion,
                "descripcion": descripcion,
                "lat": lat,
                "lon": lon,
            }
        )
    return obras


def _build_filters(
    *,
    autor: Optional[str],
    comuna: Optional[str],
    tipo: Optional[str],
    anio: Optional[int],
    limit: int,
    lat: Optional[float],
    lon: Optional[float],
    radius: Optional[float],
) -> Dict[str, object]:
    return {
        "autor": autor or "",
        "comuna": comuna or "",
        "tipo": tipo or "",
        "anio": str(anio) if anio is not None else "",
        "limit": limit,
        "lat": "" if lat is None else str(lat),
        "lon": "" if lon is None else str(lon),
        "radius": "" if radius is None else str(radius),
    }


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


def get_obras(params: Mapping[str, str]) -> Dict[str, object]:
    """Return obras list with pagination metadata based on query parameters."""
    limit = _parse_limit(params.get("limit"))
    offset = _parse_offset(params.get("offset"))
    anio = _parse_int(params.get("anio"), field="anio")
    near, lat, lon, radius = _parse_geolocation(params)
    autor = params.get("autor")
    comuna = params.get("comuna")
    tipo = params.get("tipo")

    conn = get_connection()
    try:
        rows, total = list_obras(
            conn,
            autor=autor,
            comuna=comuna,
            tipo=tipo,
            anio=anio,
            near=near,
            limit=limit,
            offset=offset,
        )
    finally:
        conn.close()

    items = _rows_to_dicts(rows)
    meta = _build_meta(total, limit, offset, len(items))
    filters = _build_filters(
        autor=autor,
        comuna=comuna,
        tipo=tipo,
        anio=anio,
        limit=limit,
        lat=lat,
        lon=lon,
        radius=radius,
    )

    return {
        "items": items,
        "meta": meta,
        "filters": filters,
    }


def get_obras_by_autor(autor_id: int, params: Mapping[str, str]) -> Dict[str, object]:
    """Return obras for a specific author with pagination metadata."""
    limit = _parse_limit(params.get("limit"))
    offset = _parse_offset(params.get("offset"))
    anio = _parse_int(params.get("anio"), field="anio")
    comuna = params.get("comuna")
    tipo = params.get("tipo")

    conn = get_connection()
    try:
        rows, total = list_obras_by_autor(
            conn,
            autor_id,
            comuna=comuna,
            tipo=tipo,
            anio=anio,
            limit=limit,
            offset=offset,
        )
    finally:
        conn.close()

    items = _rows_to_dicts(rows)
    meta = _build_meta(total, limit, offset, len(items))
    filters = _build_filters(
        autor=None,
        comuna=comuna,
        tipo=tipo,
        anio=anio,
        limit=limit,
        lat=None,
        lon=None,
        radius=None,
    )

    return {
        "items": items,
        "meta": meta,
        "filters": filters,
    }
