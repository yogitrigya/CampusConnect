"""Backward-compatible launcher for the original starter filename."""
import os

from app import app


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
