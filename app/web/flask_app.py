from flask import Flask

from app.web.routes.autores_routes import autores_bp
from app.web.routes.home_routes import home_bp
from app.web.routes.mapa_routes import mapa_bp
from app.web.routes.obras_routes import obras_bp

def create_app():
    app = Flask(__name__)

    # Registrar blueprints sin prefijos adicionales para respetar rutas declaradas
    app.register_blueprint(home_bp)
    app.register_blueprint(obras_bp)
    app.register_blueprint(autores_bp)
    app.register_blueprint(mapa_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
