"""MySQL connection and transaction helpers using mysql-connector-python."""
from contextlib import contextmanager

import mysql.connector
from flask import current_app, g


def get_connection():
    if "db_connection" not in g or not g.db_connection.is_connected():
        g.db_connection = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            connection_timeout=current_app.config["DB_CONNECT_TIMEOUT"],
            autocommit=False,
        )
    return g.db_connection


def close_connection(_error=None):
    connection = g.pop("db_connection", None)
    if connection is not None and connection.is_connected():
        connection.close()


@contextmanager
def cursor(dictionary=True):
    conn = get_connection()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield cur
    finally:
        cur.close()


@contextmanager
def transaction(dictionary=True):
    conn = get_connection()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def fetch_one(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def execute(sql, params=()):
    with transaction(dictionary=False) as cur:
        cur.execute(sql, params)
        return cur.lastrowid, cur.rowcount
