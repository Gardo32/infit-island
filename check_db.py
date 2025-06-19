from storage.database.db_handler import db_handler

def check_characters():
    characters = list(db_handler.get_collection('characters').find({}, {'_id': 1, 'name': 1}))
    if not characters:
        print("No characters found in the database")
    else:
        print(f"Found {len(characters)} characters:")
        for char in characters:
            print(f"ID: {char.get('_id')}, Name: {char.get('name', 'Unknown')}")

if __name__ == "__main__":
    check_characters()
