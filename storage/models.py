from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from bson.objectid import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        core_schema.update(type="string")
        return core_schema

class Character(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    personality: List[str]
    background: str
    traits: List[str]
    voice_type: str
    mood: str
    relationships: Dict[str, float] = Field(default_factory=dict) # char_id -> affinity_score
    ethnicity: str
    religion: str
    mental_illness: List[str]
    subconscious_traits: List[str]
    technical_iq: int
    general_iq: int

class Message(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker_type: str # 'player' or 'character'
    speaker_id: str
    content: str
    emotion: str
    context_tags: List[str] = Field(default_factory=list)

class Conversation(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    participants: List[str] # list of character_ids (and maybe player_id)
    messages: List[PyObjectId] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""

class MessageHistory(BaseModel):
    id: str = Field(..., alias="_id") # conversation_id
    summarized_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    importance_scores: Dict[str, float] = Field(default_factory=dict) # message_id -> score

class WorldState(BaseModel):
    id: str = Field(..., alias="_id") # e.g., "singleton_world_state"
    current_scene: str
    active_events: List[str] = Field(default_factory=list)
    environmental_factors: Dict[str, Any] = Field(default_factory=dict)

class Relationship(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    char1_id: str
    char2_id: str
    affinity_score: float = 0.0
    interaction_history: List[str] = Field(default_factory=list) # list of conversation_ids

class AttributePool(BaseModel):
    id: str = Field(..., alias="_id") # e.g., "personality_pool"
    values: List[str]

class Choice(BaseModel):
    id: str
    text: str
    next_scene: str
    conditions: Dict[str, Any] = Field(default_factory=dict)

class Scene(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    characters: List[str] = Field(default_factory=list)  # character IDs
    location: str
    event_id: str = ""
    description: str = ""
    choices: List[Choice] = Field(default_factory=list)
    triggers: Dict[str, Any] = Field(default_factory=dict)
