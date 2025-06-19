from storage.database.db_handler import db_handler
from engine.logic.character_engine import CharacterEngine
import asyncio
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class GameLoop:
    def __init__(self):
        """
        Initializes the game loop for director control.
        """
        self.character_engine = CharacterEngine()
        self.messages_collection = db_handler.get_collection("messages")
        self.conversations_collection = db_handler.get_collection("conversations")
        self.is_running = False
        logger.info("Director control system initialized.")

    async def start(self):
        """
        Initializes the season for director control.
        """
        self.is_running = True
        logger.info("New season ready for director control.")
        # Cast must be created via the director interface before the story can start.

    async def start_story(self, model: str):
        """
        Generates the season premiere introduction under director control.
        """
        logger.info(f"Generating season premiere with model {model}...")
        characters = list(self.character_engine.characters_collection.find({}))
        if not characters:
            return {"error": "Cannot start the season premiere without any contestants.", "choices": []}

        character_descriptions = []
        for char in characters:
            description = f"- **{char['name']}** aka {char['personality'][0]}: {char['background']}"
            character_descriptions.append(description)
        
        character_list_str = "\n".join(character_descriptions)
        
        prompt = f"""You are the narrator of a reality TV show called 'Voice Island'.
Your persona is witty, dramatic, and cheeky.

Your task is to generate the season premiere. The output must be a JSON object.

**Show Title**: Voice Island
**Narrator Persona**: Witty, dramatic, cheeky

**Cast Summary**:
{character_list_str}

**Instructions**:
1.  **Generate a Dramatic Title**: Create a catchy title for the premiere, including emojis.
2.  **Describe the Villa**: Paint a picture of the luxurious setting.
3.  **Introduce Contestants**: Write a brief, engaging introduction for each person.
4.  **First Meeting**: Script the initial interactions and dialogue between contestants.
5.  **AI Announcement**: Include a message from the 'Voice Island AI'.
6.  **Director's Choices**: Provide an array of 3-4 narrative choices for the director to steer the story.

**Output Format**:
Your response must be a JSON object with no markdown formatting.
The JSON object must conform to the following schema:
{{
    "dialogue": "string (markdown format)",
    "choices": ["string"]
}}
"""
        
        logger.info(f"Prompt for season premiere:\n{prompt}")
        response_data = await self.character_engine.llm_handler.get_response(
            prompt, 
            model=model, 
            json_format=True
        )
        logger.info(f"Response from LLM: {json.dumps(response_data, indent=2) if response_data else None}")
        
        if isinstance(response_data, dict):
            dialogue = response_data.get("dialogue", "")
            choices = response_data.get("choices", [])
        else:
            dialogue = str(response_data) if response_data else "Error: The AI narrator provided an invalid response. Please try again."
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

    async def progress_story(self, director_choice: str, model: str):
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
...{summary}
"""
        
        prompt = f"""You are the writer for a reality TV show called 'Voice Island'.
Your persona is witty, dramatic, and cheeky.

Your task is to progress the story based on the director's choice. The output must be a JSON object.

**Show Title**: Voice Island
**Writer Persona**: Witty, dramatic, cheeky

**Cast Summary**:
{character_list_str}

**Story Context**:
{story_context}

**Director's Choice**: {director_choice}

**Instructions**:
1.  **Write a New Scene**: The scene must be a direct result of the director's choice.
2.  **Format as Chat**: The scene should be a series of short chat messages from the Narrator and characters.
3.  **Character Dialogue**: Include dialogue from at least 2-3 characters.
4.  **Specify Speaker/Emotion**: For each message, specify the speaker, their line, and optionally, their emotion.
5.  **Game Over**: If the story has reached a conclusion, set `is_game_over` to `true`.
6.  **Director's Choices**: Provide an array of 3-4 new narrative choices for the director.

**Output Format**:
Your response must be a JSON object with no markdown formatting.
The JSON object must conform to the following schema:
{{
    "scene": [{{ "speaker": "string", "line": "string", "emotion": "string (optional)" }}],
    "choices": ["string"],
    "is_game_over": "boolean"
}}
"""

        logger.info(f"Prompt for story progression:\n{prompt}")
        response_data = await self.character_engine.llm_handler.get_response(
            prompt, 
            model=model, 
            json_format=True
        )
        logger.info(f"Response from LLM: {json.dumps(response_data, indent=2)}")
        
        if isinstance(response_data, dict):
            scene = response_data.get("scene", [])
            choices = response_data.get("choices", [])
            is_game_over = response_data.get("is_game_over", False)
            
            dialogue = ""
            for message in scene:
                speaker = message.get('speaker', 'Unknown')
                line = message.get('line', '')
                emotion = message.get('emotion')
                if emotion:
                    dialogue += f"**{speaker}** (*{emotion}*): {line}\n"
                else:
                    dialogue += f"**{speaker}**: {line}\n"
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
            logger.info(f"Conversation {conversation_id} has {message_count} messages. Triggering summarization.")
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
                logger.info("Conversation summary updated.")

    def stop(self):
        """Stops the game loop."""
        self.is_running = False

    async def end_game(self):
        """
        Ends the current season, clearing all volatile data.
        """
        logger.info("Archiving and clearing season data...")
        self.messages_collection.delete_many({})
        self.conversations_collection.delete_many({})
        self.character_engine.characters_collection.delete_many({})
        self.character_engine.relationships_collection.delete_many({})
        logger.info("Season data cleared.")
        self.is_running = False
