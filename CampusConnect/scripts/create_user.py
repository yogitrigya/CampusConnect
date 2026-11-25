"""Create privileged accounts without exposing a public role-selection form."""
import getpass
import sys
from pathlib import Path

import bcrypt
import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Config


def main():
    role = input("Role (admin/faculty/placement_officer): ").strip().lower()
    if role not in {"admin", "faculty", "placement_officer"}:
        raise SystemExit("Unsupported privileged role.")
    email = input("Email: ").strip().lower()
    password = getpass.getpass("Password (10-72 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm or not 10 <= len(password.encode("utf-8")) <= 72:
        raise SystemExit("Passwords must match and be between 10 and 72 bytes.")
    department_id = None
    designation = None
    if role == "faculty":
        department_id = input("Department ID: ").strip()
        designation = input("Designation: ").strip()
        if not department_id.isdigit() or not designation:
            raise SystemExit("Faculty accounts need a valid department ID and designation.")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    conn = mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME, connection_timeout=Config.DB_CONNECT_TIMEOUT)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users(email,password_hash,role) VALUES(%s,%s,%s)", (email,password_hash,role))
        user_id = cur.lastrowid
        if role == "faculty":
            cur.execute("INSERT INTO faculty(user_id,department_id,designation) VALUES(%s,%s,%s)", (user_id,int(department_id),designation))
        conn.commit()
        print(f"Created {role} account for {email}.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
