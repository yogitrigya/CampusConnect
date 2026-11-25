import unittest
from unittest.mock import patch
from mysql.connector import Error as MySQLError

from app import create_app
from app.config import TestConfig


class FakeCursor:
    lastrowid = 42
    rowcount = 1
    def __init__(self): self.executed = []
    def execute(self, sql, params=()): self.executed.append((sql, params))
    def close(self): pass


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.client.get("/api/auth/csrf")
        with self.client.session_transaction() as sess:
            self.csrf = sess["csrf_token"]

    def headers(self):
        return {"X-CSRF-Token": self.csrf}

    def test_pages_load_without_database(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/login").status_code, 200)

    def test_registration_explains_unavailable_department_lookup(self):
        with patch("app.database.connection.fetch_all", side_effect=MySQLError("offline")):
            response=self.client.get("/register")
        self.assertEqual(response.status_code,200)
        self.assertIn(b"department list could not be loaded",response.data.lower())
        self.assertIn(b"disabled",response.data)

    def test_registration_explains_empty_department_table(self):
        with patch("app.database.connection.fetch_all", return_value=[]):
            response=self.client.get("/register")
        self.assertIn(b"no departments are in the database yet",response.data.lower())

    def test_unauthenticated_api_is_rejected(self):
        response = self.client.get("/api/students/1")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["error"]["code"], "unauthenticated")

    def test_csrf_is_required_for_writes(self):
        response = self.client.post("/api/auth/logout", json={}, headers={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"]["code"], "csrf_failed")

    def test_student_cannot_create_administrative_student_record(self):
        with self.client.session_transaction() as sess:
            sess.update(user_id=10, role="student", csrf_token=self.csrf)
        response = self.client.post("/api/students", json={"name":"Test","roll_no":"T-1","department_id":1}, headers=self.headers())
        self.assertEqual(response.status_code, 403)

    def test_student_registration_is_student_only_and_transactional(self):
        fake = FakeCursor()
        with patch("app.auth.routes.transaction") as transaction:
            transaction.return_value.__enter__.return_value = fake
            response = self.client.post("/api/auth/register", json={
                "email":"new.student@example.edu", "password":"correct-horse-2026", "name":"New Student",
                "roll_no":"CC-2601", "department_id":3, "role":"admin"
            }, headers=self.headers())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(fake.executed), 2)
        self.assertIn("'student'", fake.executed[0][0])
        self.assertNotIn("admin", fake.executed[0][1])
        transaction.return_value.__exit__.assert_called_once_with(None, None, None)

    def test_login_does_not_return_password_hash(self):
        user = {"user_id":8,"email":"person@example.edu","password_hash":"hashed","role":"student","display_name":"Person"}
        with patch("app.auth.routes.fetch_one", return_value=user), patch("app.auth.routes.bcrypt.checkpw", return_value=True):
            response = self.client.post("/api/auth/login", json={"email":"person@example.edu","password":"some-password"}, headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password_hash", response.get_data(as_text=True))
        self.assertEqual(response.json["data"]["role"], "student")
        self.assertTrue(response.json["data"]["csrf_token"])

    def test_transaction_commits_and_rolls_back(self):
        class Connection:
            def __init__(self): self.commits=0; self.rollbacks=0; self.cur=FakeCursor()
            def cursor(self, dictionary=True): return self.cur
            def commit(self): self.commits += 1
            def rollback(self): self.rollbacks += 1
        conn=Connection()
        with self.app.app_context(), patch("app.database.connection.get_connection", return_value=conn):
            from app.database.connection import transaction
            with transaction() as cur: cur.execute("SELECT 1")
            self.assertEqual(conn.commits,1)
            with self.assertRaises(RuntimeError):
                with transaction(): raise RuntimeError("expected")
            self.assertEqual(conn.rollbacks,1)


if __name__ == "__main__":
    unittest.main()
