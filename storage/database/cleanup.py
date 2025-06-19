"""
Database cleanup utilities for ending seasons and clearing game data.
"""
from . import db_handler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def end_season():
    """
    End the current season by clearing all game data from the database.
    Character and conversation data will be removed.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Starting season cleanup process...")
        
        # Get database collections
        characters_collection = db_handler.get_collection("characters")
        conversations_collection = db_handler.get_collection("conversations")
        messages_collection = db_handler.get_collection("messages")
        message_history_collection = db_handler.get_collection("message_history")
        relationships_collection = db_handler.get_collection("relationships")
        
        # Clear all game data
        logger.info("Removing character data...")
        character_result = characters_collection.delete_many({})
        
        logger.info("Removing conversation data...")
        conversation_result = conversations_collection.delete_many({})
        
        logger.info("Removing message data...")
        message_result = messages_collection.delete_many({})
        
        logger.info("Removing message history...")
        history_result = message_history_collection.delete_many({})
        
        logger.info("Removing relationship data...")
        relationship_result = relationships_collection.delete_many({})
        
        # Reset world state to default
        world_state_collection = db_handler.get_collection("world_state")
        world_state_collection.update_one(
            {"_id": "singleton_world_state"},
            {"$set": {
                "current_scene": "the_tavern",
                "active_events": ["rumors_of_treasure"],
                "environmental_factors": {
                    "time_of_day": "evening",
                    "weather": "clear"
                }
            }},
            upsert=True
        )
        
        # Log cleanup results
        logger.info(f"Cleanup completed: Removed {character_result.deleted_count} characters, "
                   f"{conversation_result.deleted_count} conversations, "
                   f"{message_result.deleted_count} messages, "
                   f"{history_result.deleted_count} history entries, "
                   f"{relationship_result.deleted_count} relationships")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during season cleanup: {str(e)}")
        return False

def archive_season(season_id=None):
    """
    End the current season or a specific season by ID by archiving it.
    This performs cleanup tasks such as archiving data and resetting state.
    
    Args:
        season_id: Optional ID of the season to end. If None, ends the current season.
    
    Returns:
        dict: Result information about the ended season
    """
    db = db_handler
    
    # If no season ID provided, get the current active season
    if season_id is None:
        current_season = db.get_collection("seasons").find_one({"active": True})
        if current_season:
            season_id = current_season["_id"]
        else:
            return {"error": "No active season found"}
    
    # Update the season status
    result = db.get_collection("seasons").update_one(
        {"_id": season_id},
        {
            "$set": {
                "active": False,
                "end_date": datetime.utcnow(),
                "status": "completed"
            }
        }
    )
    
    if result.modified_count == 0:
        return {"error": f"Failed to end season {season_id} or season not found"}
    
    # Archive season data if needed
    # (This could move data to archive collections or perform other cleanup)
    
    return {
        "success": True,
        "season_id": season_id,
        "message": f"Season {season_id} ended successfully",
        "timestamp": datetime.utcnow()
    }
