from engine.logic import CharacterEngine
import asyncio

async def seed_test_data():
    print("Creating CharacterEngine instance...")
    engine = CharacterEngine()
    
    print("Generating test characters...")
    characters = engine.create_characters(2)
    
    print(f"Created {len(characters)} characters:")
    for char in characters:
        print(f"ID: {char['_id']}, Name: {char['name']}")
    
    return characters[0]['_id'] if characters else None

if __name__ == "__main__":
    character_id = asyncio.run(seed_test_data())
    print(f"\nUse this character ID for testing: {character_id}")
