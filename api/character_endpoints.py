"""
API endpoints for character management.
"""
from flask import Blueprint, jsonify, request
from storage.database.db_handler import db_handler
import logging

logger = logging.getLogger(__name__)

# Create the Blueprint for character endpoints
blueprint = Blueprint('characters', __name__)

@blueprint.route("/", methods=["GET"])
def get_all_characters():
    """Get all characters"""
    try:
        characters_collection = db_handler.get_collection("characters")
        characters = list(characters_collection.find({}))
        
        # Convert ObjectId to string for JSON serialization
        for char in characters:
            char["id"] = str(char["_id"])
            del char["_id"]
            
        return jsonify(characters)
    except Exception as e:
        logger.error(f"Error fetching characters: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@blueprint.route("/<character_id>", methods=["GET"])
def get_character(character_id):
    """Get a specific character by ID"""
    try:
        characters_collection = db_handler.get_collection("characters")
        character = characters_collection.find_one({"_id": character_id})
        
        if not character:
            return jsonify({"error": "Character not found"}), 404
            
        character["id"] = str(character["_id"])
        del character["_id"]
        
        return jsonify(character)
    except Exception as e:
        logger.error(f"Error fetching character: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
