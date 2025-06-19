"""
API package initializer that configures all routes.
"""

from flask import Blueprint, Flask

# Replace APIRouter with Blueprint
api_blueprint = Blueprint('api', __name__)

# Import endpoint modules
from . import character_endpoints
from . import season_endpoints

# Replace include_router with register_blueprint
# Assuming character_endpoints.router is now character_endpoints.blueprint
api_blueprint.register_blueprint(character_endpoints.blueprint, url_prefix="/characters")
api_blueprint.register_blueprint(season_endpoints.blueprint, url_prefix="/season")

def init_api_routes(app: Flask):
    """Initialize all API routes with the Flask application"""
    app.register_blueprint(api_blueprint, url_prefix="/api")
