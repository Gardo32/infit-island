import importlib.util
import os
# This file makes the storage directory a package

# Dynamically import db_handler from the database directory to avoid circular imports
db_file_path = os.path.join(os.path.dirname(__file__), "database", "db_handler.py")
spec = importlib.util.spec_from_file_location('database_module', db_file_path)
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)
db_handler = database_module.db_handler

# Import models
from .models import Character, Conversation, Message
