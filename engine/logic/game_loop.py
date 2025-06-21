import logging
from datetime import datetime
from bson.objectid import ObjectId

from storage.database.db_handler import db_handler
from engine.logic.character_engine import CharacterEngine

logger = logging.getLogger(__name__)

class GameLoop:
    def __init__(self):
        self.character_engine = CharacterEngine()
        self.messages_collection = db_handler.get_collection("messages")
        self.conversations_collection = db_handler.get_collection("conversations")
        self.is_running = False
        logger.info("🎮 Game loop initialized under director control.")

    async def start(self):
        self.is_running = True
        logger.info("🎬 New season launched. Awaiting cast setup via director interface.")

    async def start_story(self, model: str):
        logger.info(f"🚀 Generating season premiere with model `{model}`...")

        characters = list(self.character_engine.characters_collection.find({}))
        if not characters:
            logger.warning("No characters in the database. Cannot start story.")
            return {"dialogue": "Cannot start a story without any contestants.", "choices": [], "is_game_over": False}

        character_descriptions = [
            f"- **{char['name']}** aka {char['personality'][0]}: {char['background']}"
            for char in characters
        ]
        character_list_str = "\n".join(character_descriptions)

        prompt = f"""
You are a **structured narrator agent** for an AI-powered reality show simulation called **🎙️ Voice Island**.

---

## 🧠 Role Instructions:
- You are ONLY allowed to speak as **Narrator**, **Voice Island AI**, or **contestants** (using their exact names).
- Each line must be attributed using one of these speaker types:
  - 🧠 **Narrator** – Use `Narrator` for scenic descriptions and commentary.
  - 🗣️ **Character Name** – Only use names listed in the cast. Dialogue must reflect their personality.
  - 🤖 **Voice Island AI** – Occasional cryptic announcements or twists.

Do NOT generate any narration or dialogue from characters not in the cast.

---

## 👥 Cast (Contestants):
{character_list_str}

---

## 🎬 Season Premiere Requirements:

1. **Episode Title**: A dramatic title with emojis.
2. **Villa Description**: Paint a vivid picture of the futuristic villa setting.
3. **Cast Introductions**: Brief, exciting intros for each contestant.
4. **First Interactions**: Let the contestants meet and talk.
5. **AI Announcement**: Add a mysterious or unexpected twist from the Voice Island AI.
6. **Director’s Choices**: Provide 3–4 interesting next steps the director may choose.

---

## 🔐 Output Format (STRICT)

Return only a **valid JSON object** with this exact structure, Choice section is mandatory:

{{
  "title": "string (episode title with emojis)",
  "dialogue": [
    {{
      "speaker": "Narrator | Character Name | Voice Island AI",
      "line": "string (markdown-formatted narration or dialogue)"
    }},
    ...
  ],
  "choices": [
    "string (director choice)",
    "string (director choice)",
    "string (director choice)"
  ]
}}

---

## ✅ Formatting Rules:

- Use **markdown** in `line` values: bold, italics, emojis, etc.
- Each entry must clearly specify `speaker` and `line`.
- Do NOT include any code block formatting (e.g. no triple backticks or indentation).
- No other output or commentary is allowed.
- Do NOT invent extra data, characters, or formats.

---

Now generate the **season premiere episode**.
"""

        response_data = await self.character_engine.llm_handler.get_response(
            prompt, model=model, json_format=True
        )

        if isinstance(response_data, dict):
            title = response_data.get("title", "The Premiere")
            dialogue_list = response_data.get("dialogue", [])
            choices = response_data.get("choices", [])

            conversation_id = str(ObjectId())
            self.conversations_collection.insert_one({
                "_id": conversation_id,
                "timestamp": datetime.utcnow(),
                "participants": [char["_id"] for char in characters] + ["NARRATOR", "Voice Island AI"],
                "context": {"title": title}
            })

            for item in dialogue_list:
                self.messages_collection.insert_one({
                    "conversation_id": conversation_id,
                    "timestamp": datetime.utcnow(),
                    "speaker_type": "character" if item['speaker'] not in ["Narrator", "Voice Island AI"] else "system",
                    "speaker_id": item['speaker'],
                    "content": item['line'],
                    "emotion": "dramatic",
                })

            log_dialogue = f"# {title}\n" + "\n".join([
                f"**{item['speaker']}**: {item['line']}"
                for item in dialogue_list
            ])

            self.messages_collection.insert_one({
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow(),
                "speaker_type": "system",
                "speaker_id": "NARRATOR",
                "content": log_dialogue,
                "choices": choices,
                "emotion": "dramatic",
                "director_control": True,
                "is_game_over": False
            })

            return {"title": title, "dialogue": dialogue_list, "choices": choices, "is_game_over": False}

        fallback = str(response_data) if response_data else "Invalid LLM response."
        self.messages_collection.insert_one({
            "conversation_id": "SYSTEM_SEASON_START_ERROR",
            "timestamp": datetime.utcnow(),
            "speaker_type": "system",
            "speaker_id": "NARRATOR",
            "content": fallback,
            "choices": [],
            "emotion": "dramatic",
            "director_control": True,
            "is_game_over": False
        })
        return {"dialogue": fallback, "choices": [], "is_game_over": False}

    async def progress_story(self, director_choice: str, model: str):
        characters = list(self.character_engine.characters_collection.find({}))
        if not characters:
            return {"dialogue": "Cannot progress the story without any contestants.", "choices": []}

        character_descriptions = [f"- **{char['name']}** ({', '.join(char['personality'])}, {char['background']})" for char in characters]
        character_list_str = "\n".join(character_descriptions)

        last_block = self.messages_collection.find_one(
            {"speaker_type": "system", "director_control": True},
            sort=[("timestamp", -1)]
        )
        story_context = last_block['content'][-700:] if last_block and 'content' in last_block else ""
        conversation_id = last_block.get('conversation_id') if last_block else None

        prompt = f"""
You are a **story progression agent** for the AI reality show **🎙️ Voice Island**.

---

## 🧠 Role Instructions:
- You may ONLY speak as **Narrator**, **Voice Island AI**, or **contestants** (must match the cast names).
- Use their personality traits.
- Reactions must directly follow the selected **Director’s Choice**.

---

## 👥 Cast:
{character_list_str}

---

## 🎞️ Context:
{story_context}

---

## 🎮 Director’s Selected Choice:
{director_choice}

---

## 📝 Task:
Generate the next scene in JSON. Include:
1. 3–5 lines of dramatic interaction (Narrator, 2–3 contestants, optional AI line).
2. 3–4 new choices.
3. End condition flag.

---

## 🔐 JSON Output Format (STRICT):

{{
  "scene": [
    {{ "speaker": "Narrator | Character Name | Voice Island AI", "line": "string", "emotion": "optional" }},
    ...
  ],
  "choices": [
    "string (director choice)",
    "string (director choice)",
    "string (director choice)"
  ],
  "is_game_over": boolean
}}

---

## ✅ Rules:
- Do not add extra metadata.
- No code blocks or markdown formatting.
- No outside commentary.

Now continue the story from the Director’s choice.
"""

        response_data = await self.character_engine.llm_handler.get_response(
            prompt, model=model, json_format=True
        )

        if isinstance(response_data, dict):
            scene = response_data.get("scene", [])
            choices = response_data.get("choices", [])
            is_game_over = response_data.get("is_game_over", False)

            if not conversation_id:
                conversation_id = str(ObjectId())
                self.conversations_collection.insert_one({
                    "_id": conversation_id,
                    "timestamp": datetime.utcnow(),
                    "participants": [char["_id"] for char in characters] + ["NARRATOR", "Voice Island AI"],
                    "context": {"title": "Story Progression"}
                })

            for item in scene:
                self.messages_collection.insert_one({
                    "conversation_id": conversation_id,
                    "timestamp": datetime.utcnow(),
                    "speaker_type": "character" if item['speaker'] not in ["Narrator", "Voice Island AI"] else "system",
                    "speaker_id": item['speaker'],
                    "content": item['line'],
                    "emotion": item.get("emotion", "neutral"),
                })
            
            dialogue_to_return = scene
        else:
            scene = []
            choices = []
            is_game_over = False
            dialogue_to_return = [{"speaker": "System", "line": "Invalid LLM response."}]


        if is_game_over:
            self.stop()

        log_content = "\n".join([
            f"**{m['speaker']}** ({m.get('emotion', 'neutral')}): {m['line']}"
            for m in scene
        ]) if scene else "No scene generated from LLM."

        self.messages_collection.insert_one({
            "conversation_id": conversation_id or "SYSTEM_STORY_PROGRESS_ERROR",
            "timestamp": datetime.utcnow(),
            "speaker_type": "system",
            "speaker_id": "NARRATOR",
            "content": log_content,
            "choices": choices,
            "emotion": "dramatic",
            "director_control": True,
            "triggering_choice": director_choice,
            "is_game_over": is_game_over
        })

        return {"dialogue": dialogue_to_return, "choices": choices, "is_game_over": is_game_over}

    def get_story_history(self):
        """
        Retrieves the full story history from the messages collection for the current season.
        """
        latest_conv = self.conversations_collection.find_one(sort=[("timestamp", -1)])
        if not latest_conv:
            return {"dialogue": [], "choices": []}
        
        conv_id = latest_conv["_id"]
        
        messages = self.messages_collection.find(
            {
                "conversation_id": conv_id,
                "director_control": {"$ne": True}
            },
            sort=[("timestamp", 1)]
        )
        
        dialogue = []
        for msg in messages:
            dialogue.append({
                "speaker": msg.get("speaker_id"),
                "line": msg.get("content"),
                "emotion": msg.get("emotion")
            })
            
        last_director_message = self.messages_collection.find_one(
            {
                "conversation_id": conv_id,
                "director_control": True
            },
            sort=[("timestamp", -1)]
        )
        
        choices = []
        if last_director_message:
            choices = last_director_message.get("choices", [])
            
        return {"dialogue": dialogue, "choices": choices}

    async def end_game(self):
        """Ends the current game season."""
        self.is_running = False
        logger.info("Game loop stopped.")

    def stop(self):
        self.is_running = False
        logger.info("🛑 Story has concluded.")
