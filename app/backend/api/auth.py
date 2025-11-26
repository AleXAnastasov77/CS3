from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from db import get_conn
from jwt_utils import create_token
from config import Config
auth_bp = Blueprint("auth_api", __name__)

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token(user["id"], user["username"])
    print("LOGIN SECRET:", Config.JWT_SECRET)
    return jsonify({"access_token": token})
