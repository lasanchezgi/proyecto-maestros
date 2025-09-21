from urllib.parse import urlencode

from flask import Blueprint, jsonify, render_template, request

from app.services.autores_service import get_autor_detail, get_autores


autores_bp = Blueprint("autores", __name__)


@autores_bp.route("/autores", methods=["GET"])
def autores_collection():
    """Return authors with obra counts and pagination."""
    try:
        data = get_autores(request.args)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(data)


def _build_page_url(base_params: dict[str, str], *, offset: int) -> str:
    params = base_params.copy()
    params["offset"] = str(offset)
    return "/autores/page?" + urlencode(params)


@autores_bp.route("/autores/page", methods=["GET"])
def autores_page():
    """Render autores list using server-side template."""
    try:
        data = get_autores(request.args)
    except ValueError as exc:
        empty_state = {
            "items": [],
            "meta": {
                "total": 0,
                "limit": 50,
                "offset": 0,
                "page": 1,
                "total_pages": 1,
                "count": 0,
                "has_prev": False,
                "has_next": False,
                "prev_offset": None,
                "next_offset": None,
            },
            "filters": {
                "nombre": "",
                "min_obras": "",
                "max_obras": "",
                "limit": 50,
            },
        }
        return (
            render_template(
                "autores_list.html",
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
        empty_message = "No se encontraron autores con estos filtros."

    base_params = {
        "nombre": filters["nombre"],
        "min_obras": filters["min_obras"],
        "max_obras": filters["max_obras"],
        "limit": str(filters["limit"]),
    }

    pagination = {"prev": None, "next": None}
    if meta.get("has_prev") and meta.get("prev_offset") is not None:
        pagination["prev"] = _build_page_url(base_params, offset=meta["prev_offset"])
    if meta.get("has_next") and meta.get("next_offset") is not None:
        pagination["next"] = _build_page_url(base_params, offset=meta["next_offset"])

    return render_template(
        "autores_list.html",
        items=items,
        filters=filters,
        meta=meta,
        pagination=pagination,
        empty_message=empty_message,
        error=None,
    )


@autores_bp.route("/autores/<int:autor_id>", methods=["GET"])
def autores_detail(autor_id: int):
    """Return single author detail and its obras."""
    try:
        data = get_autor_detail(autor_id, request.args)
    except LookupError:
        return jsonify({"error": "Autor no encontrado"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(data)
