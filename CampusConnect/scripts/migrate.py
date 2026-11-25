"""Apply additive project migrations after checking the pre-existing core schema."""
import argparse
import os
from pathlib import Path
import sys

import mysql.connector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import Config

BASE = ROOT
MIGRATIONS = BASE / "database" / "migrations"
REQUIRED_CORE = {"users", "departments", "students", "faculty", "semesters", "courses", "enrollments"}
REQUIRED_COLUMNS = {
    "users": {"user_id", "email", "password_hash", "role"},
    "departments": {"department_id", "department_name"},
    "students": {"student_id", "user_id", "roll_no", "name", "department_id", "admission_year"},
    "faculty": {"faculty_id", "user_id", "department_id", "designation"},
    "semesters": {"semester_id", "semester_number", "academic_year"},
    "courses": {"course_id", "course_code", "course_name", "credits", "department_id"},
    "enrollments": {"enrollment_id", "student_id", "course_id", "semester_id"},
}


def connect():
    return mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT,
        user=os.getenv("MIGRATION_DB_USER", Config.DB_USER),
        password=os.getenv("MIGRATION_DB_PASSWORD", Config.DB_PASSWORD), database=Config.DB_NAME,
        connection_timeout=Config.DB_CONNECT_TIMEOUT, autocommit=False)


def run(apply=False):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s", (Config.DB_NAME,))
        current = {row[0] for row in cur.fetchall()}
        missing = REQUIRED_CORE - current
        if missing:
            raise RuntimeError("Core schema check failed; missing tables: " + ", ".join(sorted(missing)) + ". No migration was applied.")
        cur.execute("SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s", (Config.DB_NAME,))
        columns = {}
        for table, column in cur.fetchall(): columns.setdefault(table,set()).add(column)
        missing_columns = [f"{table}.{column}" for table, required in REQUIRED_COLUMNS.items() for column in sorted(required-columns.get(table,set()))]
        if missing_columns:
            raise RuntimeError("Core schema check failed; missing columns: " + ", ".join(missing_columns) + ". No migration was applied.")
        cur.execute("SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'", (Config.DB_NAME,))
        engines = dict(cur.fetchall())
        non_transactional = [name for name in REQUIRED_CORE if engines.get(name, "").upper() != "INNODB"]
        if non_transactional:
            raise RuntimeError("Core schema check failed; InnoDB is required for: " + ", ".join(sorted(non_transactional)) + ". No migration was applied.")
        migrations = sorted(MIGRATIONS.glob("*.sql"))
        if not apply:
            pending = migrations
            if "schema_migrations" in current:
                cur.execute("SELECT version FROM schema_migrations")
                applied = {row[0] for row in cur.fetchall()}
                pending = [path for path in migrations if path.name not in applied]
            print("Connected database:", Config.DB_NAME)
            print("Core schema is present. Pending migration files:", ", ".join(p.name for p in pending) or "none")
            print("Dry run only. Use --apply to apply additive migrations.")
            return
        cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(190) PRIMARY KEY, applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
        for migration in migrations:
            cur.execute("SELECT version FROM schema_migrations WHERE version=%s", (migration.name,))
            if cur.fetchone():
                print("Already applied:", migration.name)
                continue
            sql = migration.read_text(encoding="utf-8")
            statements = [part.strip() for part in sql.split(";") if part.strip()]
            try:
                for statement in statements:
                    cur.execute(statement)
                if migration.name == "002_enrollment_audit.sql":
                    trigger_sql = {
                        "after_enrollment_insert": "CREATE TRIGGER after_enrollment_insert AFTER INSERT ON enrollments FOR EACH ROW INSERT INTO enrollment_audit(enrollment_id,student_id,course_id,action_type) VALUES(NEW.enrollment_id,NEW.student_id,NEW.course_id,'INSERT')",
                        "after_enrollment_update": "CREATE TRIGGER after_enrollment_update AFTER UPDATE ON enrollments FOR EACH ROW INSERT INTO enrollment_audit(enrollment_id,student_id,course_id,action_type) VALUES(NEW.enrollment_id,NEW.student_id,NEW.course_id,'UPDATE')",
                        "after_enrollment_delete": "CREATE TRIGGER after_enrollment_delete AFTER DELETE ON enrollments FOR EACH ROW INSERT INTO enrollment_audit(enrollment_id,student_id,course_id,action_type) VALUES(OLD.enrollment_id,OLD.student_id,OLD.course_id,'DELETE')",
                    }
                    cur.execute("SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s", (Config.DB_NAME,))
                    existing_triggers = {row[0] for row in cur.fetchall()}
                    for name, statement in trigger_sql.items():
                        if name not in existing_triggers:
                            cur.execute(statement)
                cur.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (migration.name,))
                conn.commit()
                print("Applied:", migration.name)
            except Exception:
                conn.rollback()
                raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply unapplied additive SQL migration files.")
    try:
        run(parser.parse_args().apply)
    except (mysql.connector.Error, RuntimeError) as error:
        raise SystemExit(f"Migration stopped safely: {error}") from None
