"""
API endpoints for season management.
"""
from flask import Blueprint, jsonify
import logging
import asyncio

logger = logging.getLogger(__name__)

# Create the Blueprint for season endpoints
blueprint = Blueprint('seasons', __name__)

@blueprint.route("/end", methods=["POST"])
def end_current_season():
    """
    End the current season and clean up all related data.
    """
    # Import here to avoid circular dependencies at startup
    from web.app import game_state, socketio
    
    if not game_state["is_running"]:
        return jsonify({"success": False, "message": "No active season to end."})

    logger.info("API call to end current season...")
    try:
        if game_state.get("game_loop"):
            loop = game_state["game_loop"]
            asyncio.run(loop.end_game())
        
        # Reset server state
        game_state["is_running"] = False
        game_state["status"] = "Idle"
        game_state["game_loop"] = None
        
        socketio.emit('game_state', {"status": "Idle", "message": "Season ended. All data archived and cleared."}, broadcast=True)
        logger.info("Season ended and data cleared via API.")
        return jsonify({"success": True, "message": "Season ended successfully"})
    except Exception as e:
        logger.error(f"Error ending season: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@blueprint.route("/", methods=["GET"])
def get_seasons():
    """Get all seasons"""
    # Placeholder for fetching season data from a persistent store
    return jsonify({"seasons": []})

@blueprint.route("/<int:season_id>", methods=["GET"])
def get_season(season_id):
    """Get a specific season by ID"""
    # Placeholder for fetching season data from a persistent store
    return jsonify({"season_id": season_id, "name": f"Season {season_id}"})
