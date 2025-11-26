import datetime
from jose import jwt
from functools import wraps
from flask import request, jsonify
from config import Config

def create_token(user_id, username):
    now = datetime.datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=Config.JWT_EXPIRES_MINUTES)
    }
    return jwt.encode(
        payload,
        Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

def decode_token(token):
    return jwt.decode(
        token,
        Config.JWT_SECRET,
        algorithms=[Config.JWT_ALGORITHM]
    )

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "").strip()

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = parts[1]

        try:
            payload = decode_token(token)
            request.user = payload
        except Exception as e:
            print("JWT ERROR:", e)
            return jsonify({"error": "Invalid or expired token"}), 401

        return fn(*args, **kwargs)
    return wrapper

