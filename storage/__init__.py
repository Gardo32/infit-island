# This file makes the storage directory a package

# Import from the specific database.py file
import importlib.util
import sys
import os

# Get the absolute path to the database.py file
db_file_path = os.path.join(os.path.dirname(__file__), 'database.py')
spec = importlib.util.spec_from_file_location('database_module', db_file_path)
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)

# Now import from the module
Database = database_module.Database
db_handler = database_module.db_handler

# Import models
from .models import Character, Conversation, Message
