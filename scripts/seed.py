import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage.database import db_handler

# Attribute Pools
personality_pool = [
    "curious", "gruff", "wise", "playful", "mysterious", "brave", "cautious", "energetic",
    "ambitious", "compassionate", "cynical", "deceitful", "honorable", "humble", "impulsive",
    "jaded", "melancholic", "methodical", "pessimistic", "stoic", "whimsical", "gregarious"
]
background_pool = [
    "explorer", "mechanic", "scholar", "artist", "warrior", "merchant", "hermit", "inventor",
    "assassin", "baker", "diplomat", "doctor", "farmer", "guard", "musician", "navigator",
    "priest", "smuggler", "spy", "tinkerer", "cartographer", "librarian"
]
trait_pool = [
    "loyal", "sarcastic", "optimistic", "stubborn", "creative", "analytical", "empathetic",
    "rebellious", "arrogant", "charming", "clumsy", "cowardly", "disciplined", "gullible",
    "patient", "paranoid", "resourceful", "vain", "witty", "zealous", "forgetful", "graceful"
]
voice_pool = ["alto", "bass", "soprano", "tenor", "raspy", "smooth", "young", "elderly"]

# New Pools
ethnicity_pool = [
    "Aethelgardian", "Bjorning", "Cymric", "Dornishman", "Eldorian", "Fjornlander", "Gaelic",
    "Highlander", "Icenian", "Jute", "Khemrian", "Lombard", "Mycenaean", "Norseman", "Ostrogoth",
    "Pict", "Quendonian", "Romanesque", "Saxon", "Thracian", "Umberian", "Vandal", "Wessexian"
]
religion_pool = [
    "Sun-worshipper (Dawnbreaker Sect)", "Moon-cultist (Shadow-weaver Sect)", "Ancestor Veneration (Spirit-speaker Clan)",
    "The Old Ways (Druidic Circle)", "Forge God Devotee (Iron-hand Order)", "Sea Titan Follower (Tide-caller Cult)",
    "Celestialism (Stargazer's Concordance)", "Path of the Void (Silent Brotherhood)", "Nature's Balance (Greenwood Covenant)",
    "The Unseen Path (Seekers of Knowledge)", "Blood Rite Cult (Crimson Guard)", "Divine Monarchy (Throne-Sworn)",
    "Fate Weavers (Tapestry Coven)", "Chaos Embrace (Mawsworn)", "Order of the Serpent (Venomous Disciples)"
]
mental_illness_pool = [
    "Chronic Anxiety", "Paranoid Tendencies", "Obsessive Compulsions", "Manic Episodes", "Severe Melancholy (Depression)",
    "Amnesiac Fugues", "Identity Dysphoria", "Auditory Hallucinations", "Visual Hallucinations", "Messiah Complex",
    "Pathological Lying", "Hoarding Disorder", "Social Phobia", "PTSD Flashbacks", "Apathy Syndrome"
]
subconscious_trait_pool = [
    "Fear of abandonment", "Imposter syndrome", "A deep-seated need for validation", "Aversion to authority",
    "Unresolved grief", "A savior complex", "A desire for chaos", "Crippling perfectionism", "A phobia of failure",
    "Subconscious self-loathing", "A secret desire for a simple life", "Repressed memories", "An unyielding sense of duty",
    "A hidden rebellious streak", "A profound sense of loneliness"
]

def seed_database():
    """
    Seeds the database with attribute pools and initial world state.
    Characters are generated dynamically by the CharacterEngine.
    """
    print("Seeding database...")
    print(f"Connecting to MongoDB at {db_handler.client.address}...")

    # Get collections
    characters_collection = db_handler.get_collection("characters")
    conversations_collection = db_handler.get_collection("conversations")
    messages_collection = db_handler.get_collection("messages")
    message_history_collection = db_handler.get_collection("message_history")
    world_state_collection = db_handler.get_collection("world_state")
    relationships_collection = db_handler.get_collection("relationships")
    attribute_pools_collection = db_handler.get_collection("attribute_pools")

    # Clear existing data
    print("Clearing existing data...")
    for collection in [
        characters_collection, conversations_collection, messages_collection,
        message_history_collection, world_state_collection,
        relationships_collection, attribute_pools_collection
    ]:
        collection.delete_many({})

    # Seed all attribute pools
    print("Seeding attribute pools...")
    all_pools = {
        "personality_pool": personality_pool,
        "background_pool": background_pool,
        "trait_pool": trait_pool,
        "voice_pool": voice_pool,
        "ethnicity_pool": ethnicity_pool,
        "religion_pool": religion_pool,
        "mental_illness_pool": mental_illness_pool,
        "subconscious_trait_pool": subconscious_trait_pool,
    }

    for pool_id, values in all_pools.items():
        attribute_pools_collection.insert_one({"_id": pool_id, "values": values})
    print(f"Seeded {len(all_pools)} attribute pools.")

    # Seed initial world state
    print("Seeding world state...")
    world_state = {
        "_id": "singleton_world_state",
        "current_scene": "the_tavern",
        "active_events": ["rumors_of_treasure"],
        "environmental_factors": {
            "time_of_day": "evening",
            "weather": "clear"
        }
    }
    world_state_collection.insert_one(world_state)
    print("Seeded world state.")

    print("Database seeding complete.")

if __name__ == "__main__":
    seed_database()
