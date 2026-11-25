"""Read-only inventory of the live CampusConnect schema. Never prints row data."""
import sys
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.migrate import connect, REQUIRED_CORE


def main():
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT TABLE_NAME,TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME")
        objects = cur.fetchall()
        print("Database object inventory:")
        for name, kind in objects:
            print(f"  {kind}: {name}")
        present = {name for name, kind in objects if kind == "BASE TABLE"}
        missing = REQUIRED_CORE - present
        print("Core tables:", "present" if not missing else "missing " + ", ".join(sorted(missing)))
        cur.execute("SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION")
        current = None
        for table, name, kind, nullable, key in cur.fetchall():
            if table != current:
                current = table
                print(f"\n{table}")
            print(f"  {name}: {kind}; nullable={nullable}; key={key or '-'}")
        for query, label in [
            ("SELECT TRIGGER_NAME,EVENT_MANIPULATION,EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() ORDER BY TRIGGER_NAME", "Triggers"),
            ("SELECT ROUTINE_NAME,ROUTINE_TYPE FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() ORDER BY ROUTINE_TYPE,ROUTINE_NAME", "Procedures and functions"),
        ]:
            cur.execute(query)
            rows = cur.fetchall()
            print(f"\n{label}:")
            for row in rows: print("  " + " · ".join(str(value) for value in row))
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except mysql.connector.Error as error:
        raise SystemExit(f"Database audit could not connect: {error}") from None
