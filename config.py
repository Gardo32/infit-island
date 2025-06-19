from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
    DB_NAME: str = os.getenv("DB_NAME", "voice_island")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
