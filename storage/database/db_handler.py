from pymongo import MongoClient
from config import settings

class DatabaseHandler:
    """Database handler for MongoDB connections"""
    
    def __init__(self):
        """Initialize the database connection"""
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client.get_database(settings.DB_NAME)
        
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        return self.db[collection_name]
    
    def ping(self):
        """Checks if the database connection is alive."""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()

# Create a singleton instance
db_handler = DatabaseHandler()
