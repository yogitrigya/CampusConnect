"""Opt-in destructive integration checks. Requires an isolated *_test database."""
import os
import uuid
import unittest
from unittest.mock import patch

import mysql.connector

from app import create_app
from app.config import Config


RUN = os.getenv("CAMPUSCONNECT_RUN_DB_TESTS") == "1"


@unittest.skipUnless(RUN, "Set CAMPUSCONNECT_RUN_DB_TESTS=1 to run isolated MySQL integration tests.")
class MySQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_name = os.getenv("TEST_DB_NAME", "")
        if not cls.db_name.endswith("_test"):
            raise RuntimeError("Integration tests only run when TEST_DB_NAME ends with _test.")
        config = mysql.connector.connect(host=Config.DB_HOST,port=Config.DB_PORT,user=Config.DB_USER,
            password=Config.DB_PASSWORD,database=cls.db_name,connection_timeout=Config.DB_CONNECT_TIMEOUT)
        config.close()
        from scripts.migrate import run
        with patch("scripts.migrate.Config.DB_NAME",cls.db_name):
            run(apply=True)
        cls.app = create_app({"TESTING":True,"SECRET_KEY":"mysql-integration-test","DB_HOST":Config.DB_HOST,
            "DB_PORT":Config.DB_PORT,"DB_USER":Config.DB_USER,"DB_PASSWORD":Config.DB_PASSWORD,
            "DB_NAME":cls.db_name,"DB_CONNECT_TIMEOUT":Config.DB_CONNECT_TIMEOUT})

    def setUp(self):
        self.marker=uuid.uuid4().hex[:10]
        self.conn=mysql.connector.connect(host=Config.DB_HOST,port=Config.DB_PORT,user=Config.DB_USER,
            password=Config.DB_PASSWORD,database=self.db_name,connection_timeout=Config.DB_CONNECT_TIMEOUT)
        self.cur=self.conn.cursor()
        self.cur.execute("INSERT INTO departments(department_name) VALUES(%s)",(f"Test Department {self.marker}",))
        self.department_id=self.cur.lastrowid
        self.cur.execute("INSERT INTO users(email,password_hash,role) VALUES(%s,%s,'student')",(f"s-{self.marker}@test.invalid","not-used"))
        student_user=self.cur.lastrowid
        self.cur.execute("INSERT INTO students(user_id,roll_no,name,department_id,admission_year) VALUES(%s,%s,%s,%s,2025)",(student_user,f"T-{self.marker}","Integration Student",self.department_id))
        self.student_id=self.cur.lastrowid
        self.cur.execute("INSERT INTO users(email,password_hash,role) VALUES(%s,%s,'placement_officer')",(f"p-{self.marker}@test.invalid","not-used"))
        self.officer_user=self.cur.lastrowid
        self.cur.execute("INSERT INTO academic_profiles(student_id,cgpa,tenth_percentage,twelfth_percentage,active_backlogs) VALUES(%s,8.00,80,80,0)",(self.student_id,))
        self.skill=f"IntegrationSkill-{self.marker}"
        self.cur.execute("INSERT INTO student_skills(student_id,skill_name) VALUES(%s,%s)",(self.student_id,self.skill))
        self.cur.execute("INSERT INTO companies(company_name) VALUES(%s)",(f"Integration Company {self.marker}",))
        self.company_id=self.cur.lastrowid
        self.cur.execute("INSERT INTO semesters(semester_number,academic_year) VALUES(1,%s)",(f"T-{self.marker}",))
        self.semester_id=self.cur.lastrowid
        self.cur.execute("INSERT INTO courses(course_code,course_name,credits,department_id) VALUES(%s,%s,3,%s)",(f"T-{self.marker}","Integration Course",self.department_id))
        self.course_id=self.cur.lastrowid
        self.cur.execute("INSERT INTO jobs(company_id,title,minimum_cgpa,minimum_tenth_percentage,minimum_twelfth_percentage,maximum_active_backlogs,created_by) VALUES(%s,%s,7.00,70,70,0,%s)",(self.company_id,"Integration Role",self.officer_user))
        self.job_id=self.cur.lastrowid
        self.cur.execute("INSERT INTO job_required_skills(job_id,skill_name) VALUES(%s,%s)",(self.job_id,self.skill))
        self.conn.commit()
        self.client=self.app.test_client()
        self.client.get("/api/auth/csrf")
        with self.client.session_transaction() as sess:
            self.csrf=sess["csrf_token"]

    def tearDown(self):
        self.conn.rollback()
        self.cur.execute("DELETE FROM applications WHERE student_id=%s",(getattr(self,"student_id",-1),))
        self.cur.execute("DELETE FROM jobs WHERE company_id=%s",(getattr(self,"company_id",-1),))
        self.cur.execute("DELETE FROM companies WHERE company_id=%s",(getattr(self,"company_id",-1),))
        self.cur.execute("DELETE FROM students WHERE student_id=%s",(getattr(self,"student_id",-1),))
        self.cur.execute("DELETE FROM enrollment_audit WHERE student_id=%s",(getattr(self,"student_id",-1),))
        self.cur.execute("DELETE FROM courses WHERE course_id=%s",(getattr(self,"course_id",-1),))
        self.cur.execute("DELETE FROM semesters WHERE semester_id=%s",(getattr(self,"semester_id",-1),))
        self.cur.execute("DELETE FROM users WHERE email LIKE %s",(f"s-{self.marker}@test.invalid",))
        self.cur.execute("DELETE FROM users WHERE user_id=%s",(getattr(self,"officer_user",-1),))
        self.cur.execute("DELETE FROM departments WHERE department_id=%s",(getattr(self,"department_id",-1),))
        self.conn.commit(); self.cur.close(); self.conn.close()

    def signed_in(self, role, user_id):
        with self.client.session_transaction() as sess:
            sess.update(role=role,user_id=user_id,csrf_token=self.csrf)

    def write_headers(self): return {"X-CSRF-Token":self.csrf}

    def test_database_connection(self):
        conn=mysql.connector.connect(host=Config.DB_HOST,port=Config.DB_PORT,user=Config.DB_USER,
            password=Config.DB_PASSWORD,database=self.db_name,connection_timeout=Config.DB_CONNECT_TIMEOUT)
        cur=conn.cursor(); cur.execute("SELECT 1"); self.assertEqual(cur.fetchone()[0],1); cur.close(); conn.close()

    def test_placement_eligibility_and_duplicate_application_constraint(self):
        self.signed_in("placement_officer",self.officer_user)
        eligible=self.client.get(f"/api/jobs/{self.job_id}/eligible-students")
        self.assertEqual(eligible.status_code,200)
        self.assertEqual([x["student_id"] for x in eligible.json["data"]],[self.student_id])
        self.signed_in("student",self._student_user_id())
        path=f"/api/jobs/{self.job_id}/apply"
        first=self.client.post(path,json={},headers=self.write_headers())
        second=self.client.post(path,json={},headers=self.write_headers())
        self.assertEqual(first.status_code,201)
        self.assertEqual(second.status_code,409)

    def _student_user_id(self):
        cur=self.conn.cursor(); cur.execute("SELECT user_id FROM students WHERE student_id=%s",(self.student_id,)); value=cur.fetchone()[0]; cur.close(); return value

    def test_ineligible_student_cannot_apply(self):
        self.cur.execute("UPDATE academic_profiles SET cgpa=6.00 WHERE student_id=%s",(self.student_id,)); self.conn.commit()
        self.signed_in("student",self._student_user_id())
        response=self.client.post(f"/api/jobs/{self.job_id}/apply",json={},headers=self.write_headers())
        self.assertEqual(response.status_code,422)

    def test_interview_and_offer_workflow(self):
        self.cur.execute("INSERT INTO applications(job_id,student_id,status) VALUES(%s,%s,'shortlisted')",(self.job_id,self.student_id))
        application_id=self.cur.lastrowid; self.conn.commit()
        self.signed_in("placement_officer",self.officer_user)
        interview=self.client.post(f"/api/applications/{application_id}/interviews",json={
            "round_number":1,"scheduled_at":"2099-05-10T10:00","mode":"online"},headers=self.write_headers())
        self.assertEqual(interview.status_code,201)
        offer=self.client.post(f"/api/applications/{application_id}/offers",json={"package_amount":1200000,"currency":"INR"},headers=self.write_headers())
        self.assertEqual(offer.status_code,201)
        self.cur.execute("SELECT status FROM applications WHERE application_id=%s",(application_id,))
        self.assertEqual(self.cur.fetchone()[0],"offered")

    def test_transaction_rolls_back_profile_change_on_error(self):
        from app.database.connection import transaction
        with self.assertRaises(RuntimeError):
            with self.app.app_context():
                with transaction(dictionary=False) as cursor:
                    cursor.execute("UPDATE academic_profiles SET cgpa=9.90 WHERE student_id=%s",(self.student_id,))
                    raise RuntimeError("force rollback")
        self.cur.execute("SELECT cgpa FROM academic_profiles WHERE student_id=%s",(self.student_id,))
        self.assertEqual(float(self.cur.fetchone()[0]),8.0)

    def test_enrollment_audit_trigger_preserves_insert_update_delete_history(self):
        self.cur.execute("INSERT INTO enrollments(student_id,course_id,semester_id) VALUES(%s,%s,%s)",(self.student_id,self.course_id,self.semester_id))
        enrollment_id=self.cur.lastrowid
        self.cur.execute("UPDATE enrollments SET semester_id=%s WHERE enrollment_id=%s",(self.semester_id,enrollment_id))
        self.cur.execute("DELETE FROM enrollments WHERE enrollment_id=%s",(enrollment_id,))
        self.conn.commit()
        self.cur.execute("SELECT action_type FROM enrollment_audit WHERE enrollment_id=%s ORDER BY audit_id",(enrollment_id,))
        self.assertEqual([r[0] for r in self.cur.fetchall()],["INSERT","UPDATE","DELETE"])


if __name__ == "__main__": unittest.main()
