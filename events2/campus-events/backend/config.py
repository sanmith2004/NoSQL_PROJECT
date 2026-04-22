import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME   = os.getenv("DB_NAME", "my_events")

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB   = int(os.getenv("REDIS_DB", 0))

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-events-secret-2024")
    DEBUG      = os.getenv("DEBUG", "True").lower() == "true"
