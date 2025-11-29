from flask import Blueprint, jsonify, request
from db import get_conn
from jwt_utils import jwt_required
from automation import provision_employee, deprovision_employee
import pymysql
from werkzeug.security import generate_password_hash

employees_bp = Blueprint("employees_api", __name__)

@employees_bp.route("/api/employees", methods=["GET"])
@jwt_required
def list_employees():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT e.*, d.name AS department_name "
                "FROM employees e JOIN departments d ON e.department_id = d.id"
            )
            employees = cur.fetchall()
    finally:
        conn.close()
    return jsonify(employees)

@employees_bp.route("/api/employees", methods=["POST"])
@jwt_required
def create_employee():
    data = request.get_json() or {}

    required = ["first_name", "last_name", "email", "department_id", "password"]
    if not all(k in data and data[k] for k in required):
        return jsonify({"error": "Missing employee fields"}), 400

    first_name = data["first_name"].strip()
    last_name = data["last_name"].strip()
    email = data["email"].strip().lower()
    department_id = data["department_id"]
    raw_password = data["password"].strip()

    hashed_password = generate_password_hash(raw_password)
    ad_username = f"{first_name.lower()}.{last_name.lower()}"

    # --------------------------------------------------
    # STEP 1 — Insert employee with full error handling
    # --------------------------------------------------
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO employees 
                    (first_name, last_name, email, department_id, ad_username, ad_password, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'active')
                    """,
                    (first_name, last_name, email, department_id, ad_username, hashed_password)
                )
                conn.commit()

            except pymysql.err.IntegrityError as e:
                if e.args[0] == 1062:  
                    msg = str(e).lower()

                    if "email" in msg:
                        return jsonify({"error": "Employee with this email already exists"}), 409

                    if "ad_username" in msg:
                        return jsonify({
                            "error": "Employee with this AD username already exists",
                            "ad_username": ad_username
                        }), 409

                    return jsonify({"error": "Duplicate entry", "details": str(e)}), 409

                return jsonify({"error": "Database integrity error", "details": str(e)}), 400

            # Get new employee ID
            cur.execute("SELECT LAST_INSERT_ID() AS id")
            new_id = cur.fetchone()["id"]

            # Fetch inserted data for provisioning
            cur.execute("SELECT * FROM employees WHERE id=%s", (new_id,))
            emp = cur.fetchone()

    finally:
        conn.close()

    # --------------------------------------------------
    # STEP 2 — Provision AD + VM
    # --------------------------------------------------
    vm_name = provision_employee(emp, raw_password)

    # --------------------------------------------------
    # STEP 3 — Save VM name + (NEW) Create HR Portal User
    # --------------------------------------------------
    conn = get_conn()
    try:
        with conn.cursor() as cur:

            # Save VM name
            cur.execute("UPDATE employees SET vm_name=%s WHERE id=%s", (vm_name, new_id))
            conn.commit()

            # -------------------------
            # NEW: IF DEPARTMENT IS HR
            # -------------------------
            cur.execute("SELECT name FROM departments WHERE id=%s", (department_id,))
            dep_name = cur.fetchone()["name"].strip().lower()

            if dep_name == "hr":
                # Username becomes AD username
                portal_username = ad_username

                try:
                    cur.execute(
                        """
                        INSERT INTO users (username, password_hash)
                        VALUES (%s, %s)
                        """,
                        (portal_username, hashed_password)
                    )
                    conn.commit()

                except pymysql.err.IntegrityError:
                    # If user already exists (rare), we ignore it
                    pass

            # Return full employee with department name
            cur.execute(
                """
                SELECT e.*, d.name AS department_name
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                WHERE e.id=%s
                """,
                (new_id,)
            )
            full_emp = cur.fetchone()

    finally:
        conn.close()

    return jsonify(full_emp), 201

@employees_bp.route("/api/employees/<int:emp_id>/deactivate", methods=["POST"])
@jwt_required
def deactivate_employee(emp_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:

            # 1) Fetch employee
            cur.execute("SELECT * FROM employees WHERE id=%s", (emp_id,))
            emp = cur.fetchone()

            if not emp:
                return jsonify({"error": "Employee not found"}), 404

            # 2) Fetch department name
            cur.execute("SELECT name FROM departments WHERE id=%s", (emp["department_id"],))
            dep = cur.fetchone()
            dep_name = dep["name"].strip().lower()

            # 3) Run VM + AD deprovisioning
            deprovision_employee(emp)

            # 4) Mark employee as deactivated
            cur.execute(
                "UPDATE employees SET status='deactivated', deactivated_at=NOW() WHERE id=%s",
                (emp_id,)
            )
            conn.commit()

            # 5) If employee is HR → delete HR portal user
            if dep_name == "hr":
                portal_username = emp["ad_username"]

                cur.execute("DELETE FROM users WHERE username=%s", (portal_username,))
                conn.commit()
                # If no user existed, DELETE just affects 0 rows → safe

    finally:
        conn.close()

    return jsonify({"message": "Employee deactivated"})

@employees_bp.route("/provision/status/<username>")
def get_status(username):
    from automation import PROVISION_STATUS
    return {"status": PROVISION_STATUS.get(username, "unknown")}