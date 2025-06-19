from engine.ai import LLMHandler
from engine.tts import CoquiHandler
from bson import ObjectId
from storage.database.db_handler import db_handler
import random
import json
from datetime import datetime
import asyncio

try:
    from slugify import slugify
except ImportError:
    slugify = None

class CharacterEngine:
    def __init__(self):
        """
        Initializes the character engine with DB connections and AI/TTS handlers.
        """
        self.llm_handler = LLMHandler()
        self.tts_handler = CoquiHandler()
        self.characters_collection = db_handler.get_collection("characters")
        self.conversations_collection = db_handler.get_collection("conversations")
        self.messages_collection = db_handler.get_collection("messages")
        self.world_state_collection = db_handler.get_collection("world_state")
        self.relationships_collection = db_handler.get_collection("relationships")
        self.attribute_pools_collection = db_handler.get_collection("attribute_pools")

    def create_characters(self, count: int):
        """
        Generates a batch of new unique characters.
        """
        new_characters = []
        for _ in range(count):
            # This will handle relationships with already existing characters,
            # including those created in the same batch.
            new_char = self.create_character()
            new_characters.append(new_char)
        return new_characters

    def create_character(self):
        """
        Generates a new unique character, saves it to the database,
        and initializes relationships with existing characters.
        """
        # 1. Fetch attribute pools from DB
        pool_docs = self.attribute_pools_collection.find({})
        pools = {doc["_id"]: doc["values"] for doc in pool_docs}

        # Default to empty lists if any pool is missing
        personality_pool = pools.get("personality_pool", [])
        background_pool = pools.get("background_pool", [])
        trait_pool = pools.get("trait_pool", [])
        voice_pool = pools.get("voice_pool", [])
        ethnicity_pool = pools.get("ethnicity_pool", [])
        religion_pool = pools.get("religion_pool", [])
        mental_illness_pool = pools.get("mental_illness_pool", [])
        subconscious_trait_pool = pools.get("subconscious_trait_pool", [])

        # 2. Generate a unique character
        character_doc = None
        while character_doc is None:
            personality = random.sample(personality_pool, k=random.randint(2, 3))
            background = random.choice(background_pool)
            traits = random.sample(trait_pool, k=random.randint(2, 4))
            ethnicity = random.choice(ethnicity_pool)
            religion = random.choice(religion_pool)
            mental_illness = random.sample(mental_illness_pool, k=random.randint(0, 2))
            subconscious_traits = random.sample(subconscious_trait_pool, k=random.randint(1, 2))
            voice_type = random.choice(voice_pool)

            name = f"{' '.join(personality)} {background}".title()
            char_id = slugify(name)

            if self.characters_collection.find_one({"_id": char_id}) is None:
                character_doc = {
                    "_id": char_id,
                    "name": name,
                    "personality": personality,
                    "background": background,
                    "traits": traits,
                    "voice_type": voice_type,
                    "ethnicity": ethnicity,
                    "religion": religion,
                    "mental_illness": mental_illness,
                    "subconscious_traits": subconscious_traits,
                    "mood": "neutral",
                    "relationships": {},
                    "technical_iq": random.randint(80, 140),
                    "general_iq": random.randint(80, 140)
                }

        # 3. Initialize relationships with existing characters
        existing_char_ids = [c["_id"] for c in self.characters_collection.find({}, {"_id": 1})]
        new_relationships = []
        for existing_id in existing_char_ids:
            # Update existing character's view of new one
            self.characters_collection.update_one(
                {"_id": existing_id},
                {"$set": {f"relationships.{character_doc['_id']}": 0.0}}
            )
            # Add reciprocal relationship
            character_doc["relationships"][existing_id] = 0.0
            new_relationships.append({
                "char1_id": character_doc['_id'],
                "char2_id": existing_id,
                "affinity_score": 0.0,
                "interaction_history": []
            })

        if new_relationships:
            self.relationships_collection.insert_many(new_relationships)

        # 4. Save new character to DB
        self.characters_collection.insert_one(character_doc)

        return character_doc

    async def interact(self, character_id: str, text: str, conversation_id: str = None):
        """
        Handles interaction with a character using JSON-based RAG.
        """
        # 1. Get character data from DB.
        character = self.characters_collection.find_one({"_id": character_id})
        if not character:
            return {"error": "Character not found."}

        # 2. Get or create conversation.
        if conversation_id:
            conversation = self.conversations_collection.find_one({"_id": ObjectId(conversation_id)})
            if not conversation:
                return {"error": "Conversation not found."}
        else:
            conversation_doc = {
                "timestamp": datetime.utcnow(),
                "participants": ["player", character_id],
                "messages": [],
                "context": {},
                "summary": ""
            }
            result = self.conversations_collection.insert_one(conversation_doc)
            conversation_id = str(result.inserted_id)
            conversation = conversation_doc
            conversation["_id"] = result.inserted_id
        
        # 3. Retrieve relevant context and construct prompt as JSON
        prompt = await self._build_prompt(character, text, conversation_id)
        
        # 4. Define JSON schema for response validation
        response_schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Character name"
                },
                "personality": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Character personality traits"
                },
                "mood": {
                    "type": "string",
                    "description": "Current mood of the character"
                },
                "dialogue": {
                    "type": "string",
                    "description": "Character's spoken dialogue in response to the player"
                },
                "emotion": {
                    "type": "string",
                    "description": "Current emotional state during this dialogue"
                },
                "action": {
                    "type": "string",
                    "description": "Any physical action the character takes"
                },
                "memory_note": {
                    "type": "string",
                    "description": "Internal thought or memory to record"
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Possible player interaction choices"
                },
                "relationships": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                    "description": "Character's relationships with other characters"
                },
                "traits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Character traits"
                },
                "subconscious_traits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Character's hidden subconscious traits"
                }
            },
            "required": ["name", "dialogue", "emotion"]
        }
        
        # 5. Get LLM response with JSON format and schema validation
        llm_response = await self.llm_handler.get_response(
            prompt, 
            model="gemma3:4b", 
            json_format=True,
            schema=response_schema
        )
        
        if not llm_response:
            return {"error": "Failed to get response from LLM."}

        # 6. Handle fallback for string responses
        if isinstance(llm_response, str):
            llm_response = {
                "name": character["name"],
                "personality": character["personality"],
                "mood": character["mood"],
                "dialogue": llm_response,
                "emotion": "neutral",
                "action": "",
                "memory_note": "LLM did not return valid JSON.",
                "choices": [],
                "relationships": character.get("relationships", {}),
                "traits": character.get("traits", []),
                "subconscious_traits": character.get("subconscious_traits", [])
            }

        # 7. Process LLM response
        dialogue = llm_response.get("dialogue", "I am speechless.")
        new_mood = llm_response.get("mood", character["mood"])
        emotion = llm_response.get("emotion", character["mood"])
        memory_note = llm_response.get("memory_note", "")
        choices = llm_response.get("choices", [])
        updated_relationships = llm_response.get("relationships", character.get("relationships", {}))
        updated_traits = llm_response.get("traits", character.get("traits", []))
        updated_subconscious = llm_response.get("subconscious_traits", character.get("subconscious_traits", []))

        # 8. Store messages in database (JSON format for context_tags)
        player_message_doc = {
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow(),
            "speaker_type": "player",
            "speaker_id": "player",
            "content": text,
            "emotion": "n/a",
            "context_tags": []
        }
        player_message_result = self.messages_collection.insert_one(player_message_doc)

        # Create context tags as JSON objects
        context_tags = []
        if llm_response.get("action"):
            context_tags.append({"type": "action", "value": llm_response.get("action")})
        if memory_note:
            context_tags.append({"type": "memory_note", "value": memory_note})
        
        character_message_doc = {
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow(),
            "speaker_type": "character",
            "speaker_id": character_id,
            "content": dialogue,
            "emotion": emotion,
            "context_tags": context_tags
        }
        character_message_result = self.messages_collection.insert_one(character_message_doc)

        # 9. Update conversation with new message IDs and update summary
        self.conversations_collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$push": {"messages": {"$each": [player_message_result.inserted_id, character_message_result.inserted_id]}}}
        )
        
        # 10. Asynchronously update the conversation summary in JSON format
        asyncio.create_task(self._update_conversation_summary(conversation_id))

        # 11. Update character with all returned data
        character_updates = {
            "mood": new_mood,
            "relationships": updated_relationships,
            "traits": updated_traits,
            "subconscious_traits": updated_subconscious
        }
        self.characters_collection.update_one({"_id": character_id}, {"$set": character_updates})

        # 12. Synthesize audio response
        audio_path = self.tts_handler.synthesize(dialogue, character.get("voice_type"))

        # 13. Return response as JSON
        return {
            "dialogue": dialogue,
            "audio_path": audio_path,
            "conversation_id": str(conversation_id),
            "character_state": {
                "mood": new_mood,
                "emotion": emotion,
                "relationships": updated_relationships,
                "traits": updated_traits,
                "subconscious_traits": updated_subconscious
            },
            "choices": choices,
            "action": llm_response.get("action", ""),
            "memory_note": memory_note
        }
        
    async def _update_conversation_summary(self, conversation_id: str):
        """
        Asynchronously updates the conversation summary using JSON format.
        """
        # 1. Get conversation messages
        messages = list(self.messages_collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1))
        
        if not messages:
            return
            
        # 2. Format messages for summarization
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "speaker_id": msg.get('speaker_id'),
                "content": msg.get('content'),
                "emotion": msg.get('emotion', 'neutral')
            })
        
        # 3. Generate JSON summary
        summary = await self.llm_handler.summarize_conversation(
            formatted_messages, 
            json_format=True
        )
        
        if not summary or not isinstance(summary, dict):
            return
            
        # 4. Update conversation with summary
        summary_text = summary.get("summary", "")
        self.conversations_collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {
                "summary": summary_text,
                "context.summary_data": summary
            }}
        )
        
    async def observe_character(self, character_id: str, observation_type: str = "general", context: str = ""):
        """
        Allows the director to observe a character from an external perspective using JSON-based RAG.
        """
        # 1. Get character data from DB
        character = self.characters_collection.find_one({"_id": character_id})
        if not character:
            return {"error": "Character not found."}

        # 2. Build observation prompt in JSON structure
        prompt = await self._build_observation_prompt(character, observation_type, context)
        
        # 3. Define JSON schema for response validation
        observation_schema = {
            "type": "object",
            "properties": {
                "observation": {
                    "type": "string",
                    "description": "Detailed observation of the character's current state and behavior"
                },
                "character_state": {
                    "type": "string",
                    "description": "A brief descriptor of the character's current emotional/mental state"
                },
                "director_insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Analysis and insights for the director about this character"
                },
                "suggested_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Potential actions the director could take regarding this character"
                }
            },
            "required": ["observation", "character_state", "director_insights"]
        }
        
        # 4. Get LLM response with JSON input/output
        llm_response = await self.llm_handler.get_response(
            prompt, 
            model="gemma3:4b", 
            json_format=True,
            schema=observation_schema
        )
        
        if not llm_response:
            return {"error": "Failed to generate observation."}
            
        # 5. Handle string responses (parsing failed in LLM handler)
        if isinstance(llm_response, str):
            llm_response = {
                "observation": llm_response,
                "character_state": "unknown",
                "director_insights": ["Character state unclear due to response format error."],
                "suggested_actions": []
            }

        # 6. Log the observation as JSON
        observation_doc = {
            "timestamp": datetime.utcnow(),
            "observer": "DIRECTOR",
            "character_id": character_id,
            "observation_type": observation_type,
            "context": context,
            "observation_data": {
                "observation": llm_response.get("observation", ""),
                "character_state": llm_response.get("character_state", "unknown"),
                "director_insights": llm_response.get("director_insights", []),
                "suggested_actions": llm_response.get("suggested_actions", [])
            }
        }
        self.messages_collection.insert_one(observation_doc)

        # 7. Return the observation data as JSON
        return {
            "observation": llm_response.get("observation", ""),
            "character_state": llm_response.get("character_state", "unknown"),
            "director_insights": llm_response.get("director_insights", []),
            "suggested_actions": llm_response.get("suggested_actions", []),
            "character_name": character["name"]
        }
        
    async def _build_observation_prompt(self, character: dict, observation_type: str, context: str) -> dict:
        """Builds JSON-structured prompts for director character observations."""
        
        # Get recent character activity
        recent_messages = list(self.messages_collection.find(
            {"speaker_id": character["_id"]}
        ).sort("timestamp", -1).limit(5))

        # Format messages for JSON
        formatted_messages = []
        for msg in recent_messages:
            formatted_messages.append({
                "speaker_id": msg.get('speaker_id'),
                "content": msg.get('content'),
                "emotion": msg.get('emotion', 'neutral'),
                "timestamp": str(msg.get('timestamp'))
            })

        # Get relationship context
        all_other_characters = self.characters_collection.find({"_id": {"$ne": character["_id"]}})
        other_char_list = list(all_other_characters)
        
        relationships_data = []
        for other_char in other_char_list:
            affinity = character.get("relationships", {}).get(other_char["_id"], 0.0)
            relationships_data.append({
                "id": other_char.get("_id"),
                "name": other_char.get("name"),
                "affinity": affinity
            })
        
        # Build the base prompt structure as JSON
        base_prompt = {
            "role": "director",
            "character": {
                "id": character.get("_id"),
                "name": character.get("name"),
                "personality": character.get("personality", []),
                "background": character.get("background", ""),
                "traits": character.get("traits", []),
                "mood": character.get("mood", "neutral"),
                "ethnicity": character.get("ethnicity", ""),
                "religion": character.get("religion", ""),
                "mental_illness": character.get("mental_illness", []),
                "subconscious_traits": character.get("subconscious_traits", []),
                "technical_iq": character.get("technical_iq", 100),
                "general_iq": character.get("general_iq", 100)
            },
            "context": {
                "setting": "Voice Island reality TV show",
                "observation_type": observation_type,
                "additional_context": context,
                "recent_activity": formatted_messages,
                "relationships": relationships_data
            },
            "instructions": {
                "task": f"Generate {observation_type} observation",
                "response_format": "JSON",
                "response_structure": {
                    "observation": "detailed_observation_text",
                    "character_state": "emotional_mental_state",
                    "director_insights": ["insight1", "insight2", "insight3"],
                    "suggested_actions": ["possible_action1", "possible_action2"]
                }
            }
        }
        
        # Add observation type specific instructions
        if observation_type == "general":
            base_prompt["instructions"]["description"] = "Observe the character's general behavior and state"
        elif observation_type == "private_thoughts":
            base_prompt["instructions"]["description"] = "Reveal the character's inner thoughts and feelings"
        elif observation_type == "interaction":
            base_prompt["instructions"]["description"] = "Analyze the character's behavior in a specific interaction"
        
        return base_prompt
        
    async def _build_prompt(self, character: dict, player_input: str, conversation_id: str) -> dict:
        """Builds the prompt for character responses as a JSON structure."""
        # Retrieve recent messages
        recent_messages_cursor = self.messages_collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", -1).limit(10)
        recent_messages = list(recent_messages_cursor)
        recent_messages.reverse()
        
        # Format messages for JSON
        formatted_messages = []
        for msg in recent_messages:
            formatted_messages.append({
                "speaker_id": msg.get('speaker_id'),
                "content": msg.get('content'),
                "emotion": msg.get('emotion', 'neutral'),
                "timestamp": str(msg.get('timestamp'))
            })
        
        # Get conversation summary
        conversation = self.conversations_collection.find_one({"_id": ObjectId(conversation_id)})
        conversation_summary = conversation.get("summary", "No summary yet.") if conversation else "No conversation found."

        # Determine prompt context
        context_prompt = "responding to player message"
        if player_input == "[Start Conversation]":
            context_prompt = "first confessional session"

        # Get all other characters for relationship context
        all_other_characters = self.characters_collection.find({"_id": {"$ne": character["_id"]}})
        other_char_list = list(all_other_characters)
        
        other_characters_data = []
        for other_char in other_char_list:
            affinity = character.get("relationships", {}).get(other_char["_id"], 0.0)
            other_characters_data.append({
                "id": other_char.get("_id"),
                "name": other_char.get("name", "Unknown"),
                "personality": other_char.get("personality", []),
                "background": other_char.get("background", "Unknown"),
                "affinity_score": affinity
            })

        # Build prompt as JSON structure
        prompt = {
            "role": "character",
            "character": {
                "id": character.get("_id"),
                "name": character.get("name"),
                "personality": character.get("personality", []),
                "background": character.get("background", ""),
                "traits": character.get("traits", []),
                "mood": character.get("mood", "neutral"),
                "relationships": character.get("relationships", {}),
                "ethnicity": character.get("ethnicity", ""),
                "religion": character.get("religion", ""),
                "mental_illness": character.get("mental_illness", []),
                "subconscious_traits": character.get("subconscious_traits", []),
                "technical_iq": character.get("technical_iq", 100),
                "general_iq": character.get("general_iq", 100)
            },
            "context": {
                "setting": "Voice Island reality TV show",
                "current_context": context_prompt,
                "player_input": player_input,
                "other_characters": other_characters_data,
                "conversation_history": formatted_messages,
                "conversation_summary": conversation_summary
            },
            "instructions": {
                "task": "Generate in-character response",
                "response_format": "JSON",
                "response_structure": {
                    "name": "character name",
                    "personality": ["personality_traits"],
                    "mood": "current_emotional_state",
                    "dialogue": "character's spoken response (under 80 words)",
                    "emotion": "specific_emotion_during_dialogue",
                    "action": "any_physical_action_taken",
                    "memory_note": "character's_internal_thoughts",
                    "choices": ["possible_player_response1", "possible_player_response2", "possible_player_response3"],
                    "relationships": {"character_id": "float_value"},
                    "traits": ["character_traits"],
                    "subconscious_traits": ["subconscious_traits"]
                }
            }
        }
        
        return prompt

    def _update_relationship(self, char1_id: str, char2_id: str, llm_response: dict):
        """Placeholder for relationship update logic."""
        # This could be based on emotion, memory_note, etc.
        # For now, we just print a message.
        print(f"Updating relationship between {char1_id} and {char2_id} based on interaction.")
        pass
