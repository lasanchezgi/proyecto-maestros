from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def home_page():
    """Render landing page for Proyecto Maestro(s)."""
    return render_template("home.html")
