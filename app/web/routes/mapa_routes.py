from flask import Blueprint, jsonify, render_template

from app.repositories.obras_repository import list_obras
from app.utils.database import get_connection

mapa_bp = Blueprint("mapa", __name__)


@mapa_bp.route("/mapa", methods=["GET"])
def mapa_page():
    """Render interactive map page."""
    return render_template("mapa.html")


@mapa_bp.route("/api/obras_geo", methods=["GET"])
def obras_geo():
    """Return obras with geographic coordinates for the map."""
    conn = get_connection()
    try:
        rows, _ = list_obras(conn, limit=2000, offset=0)
    finally:
        conn.close()

    payload = []
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

        if lat is None or lon is None:
            continue

        payload.append(
            {
                "id": obra_id,
                "nombre": nombre,
                "autor": autor_nombre,
                "anio": anio,
                "tipo": tipo,
                "comuna": comuna,
                "lat": lat,
                "lon": lon,
            }
        )

    return jsonify({"items": payload, "total": len(payload)})
