"""
API package initializer that configures all routes.
"""

from flask import Blueprint, Flask, jsonify

def init_api_routes(app: Flask, api_logger, llm_logger):
    """Initialize all API routes with the Flask application"""
    # Import endpoint modules here to avoid premature instantiation.
    from . import character_endpoints
    from . import season_endpoints

    api_bp = Blueprint('api', __name__, url_prefix='/api')

    # Simple health check
    @api_bp.route('/health')
    def health_check():
        api_logger.info("Health check endpoint was called.")
        return jsonify({"status": "healthy"})

    # Register nested blueprints
    api_bp.register_blueprint(character_endpoints.blueprint, url_prefix="/characters")
    api_bp.register_blueprint(season_endpoints.blueprint, url_prefix="/seasons")

    app.register_blueprint(api_bp)
