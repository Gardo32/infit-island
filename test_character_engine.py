import asyncio
import json
from bson.objectid import ObjectId
from engine.logic import CharacterEngine
from datetime import datetime

async def test_character_engine():
    print("Creating CharacterEngine instance...")
    engine = CharacterEngine()
    
    # Test character ID - modify this to an existing ID in your database
    character_id = "friendly-explorer"  # Replace with a valid ID from your database
    
    # Test interaction
    print(f"\nTesting interaction with character {character_id}...")
    interaction_result = await engine.interact(character_id, "Hello, how are you today?")
    
    print("\nInteraction Result:")
    print(json.dumps(interaction_result, indent=2, default=str))
    
    # Test observation
    print(f"\nTesting observation of character {character_id}...")
    observation_result = await engine.observe_character(character_id, "general", "The character is sitting alone by the pool.")
    
    print("\nObservation Result:")
    print(json.dumps(observation_result, indent=2, default=str))
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(test_character_engine())
