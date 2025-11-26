from flask import Blueprint, jsonify, request
from db import get_conn
from jwt_utils import jwt_required
from automation import provision_employee, deprovision_employee
import pymysql
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

    required = ["first_name", "last_name", "email", "department_id"]
    if not all(k in data and data[k] for k in required):
        return jsonify({"error": "Missing employee fields"}), 400

    first_name = data["first_name"].strip()
    last_name = data["last_name"].strip()
    email = data["email"].strip().lower()
    department_id = data["department_id"]

    # auto-generate AD username
    ad_username = f"{first_name.lower()}.{last_name.lower()}"

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO employees (first_name, last_name, email, department_id, ad_username, status)
                    VALUES (%s, %s, %s, %s, %s, 'active')
                    """,
                    (first_name, last_name, email, department_id, ad_username)
                )
                conn.commit()

            except pymysql.err.IntegrityError as e:
                # Duplicate key → 1062
                if e.args[0] == 1062:
                    err_msg = str(e).lower()

                    if "email" in err_msg:
                        return jsonify({
                            "error": "Employee with this email already exists"
                        }), 409

                    if "ad_username" in err_msg:
                        return jsonify({
                            "error": "Employee with this AD username already exists",
                            "ad_username": ad_username
                        }), 409

                    # Fallback if it's another field
                    return jsonify({"error": "Duplicate entry", "details": str(e)}), 409

                # Unknown integrity error
                return jsonify({"error": "Database integrity error", "details": str(e)}), 400

            # 1) Get inserted ID
            cur.execute("SELECT LAST_INSERT_ID() AS id")
            new_id = cur.fetchone()["id"]

            # 2) Fetch the employee before provisioning
            cur.execute("SELECT * FROM employees WHERE id=%s", (new_id,))
            emp = cur.fetchone()

            # 3) Provision VM / AD — this part remains unchanged
            vm_name = provision_employee(emp)

            # 4) Save VM name
            cur.execute("UPDATE employees SET vm_name=%s WHERE id=%s", (vm_name, new_id))
            conn.commit()

            # 5) Return full employee with department name
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
            cur.execute("SELECT * FROM employees WHERE id=%s", (emp_id,))
            emp = cur.fetchone()
            if not emp:
                return jsonify({"error": "Employee not found"}), 404

            deprovision_employee(emp)

            cur.execute(
                "UPDATE employees SET status='deactivated', deactivated_at=NOW() WHERE id=%s",
                (emp_id,)
            )
            conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Employee deactivated"})
