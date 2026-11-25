import secrets

from flask import Flask, jsonify, render_template, request, session

from app.config import Config
from app.database.connection import close_connection


def create_app(config_object=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)
    app.teardown_appcontext(close_connection)

    from app.auth.routes import auth_bp
    from app.routes import main_bp
    from app.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.before_request
    def csrf_protection():
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            session.setdefault("csrf_token", secrets.token_urlsafe(32))
            return None
        supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not supplied or not secrets.compare_digest(supplied, session.get("csrf_token", "")):
            if request.path.startswith("/api/"):
                return jsonify(error={"code": "csrf_failed", "message": "Refresh the page and try again."}), 400
            return render_template("error.html", message="Your form expired. Refresh the page and try again."), 400
        return None

    @app.context_processor
    def template_globals():
        return {"csrf_token": session.get("csrf_token", "")}

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(error={"code": "not_found", "message": "The requested resource was not found."}), 404
        return render_template("error.html", message="The page you requested was not found."), 404

    @app.errorhandler(500)
    def internal_error(_error):
        if request.path.startswith("/api/"):
            return jsonify(error={"code": "internal_error", "message": "Something went wrong. Please try again."}), 500
        return render_template("error.html", message="Something went wrong. Please try again."), 500

    return app
