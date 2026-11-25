import re
import secrets

import bcrypt
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from mysql.connector import IntegrityError, Error as MySQLError

from app.auth.permissions import login_required
from app.database.connection import fetch_one, transaction

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _payload():
    return request.get_json(silent=True) if request.is_json else request.form


def _error(message, status=400):
    if request.path.startswith("/api/"):
        return jsonify(error={"code": "invalid_request", "message": message}), status
    flash(message, "danger")
    return redirect(url_for("auth.register_page" if "register" in request.path else "auth.login_page"))


@auth_bp.get("/login")
def login_page():
    return render_template("auth.html", mode="login")


@auth_bp.get("/register")
def register_page():
    database_available = True
    try:
        from app.database.connection import fetch_all
        departments = fetch_all("SELECT department_id, department_name FROM departments ORDER BY department_name")
    except MySQLError:
        departments = []
        database_available = False
    return render_template("auth.html", mode="register", departments=departments, database_available=database_available)


@auth_bp.post("/api/auth/register")
@auth_bp.post("/register")
def register():
    data = _payload() or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    name = str(data.get("name", "")).strip()
    roll_no = str(data.get("roll_no", "")).strip()
    department_id = data.get("department_id")
    if not EMAIL_RE.match(email) or len(email) > 100:
        return _error("Enter a valid email address.")
    if len(password) < 10 or len(password) > 72:
        return _error("Password must be 10 to 72 bytes long.")
    if not name or len(name) > 100 or not roll_no or len(roll_no) > 30:
        return _error("Name and roll number are required.")
    try:
        department_id = int(department_id)
    except (TypeError, ValueError):
        return _error("Choose a valid department.")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    try:
        with transaction(dictionary=False) as cur:
            cur.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'student')", (email, hashed))
            user_id = cur.lastrowid
            cur.execute("INSERT INTO students (user_id, roll_no, name, department_id) VALUES (%s, %s, %s, %s)", (user_id, roll_no, name, department_id))
        if request.path.startswith("/api/"):
            return jsonify(data={"message": "Account created. Sign in to continue."}), 201
        flash("Account created. Sign in to continue.", "success")
        return redirect(url_for("auth.login_page"))
    except IntegrityError:
        return _error("That email, roll number, or department is already in use.", 409)
    except MySQLError:
        return _error("Registration could not be completed. Check the database setup and try again.", 503)


@auth_bp.post("/api/auth/login")
@auth_bp.post("/login")
def login():
    data = _payload() or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        return _error("Email and password are required.")
    try:
        user = fetch_one("SELECT u.user_id, u.email, u.password_hash, u.role, COALESCE(s.name, f.designation, 'CampusConnect user') AS display_name FROM users u LEFT JOIN students s ON s.user_id=u.user_id LEFT JOIN faculty f ON f.user_id=u.user_id WHERE u.email=%s", (email,))
    except MySQLError:
        return _error("Sign in is temporarily unavailable. Check the database connection.", 503)
    try:
        valid_password = bool(user) and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8"))
    except (ValueError, TypeError):
        # Old demonstration hashes are deliberately not valid credentials.
        valid_password = False
    if not valid_password:
        return _error("Email or password is incorrect.", 401)
    session.clear()
    session.update(user_id=user["user_id"], role=user["role"], name=user["display_name"], email=user["email"], csrf_token=secrets.token_urlsafe(32))
    session.permanent = True
    if request.path.startswith("/api/"):
        return jsonify(data={"user_id": user["user_id"], "role": user["role"], "name": user["display_name"], "csrf_token": session["csrf_token"]}), 200
    flash("Welcome back.", "success")
    return redirect(url_for("main.dashboard"))


@auth_bp.post("/api/auth/logout")
@login_required
def logout():
    session.clear()
    if request.path.startswith("/api/"):
        return jsonify(data={"message": "Signed out."}), 200
    return redirect(url_for("main.index"))


@auth_bp.post("/logout")
@login_required
def logout_page():
    session.clear()
    return redirect(url_for("main.index"))
