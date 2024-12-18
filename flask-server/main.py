import os
import pymongo
from app import server

SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
server.config['SECRET_KEY'] = SECRET_KEY

SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'DigiMeet')
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
db = client[MONGO_DATABASE]
users_collection = db["users"]
events_collection = db["events"]

def test_mongo_connection():
    try:
        # Test the connection by trying to fetch a server status
        client.admin.command('ping')
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

if __name__ == "__main__":
    test_mongo_connection()
    server.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)