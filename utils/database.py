import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "iptv_bot_db" # You can change your database name here

class MongoDB: 
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        if self._client is None:
            try:
                self._client = AsyncIOMotorClient(MONGO_URI)
                self._db = self._client[DB_NAME]
                print("MongoDB connected successfully!")
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                self._client = None
                self._db = None

    def get_db(self):
        if self._db is None:
            self._connect() # Try to reconnect if not connected
        return self._db

    def close_connection(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("MongoDB connection closed.")

def get_database():
    return MongoDB().get_db()
