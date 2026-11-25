from flask import Blueprint, redirect, render_template, session, url_for

from app.auth.permissions import login_required

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", role=session.get("role"), name=session.get("name", "CampusConnect user"))
