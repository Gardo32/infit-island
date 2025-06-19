from pymongo import MongoClient
import os

class DatabaseHandler:
    """Database handler for MongoDB connections"""
    
    def __init__(self):
        """Initialize the database connection"""
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_database("voice_island")
        
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        return self.db[collection_name]
    
    def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()

# Create a singleton instance
db_handler = DatabaseHandler()
