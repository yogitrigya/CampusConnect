from functools import wraps

from flask import jsonify, redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify(error={"code": "unauthenticated", "message": "Sign in is required."}), 401
            return redirect(url_for("auth.login_page", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                return jsonify(error={"code": "forbidden", "message": "You do not have permission for this action."}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
