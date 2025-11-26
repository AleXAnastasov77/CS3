import os

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-frontend-secret")
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001")
