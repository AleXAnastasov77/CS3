import os

class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

    # DB
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "hr_app")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRES_MINUTES = int("60")
