from flask import Blueprint, jsonify
from db import get_conn
from jwt_utils import jwt_required

departments_bp = Blueprint("departments_api", __name__)

@departments_bp.route("/api/departments", methods=["GET"])
@jwt_required
def list_departments():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM departments")
            deps = cur.fetchall()
    finally:
        conn.close()
    return jsonify(deps)
