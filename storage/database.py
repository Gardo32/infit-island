"""
Main database module for the application.
This file defines the MongoDB database connection.
"""
from pymongo import MongoClient
from config import settings

class DatabaseClient:
    """Legacy Database client class - prefer using storage.database.db_handler instead"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance.client = MongoClient(settings.MONGO_URI)
            cls._instance.db = cls._instance.client[settings.DB_NAME]
        return cls._instance

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def ping(self):
        """Checks if the database connection is alive."""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

# For backwards compatibility
Database = DatabaseClient
db_handler = Database()
