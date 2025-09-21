from urllib.parse import urlencode

from flask import Blueprint, jsonify, render_template, request

from app.services.obras_service import get_obras


obras_bp = Blueprint("obras", __name__)


@obras_bp.route("/obras", methods=["GET"])
def obras_collection():
    """Return obras as JSON applying query filters."""
    try:
        data = get_obras(request.args)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(data)


def _build_page_url(base_params: dict[str, str], *, offset: int) -> str:
    params = base_params.copy()
    params["offset"] = str(offset)
    return "/obras/page?" + urlencode(params)


@obras_bp.route("/obras/page", methods=["GET"])
def obras_page():
    """Render obras list using server-side template."""
    try:
        data = get_obras(request.args)
    except ValueError as exc:
        empty_state = {
            "items": [],
            "meta": {
                "total": 0,
                "limit": 50,
                "offset": 0,
                "page": 1,
                "total_pages": 1,
                "has_prev": False,
                "has_next": False,
                "prev_offset": None,
                "next_offset": None,
                "count": 0,
            },
            "filters": {
                "autor": "",
                "comuna": "",
                "tipo": "",
                "anio": "",
                "limit": 50,
                "lat": "",
                "lon": "",
                "radius": "",
            },
        }
        return (
            render_template(
                "obras_list.html",
                items=empty_state["items"],
                filters=empty_state["filters"],
                meta=empty_state["meta"],
                pagination={"prev": None, "next": None},
                empty_message="No pudimos interpretar los filtros. Ajusta los valores e intenta de nuevo.",
                error=str(exc),
            ),
            400,
        )

    items = data["items"]
    filters = data["filters"]
    meta = data["meta"]
    empty_message = None
    if not items:
        empty_message = "No encontramos obras que coincidan con estos filtros."

    base_params = {
        "autor": filters["autor"],
        "comuna": filters["comuna"],
        "tipo": filters["tipo"],
        "anio": filters["anio"],
        "limit": str(filters["limit"]),
    }
    if filters.get("lat"):
        base_params["lat"] = filters["lat"]
    if filters.get("lon"):
        base_params["lon"] = filters["lon"]
    if filters.get("radius"):
        base_params["radius"] = filters["radius"]

    pagination = {"prev": None, "next": None}
    if meta.get("has_prev") and meta.get("prev_offset") is not None:
        pagination["prev"] = _build_page_url(base_params, offset=meta["prev_offset"])
    if meta.get("has_next") and meta.get("next_offset") is not None:
        pagination["next"] = _build_page_url(base_params, offset=meta["next_offset"])

    return render_template(
        "obras_list.html",
        items=items,
        filters=filters,
        meta=meta,
        pagination=pagination,
        empty_message=empty_message,
        error=None,
    )
