from engine.logic.character_engine import CharacterEngine
from storage.database import db_handler
import asyncio
from datetime import datetime
import json

class GameLoop:
    def __init__(self):
        """
        Initializes the game loop for director control.
        """
        self.character_engine = CharacterEngine()
        self.messages_collection = db_handler.get_collection("messages")
        self.conversations_collection = db_handler.get_collection("conversations")
        self.is_running = False
        print("Director control system initialized.")

    async def start(self):
        """
        Initializes the season for director control.
        """
        self.is_running = True
        print("New season ready for director control.")
        # Cast must be created via the director interface before the story can start.

    async def start_story(self):
        """
        Generates the season premiere introduction under director control.
        """
        characters = list(self.character_engine.characters_collection.find({}))
        if not characters:
            return "Cannot start the season premiere without any contestants."

        character_descriptions = []
        for char in characters:
            description = f"- **{char['name']}** aka {char['personality'][0]}: {char['background']}"
            character_descriptions.append(description)
        
        character_list_str = "\n".join(character_descriptions)
        
        prompt = f"""You are the AI narrator of "Voice Island", a reality TV show controlled by an external director.
Your tone is witty, dramatic, and a bit cheeky.

The director has assembled a new cast and is ready to begin the season premiere. Write the opening sequence as a JSON object.

The cast lineup:
{character_list_str}

Instructions:
1.  **dialogue**: A markdown string containing the opening sequence. It should include:
    - A dramatic title with emojis.
    - A description of the villa.
    - An introduction for each contestant.
    - The contestants meeting for the first time.
    - An announcement from the "Voice Island AI".
2.  **choices**: An array of 3-4 strings, representing narrative choices for the director.
"""
        
        # Define the schema for the response
        opening_schema = {
            "type": "object",
            "properties": {
                "dialogue": {
                    "type": "string",
                    "description": "Markdown-formatted opening narrative for the season premiere"
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-4 narrative choices for the director to select from"
                }
            },
            "required": ["dialogue", "choices"]
        }
        
        response_data = await self.character_engine.llm_handler.get_response(
            prompt, 
            model="gemma3:4b", 
            json_format=True,
            schema=opening_schema
        )
        
        if isinstance(response_data, dict):
            dialogue = response_data.get("dialogue", "")
            choices = response_data.get("choices", [])
        else:
            dialogue = "Error: The AI narrator provided an invalid response. Please try again."
            choices = []

        # Log this as a system message
        self.messages_collection.insert_one({
            "conversation_id": "SYSTEM_SEASON_START",
            "timestamp": datetime.utcnow(),
            "speaker_type": "system",
            "speaker_id": "NARRATOR",
            "content": dialogue,
            "choices": choices,
            "emotion": "dramatic",
            "director_control": True,
            "is_game_over": False
        })

        return { "dialogue": dialogue, "choices": choices, "is_game_over": False }

    async def progress_story(self, director_choice: str):
        """
        Progresses the story based on the director's narrative choice, generating a new chat-based scene.
        """
        characters = list(self.character_engine.characters_collection.find({}))
        if not characters:
            return {"dialogue": "Cannot progress the story without any contestants.", "choices": []}

        character_descriptions = [f"- **{char['name']}** ({', '.join(char['personality'])}, {char['background']})" for char in characters]
        character_list_str = "\n".join(character_descriptions)

        last_narrative_block = self.messages_collection.find_one(
            {"speaker_type": "system", "director_control": True}, 
            sort=[("timestamp", -1)]
        )
        
        story_context = ""
        if last_narrative_block and 'content' in last_narrative_block:
            summary = (last_narrative_block['content'][-700:])
            story_context = f"""The story so far:
...{{summary}}

The director chose: "{director_choice}" 
"""
        
        prompt = f"""You are the AI writer for "Voice Island", a chat-based reality TV show.
Your tone is witty, dramatic, and cheeky.

{story_context}

Continue the story based on the director's choice.

The cast:
{character_list_str}

Instructions:
- The new scene must be a direct result of the director's choice.
- Format it as a series of short chat messages from the Narrator and characters.
- Include dialogue from at least 2-3 characters.
- If the story ends, set `is_game_over` to true.
"""

        # Define schema for story progress
        progress_schema = {
            "type": "object",
            "properties": {
                "dialogue": {
                    "type": "string", 
                    "description": "A series of chat messages from the Narrator and characters"
                },
                "choices": {
                    "type": "array", 
                    "items": {"type": "string"}, 
                    "description": "3-4 narrative choices for the director"
                },
                "is_game_over": {
                    "type": "boolean", 
                    "description": "Whether this is the end of the story"
                }
            },
            "required": ["dialogue", "choices", "is_game_over"]
        }

        response_data = await self.character_engine.llm_handler.get_response(
            prompt, 
            model="gemma3:4b", 
            json_format=True,
            schema=progress_schema
        )
        
        if isinstance(response_data, dict):
            dialogue = response_data.get("dialogue", "")
            choices = response_data.get("choices", [])
            is_game_over = response_data.get("is_game_over", False)
        else:
            dialogue = "Error: The AI writer provided an invalid response. Please try again."
            choices = []
            is_game_over = False

        if is_game_over:
            self.stop()

        self.messages_collection.insert_one({
            "conversation_id": "SYSTEM_STORY_PROGRESS",
            "timestamp": datetime.utcnow(),
            "speaker_type": "system",
            "speaker_id": "NARRATOR",
            "content": dialogue,
            "choices": choices,
            "emotion": "dramatic",
            "director_control": True,
            "triggering_choice": director_choice,
            "is_game_over": is_game_over
        })

        return {"dialogue": dialogue, "choices": choices, "is_game_over": is_game_over}

    async def get_latest_story_segment(self):
        """
        Retrieves the latest story segment (dialogue and choices) from the database.
        """
        latest_segment = self.messages_collection.find_one(
            {"director_control": True},
            sort=[("timestamp", -1)]
        )

        if not latest_segment:
            return {"dialogue": "The story hasn't started yet.", "choices": [], "is_game_over": False}

        return {
            "dialogue": latest_segment.get("content", ""),
            "choices": latest_segment.get("choices", []),
            "is_game_over": latest_segment.get("is_game_over", False)
        }

    async def manage_history(self, conversation_id: str):
        """
        Manages conversation history, including summarization.
        """
        message_count = self.messages_collection.count_documents({"conversation_id": conversation_id})
          # Summarize every 20 messages (10 pairs of player/character messages)
        if message_count > 0 and message_count % 20 == 0:
            print(f"\n[System: Conversation {conversation_id} has {message_count} messages. Triggering summarization.]")
            messages_cursor = self.messages_collection.find({"conversation_id": conversation_id}).sort("timestamp", 1)
            history_text = "\n".join([f"{m['speaker_id']}: {m['content']}" for m in messages_cursor])
            
            # Get JSON-formatted summary
            summary_data = await self.character_engine.llm_handler.summarize_conversation(history_text, json_format=True)
            
            if summary_data:
                if isinstance(summary_data, dict):
                    # Store both the full structured data and a plain text summary
                    self.conversations_collection.update_one(
                        {"_id": conversation_id},
                        {"$set": {
                            "summary": summary_data.get("summary", ""),
                            "summary_data": summary_data,
                            "key_points": summary_data.get("key_points", []),
                            "sentiment": summary_data.get("sentiment", "neutral")
                        }}
                    )
                else:
                    # Fallback for string response
                    self.conversations_collection.update_one(
                        {"_id": conversation_id},
                        {"$set": {"summary": summary_data}}
                    )
                print("[System: Conversation summary updated.]")

    def stop(self):
        """Stops the game loop."""
        self.is_running = False

    async def end_game(self):
        """
        Ends the current season, clearing all volatile data.
        """
        print("Archiving and clearing season data...")
        self.messages_collection.delete_many({})
        self.conversations_collection.delete_many({})
        self.character_engine.characters_collection.delete_many({})
        self.character_engine.relationships_collection.delete_many({})
        print("Season data cleared.")
        self.is_running = False
