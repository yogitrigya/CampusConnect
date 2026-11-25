"""REST endpoints for academic, recruitment, and reporting workflows."""
from datetime import datetime
import math

from flask import Blueprint, jsonify, request, session
from mysql.connector import IntegrityError, Error as MySQLError

from app.auth.permissions import login_required, roles_required
from app.database.connection import execute, fetch_all, fetch_one, transaction

api_bp = Blueprint("api", __name__)


def ok(data, status=200):
    return jsonify(data=data), status


def fail(message, status=400, code="invalid_request"):
    return jsonify(error={"code": code, "message": message}), status


def body():
    return request.get_json(silent=True) or {}


def positive_int(value, label):
    try:
        number = int(value)
        if number < 1:
            raise ValueError
        return number
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a positive integer.")


def db_call(fn):
    try:
        return fn()
    except IntegrityError:
        return fail("The request conflicts with existing data or a database constraint.", 409, "conflict")
    except MySQLError:
        return fail("The database could not complete this request.", 503, "database_unavailable")


def faculty_department_id():
    row = fetch_one("SELECT department_id FROM faculty WHERE user_id=%s", (session.get("user_id"),))
    return row["department_id"] if row else None


def faculty_owns_enrollment(enrollment_id):
    department_id = faculty_department_id()
    if not department_id:
        return False
    return bool(fetch_one("SELECT e.enrollment_id FROM enrollments e JOIN courses c ON c.course_id=e.course_id JOIN students s ON s.student_id=e.student_id WHERE e.enrollment_id=%s AND c.department_id=%s AND s.department_id=%s", (enrollment_id,department_id,department_id)))


@api_bp.get("/auth/csrf")
def csrf():
    from flask import session as flask_session
    return ok({"csrf_token": flask_session.get("csrf_token", "")})


@api_bp.get("/departments")
def departments():
    return db_call(lambda: ok(fetch_all("SELECT department_id, department_name FROM departments ORDER BY department_name")))


@api_bp.post("/departments")
@roles_required("admin")
def create_department():
    name = str(body().get("department_name", "")).strip()
    if not name or len(name) > 100:
        return fail("Department name is required (up to 100 characters).")
    return db_call(lambda: ok({"department_id": execute("INSERT INTO departments (department_name) VALUES (%s)", (name,))[0]}, 201))


@api_bp.put("/departments/<int:department_id>")
@roles_required("admin")
def update_department(department_id):
    name=str(body().get("department_name", "")).strip()
    if not name or len(name)>100:
        return fail("Department name is required.")
    return db_call(lambda: ok({"updated":execute("UPDATE departments SET department_name=%s WHERE department_id=%s",(name,department_id))[1]>0}))


@api_bp.delete("/departments/<int:department_id>")
@roles_required("admin")
def delete_department(department_id):
    return db_call(lambda: ok({"deleted":execute("DELETE FROM departments WHERE department_id=%s",(department_id,))[1]>0}))


@api_bp.get("/students")
@roles_required("admin", "faculty", "placement_officer")
def students():
    department_id = request.args.get("department_id")
    search = request.args.get("q", "").strip()
    sql = "SELECT s.student_id,s.user_id,s.roll_no,s.name,s.department_id,s.admission_year,d.department_name,ap.cgpa,ap.tenth_percentage,ap.twelfth_percentage,ap.active_backlogs FROM students s LEFT JOIN departments d ON d.department_id=s.department_id LEFT JOIN academic_profiles ap ON ap.student_id=s.student_id WHERE 1=1"
    params = []
    if session.get("role") == "faculty":
        assigned = faculty_department_id()
        if not assigned:
            return fail("Your faculty profile has no department assigned.",403,"forbidden")
        if department_id and str(department_id) != str(assigned):
            return fail("Faculty can only view students in their department.",403,"forbidden")
        department_id = assigned
    if department_id:
        try:
            params.append(positive_int(department_id, "department_id"))
        except ValueError as ex:
            return fail(str(ex))
        sql += " AND s.department_id=%s"
    if search:
        sql += " AND (s.name LIKE %s OR s.roll_no LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    sql += " ORDER BY s.name LIMIT 500"
    return db_call(lambda: ok(fetch_all(sql, tuple(params))))


@api_bp.post("/students")
@roles_required("admin")
def create_student():
    data = body()
    name, roll = str(data.get("name", "")).strip(), str(data.get("roll_no", "")).strip()
    if not name or len(name) > 100 or not roll or len(roll) > 30:
        return fail("Name and roll number are required.")
    try:
        dept = positive_int(data.get("department_id"), "department_id")
        admission = data.get("admission_year") or None
        with transaction(dictionary=False) as cur:
            cur.execute("INSERT INTO students (roll_no,name,department_id,admission_year) VALUES (%s,%s,%s,%s)", (roll, name, dept, admission))
            student_id = cur.lastrowid
        return ok({"student_id": student_id}, 201)
    except ValueError as ex:
        return fail(str(ex))
    except IntegrityError:
        return fail("Roll number or department conflicts with existing data.", 409, "conflict")
    except MySQLError:
        return fail("The database could not complete this request.", 503, "database_unavailable")


@api_bp.get("/students/<int:student_id>")
@login_required
def student_detail(student_id):
    if session.get("role") == "student":
        own = fetch_one("SELECT student_id FROM students WHERE user_id=%s", (session["user_id"],))
        if not own or own["student_id"] != student_id:
            return fail("You can only view your own student profile.", 403, "forbidden")
    elif session.get("role") not in {"admin", "faculty", "placement_officer"}:
        return fail("You do not have permission for this action.", 403, "forbidden")
    elif session.get("role") == "faculty":
        assigned = faculty_department_id()
        target = fetch_one("SELECT department_id FROM students WHERE student_id=%s",(student_id,))
        if not assigned or not target or target["department_id"] != assigned:
            return fail("Faculty can only view students in their department.",403,"forbidden")
    def load():
        profile = fetch_one("SELECT s.student_id,s.user_id,s.roll_no,s.name,s.department_id,s.admission_year,d.department_name,ap.cgpa,ap.tenth_percentage,ap.twelfth_percentage,ap.active_backlogs FROM students s LEFT JOIN departments d ON d.department_id=s.department_id LEFT JOIN academic_profiles ap ON ap.student_id=s.student_id WHERE s.student_id=%s", (student_id,))
        if not profile:
            return fail("Student not found.", 404, "not_found")
        profile["skills"] = fetch_all("SELECT skill_name FROM student_skills WHERE student_id=%s ORDER BY skill_name", (student_id,))
        return ok(profile)
    return db_call(load)


@api_bp.put("/students/<int:student_id>/academic-profile")
@roles_required("admin", "faculty")
def update_academic_profile(student_id):
    data = body()
    try:
        cgpa = float(data.get("cgpa"))
        tenth, twelfth = float(data.get("tenth_percentage")), float(data.get("twelfth_percentage"))
        backlogs = int(data.get("active_backlogs"))
        if not 0 <= cgpa <= 10 or not 0 <= tenth <= 100 or not 0 <= twelfth <= 100 or backlogs < 0:
            raise ValueError("Values are outside valid ranges.")
    except (TypeError, ValueError) as ex:
        return fail(str(ex) or "Enter valid academic profile values.")
    if session.get("role") == "faculty":
        assigned = faculty_department_id()
        student = fetch_one("SELECT department_id FROM students WHERE student_id=%s",(student_id,))
        if not assigned or not student or student["department_id"] != assigned:
            return fail("Faculty can only update academic profiles in their department.",403,"forbidden")
    sql = "INSERT INTO academic_profiles (student_id,cgpa,tenth_percentage,twelfth_percentage,active_backlogs) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE cgpa=VALUES(cgpa),tenth_percentage=VALUES(tenth_percentage),twelfth_percentage=VALUES(twelfth_percentage),active_backlogs=VALUES(active_backlogs)"
    return db_call(lambda: (execute(sql,(student_id,cgpa,tenth,twelfth,backlogs)), ok({"updated": True}))[1])


@api_bp.get("/students/<int:student_id>/skills")
@login_required
def list_student_skills(student_id):
    role = session.get("role")
    if role == "student":
        owner = fetch_one("SELECT student_id FROM students WHERE user_id=%s", (session["user_id"],))
        if not owner or owner["student_id"] != student_id:
            return fail("You can only view your own skills.", 403, "forbidden")
    elif role not in {"admin", "faculty", "placement_officer"}:
        return fail("You do not have permission for this action.", 403, "forbidden")
    elif role == "faculty":
        assigned=faculty_department_id()
        target=fetch_one("SELECT department_id FROM students WHERE student_id=%s",(student_id,))
        if not assigned or not target or target["department_id"] != assigned:
            return fail("Faculty can only view skills in their department.",403,"forbidden")
    return db_call(lambda: ok(fetch_all("SELECT skill_name FROM student_skills WHERE student_id=%s ORDER BY skill_name",(student_id,))))


@api_bp.get("/students/<int:student_id>/performance")
@login_required
def student_performance(student_id):
    role=session.get("role")
    if role == "student":
        owner=fetch_one("SELECT student_id FROM students WHERE user_id=%s",(session["user_id"],))
        if not owner or owner["student_id"] != student_id:
            return fail("You can only view your own academic performance.",403,"forbidden")
    elif role == "faculty":
        assigned=faculty_department_id()
        target=fetch_one("SELECT department_id FROM students WHERE student_id=%s",(student_id,))
        if not assigned or not target or target["department_id"] != assigned:
            return fail("Faculty can only view performance in their department.",403,"forbidden")
    elif role not in {"admin","placement_officer"}:
        return fail("You do not have permission for this action.",403,"forbidden")
    def load():
        marks=fetch_all("SELECT c.course_code,c.course_name,r.assessment_name,r.score,r.maximum_score,ROUND(100*r.score/r.maximum_score,2) AS percentage FROM exam_results r JOIN enrollments e ON e.enrollment_id=r.enrollment_id JOIN courses c ON c.course_id=e.course_id WHERE e.student_id=%s ORDER BY c.course_code,r.assessment_name",(student_id,))
        attendance=fetch_all("SELECT c.course_code,c.course_name,COUNT(*) AS sessions,SUM(a.status IN ('present','late')) AS attended,ROUND(100*SUM(a.status IN ('present','late'))/NULLIF(COUNT(*),0),1) AS attendance_rate FROM attendance_records a JOIN enrollments e ON e.enrollment_id=a.enrollment_id JOIN courses c ON c.course_id=e.course_id WHERE e.student_id=%s GROUP BY c.course_id,c.course_code,c.course_name ORDER BY c.course_code",(student_id,))
        return ok({"marks":marks,"attendance":attendance})
    return db_call(load)


@api_bp.put("/students/<int:student_id>/skills")
@login_required
def replace_student_skills(student_id):
    role = session.get("role")
    if role == "student":
        owner = fetch_one("SELECT student_id FROM students WHERE user_id=%s", (session["user_id"],))
        if not owner or owner["student_id"] != student_id:
            return fail("You can only update your own skills.", 403, "forbidden")
    elif role not in {"admin", "faculty"}:
        return fail("You do not have permission for this action.", 403, "forbidden")
    if role == "faculty":
        assigned = faculty_department_id()
        student = fetch_one("SELECT department_id FROM students WHERE student_id=%s",(student_id,))
        if not assigned or not student or student["department_id"] != assigned:
            return fail("Faculty can only update skills in their department.",403,"forbidden")
    skills = body().get("skills")
    if not isinstance(skills, list) or len(skills) > 50 or any(not isinstance(s, str) or not s.strip() or len(s.strip()) > 80 for s in skills):
        return fail("Skills must be a list of up to 50 non-empty names.")
    skills = sorted({s.strip() for s in skills})
    def replace():
        with transaction(dictionary=False) as cur:
            cur.execute("DELETE FROM student_skills WHERE student_id=%s", (student_id,))
            for skill in skills:
                cur.execute("INSERT INTO student_skills(student_id,skill_name) VALUES(%s,%s)",(student_id,skill))
        return ok({"skills": skills})
    return db_call(replace)


@api_bp.put("/students/<int:student_id>")
@roles_required("admin")
def update_student(student_id):
    data = body()
    try:
        with transaction(dictionary=False) as cur:
            cur.execute("UPDATE students SET name=COALESCE(%s,name), department_id=COALESCE(%s,department_id), admission_year=COALESCE(%s,admission_year) WHERE student_id=%s", (data.get("name"), data.get("department_id"), data.get("admission_year"), student_id))
            if not cur.rowcount:
                cur.execute("SELECT student_id FROM students WHERE student_id=%s", (student_id,))
                if not cur.fetchone():
                    return fail("Student not found.", 404, "not_found")
        return ok({"student_id": student_id, "updated": True})
    except IntegrityError:
        return fail("The department is invalid.", 409, "conflict")
    except MySQLError:
        return fail("The database could not complete this request.", 503, "database_unavailable")


@api_bp.delete("/students/<int:student_id>")
@roles_required("admin")
def delete_student(student_id):
    def remove():
        _, count = execute("DELETE FROM students WHERE student_id=%s", (student_id,))
        if not count:
            return fail("Student not found.", 404, "not_found")
        return ok({"deleted": True})
    return db_call(remove)


@api_bp.get("/courses")
@login_required
def courses():
    if session.get("role") == "faculty":
        assigned = faculty_department_id()
        if not assigned:
            return fail("Your faculty profile has no department assigned.",403,"forbidden")
        sql="SELECT c.course_id,c.course_code,c.course_name,c.credits,c.department_id,d.department_name FROM courses c LEFT JOIN departments d ON d.department_id=c.department_id WHERE c.department_id=%s ORDER BY c.course_code"
        return db_call(lambda: ok(fetch_all(sql,(assigned,))))
    return db_call(lambda: ok(fetch_all("SELECT c.course_id,c.course_code,c.course_name,c.credits,c.department_id,d.department_name FROM courses c LEFT JOIN departments d ON d.department_id=c.department_id ORDER BY c.course_code")))


@api_bp.post("/courses")
@roles_required("admin", "faculty")
def create_course():
    data = body()
    code, name = str(data.get("course_code", "")).strip(), str(data.get("course_name", "")).strip()
    try:
        credits = positive_int(data.get("credits"), "credits")
        department = positive_int(data.get("department_id"), "department_id")
    except ValueError as ex:
        return fail(str(ex))
    if not code or len(code) > 20 or not name or len(name) > 100:
        return fail("Course code and name are required.")
    if session.get("role") == "faculty" and faculty_department_id() != department:
        return fail("Faculty can only manage courses in their department.",403,"forbidden")
    return db_call(lambda: ok({"course_id": execute("INSERT INTO courses (course_code,course_name,credits,department_id) VALUES (%s,%s,%s,%s)", (code,name,credits,department))[0]}, 201))


@api_bp.get("/semesters")
@login_required
def semesters():
    return db_call(lambda: ok(fetch_all("SELECT semester_id,semester_number,academic_year FROM semesters ORDER BY academic_year DESC,semester_number")))


@api_bp.post("/semesters")
@roles_required("admin")
def create_semester():
    data = body()
    try:
        number = positive_int(data.get("semester_number"), "semester_number")
    except ValueError as ex:
        return fail(str(ex))
    year = str(data.get("academic_year", "")).strip()
    if not year or len(year) > 20:
        return fail("Academic year is required.")
    return db_call(lambda: ok({"semester_id": execute("INSERT INTO semesters(semester_number,academic_year) VALUES(%s,%s)",(number,year))[0]},201))


@api_bp.get("/faculty")
@roles_required("admin", "faculty")
def faculty_list():
    sql = "SELECT f.faculty_id,f.user_id,u.email,f.department_id,d.department_name,f.designation FROM faculty f LEFT JOIN users u ON u.user_id=f.user_id LEFT JOIN departments d ON d.department_id=f.department_id ORDER BY u.email"
    return db_call(lambda: ok(fetch_all(sql)))


@api_bp.post("/enrollments")
@roles_required("admin", "faculty")
def create_enrollment():
    data = body()
    try:
        values = tuple(positive_int(data.get(k), k) for k in ("student_id", "course_id", "semester_id"))
    except ValueError as ex:
        return fail(str(ex))
    if session.get("role") == "faculty":
        assigned=faculty_department_id()
        if not assigned or not fetch_one("SELECT c.course_id FROM courses c JOIN students s ON s.student_id=%s WHERE c.course_id=%s AND c.department_id=%s AND s.department_id=%s",(values[0],values[1],assigned,assigned)):
            return fail("Faculty can only enroll students in courses in their department.",403,"forbidden")
    return db_call(lambda: ok({"enrollment_id": execute("INSERT INTO enrollments (student_id,course_id,semester_id) VALUES (%s,%s,%s)", values)[0]}, 201))


@api_bp.post("/attendance")
@roles_required("admin", "faculty")
def record_attendance():
    data = body()
    try:
        enrollment = positive_int(data.get("enrollment_id"), "enrollment_id")
        attendance_date = datetime.strptime(str(data.get("attendance_date", "")), "%Y-%m-%d").date()
        status = str(data.get("status", "")).lower()
        if status not in {"present", "absent", "late", "excused"}:
            raise ValueError("Status must be present, absent, late, or excused.")
    except ValueError as ex:
        return fail(str(ex))
    if session.get("role") == "faculty" and not faculty_owns_enrollment(enrollment):
        return fail("Faculty can only record attendance for their department's enrollments.",403,"forbidden")
    return db_call(lambda: ok({"attendance_id": execute("INSERT INTO attendance_records (enrollment_id,attendance_date,status,recorded_by) VALUES (%s,%s,%s,%s)", (enrollment, attendance_date, status, session["user_id"]))[0]}, 201))


@api_bp.post("/marks")
@roles_required("admin", "faculty")
def record_marks():
    data = body()
    try:
        enrollment = positive_int(data.get("enrollment_id"), "enrollment_id")
        label = str(data.get("assessment_name", "")).strip()
        score, maximum = float(data.get("score")), float(data.get("maximum_score"))
        if not label or len(label) > 100 or not math.isfinite(score) or not math.isfinite(maximum) or score < 0 or maximum <= 0 or score > maximum:
            raise ValueError("Enter a valid assessment and score within its maximum.")
    except (TypeError, ValueError) as ex:
        return fail(str(ex) or "Enter a valid score.")
    if session.get("role") == "faculty" and not faculty_owns_enrollment(enrollment):
        return fail("Faculty can only record results for their department's enrollments.",403,"forbidden")
    return db_call(lambda: ok({"result_id": execute("INSERT INTO exam_results (enrollment_id,assessment_name,score,maximum_score,recorded_by) VALUES (%s,%s,%s,%s,%s)", (enrollment,label,score,maximum,session["user_id"]))[0]}, 201))


@api_bp.get("/companies")
@login_required
def companies():
    return db_call(lambda: ok(fetch_all("SELECT company_id,company_name,website,industry,description,created_at FROM companies ORDER BY company_name")))


@api_bp.post("/companies")
@roles_required("admin", "placement_officer")
def create_company():
    data = body()
    name = str(data.get("company_name", "")).strip()
    if not name or len(name) > 150:
        return fail("Company name is required (up to 150 characters).")
    sql = "INSERT INTO companies (company_name,website,industry,description) VALUES (%s,%s,%s,%s)"
    vals = (name, data.get("website") or None, data.get("industry") or None, data.get("description") or None)
    return db_call(lambda: ok({"company_id": execute(sql, vals)[0]}, 201))


@api_bp.get("/companies/<int:company_id>/recruiters")
@roles_required("admin", "placement_officer")
def recruiters(company_id):
    return db_call(lambda: ok(fetch_all("SELECT recruiter_id,company_id,name,email,phone FROM recruiters WHERE company_id=%s ORDER BY name", (company_id,))))


@api_bp.post("/companies/<int:company_id>/recruiters")
@roles_required("admin", "placement_officer")
def add_recruiter(company_id):
    data = body()
    name, email = str(data.get("name", "")).strip(), str(data.get("email", "")).strip().lower()
    if not name or not email or len(name) > 100 or len(email) > 150:
        return fail("Recruiter name and email are required.")
    sql = "INSERT INTO recruiters(company_id,name,email,phone) VALUES(%s,%s,%s,%s)"
    return db_call(lambda: ok({"recruiter_id": execute(sql,(company_id,name,email,data.get("phone")))[0]},201))


@api_bp.put("/companies/<int:company_id>")
@roles_required("admin", "placement_officer")
def update_company(company_id):
    data = body()
    return db_call(lambda: ok({"updated": execute("UPDATE companies SET company_name=COALESCE(%s,company_name),website=%s,industry=%s,description=%s WHERE company_id=%s", (data.get("company_name"),data.get("website"),data.get("industry"),data.get("description"),company_id))[1] > 0}))


def _required_skills(data):
    raw = data.get("required_skills", [])
    if not isinstance(raw, list) or any(not isinstance(s, str) or not s.strip() or len(s.strip()) > 80 for s in raw):
        raise ValueError("required_skills must be a list of skill names.")
    return sorted({s.strip().lower() for s in raw})


@api_bp.get("/jobs")
@login_required
def jobs():
    return db_call(lambda: ok(fetch_all("SELECT j.job_id,j.company_id,c.company_name,j.title,j.description,j.location,j.minimum_cgpa,j.minimum_tenth_percentage,j.minimum_twelfth_percentage,j.maximum_active_backlogs,j.application_deadline,j.status,j.created_at FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.status='open' OR %s IN ('admin','placement_officer') ORDER BY j.created_at DESC", (session["role"],))))


@api_bp.post("/jobs")
@roles_required("admin", "placement_officer")
def create_job():
    data = body()
    title = str(data.get("title", "")).strip()
    if not title or len(title) > 150:
        return fail("Job title is required.")
    try:
        company_id = positive_int(data.get("company_id"), "company_id")
        cgpa = float(data.get("minimum_cgpa", 0))
        tenth, twelfth = float(data.get("minimum_tenth_percentage", 0)), float(data.get("minimum_twelfth_percentage", 0))
        backlogs = int(data.get("maximum_active_backlogs", 0))
        skills = _required_skills(data)
        if not 0 <= cgpa <= 10 or not 0 <= tenth <= 100 or not 0 <= twelfth <= 100 or backlogs < 0:
            raise ValueError("Eligibility thresholds are outside valid ranges.")
    except (ValueError, TypeError) as ex:
        return fail(str(ex) or "Invalid eligibility criteria.")
    def create():
        with transaction(dictionary=False) as cur:
            cur.execute("INSERT INTO jobs (company_id,title,description,location,minimum_cgpa,minimum_tenth_percentage,minimum_twelfth_percentage,maximum_active_backlogs,application_deadline,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (company_id,title,data.get("description"),data.get("location"),cgpa,tenth,twelfth,backlogs,data.get("application_deadline") or None,session["user_id"]))
            job_id = cur.lastrowid
            for skill in skills:
                cur.execute("INSERT INTO job_required_skills (job_id,skill_name) VALUES (%s,%s)", (job_id, skill))
        return ok({"job_id": job_id}, 201)
    return db_call(create)


@api_bp.get("/jobs/<int:job_id>/eligible-students")
@roles_required("admin", "placement_officer")
def eligible_students(job_id):
    sql = """SELECT s.student_id,s.roll_no,s.name,ap.cgpa,ap.tenth_percentage,ap.twelfth_percentage,ap.active_backlogs
      FROM students s JOIN academic_profiles ap ON ap.student_id=s.student_id JOIN jobs j ON j.job_id=%s
      WHERE ap.cgpa>=j.minimum_cgpa AND ap.tenth_percentage>=j.minimum_tenth_percentage
      AND ap.twelfth_percentage>=j.minimum_twelfth_percentage AND ap.active_backlogs<=j.maximum_active_backlogs
      AND NOT EXISTS (SELECT 1 FROM job_required_skills req WHERE req.job_id=j.job_id AND NOT EXISTS
        (SELECT 1 FROM student_skills ss WHERE ss.student_id=s.student_id AND LOWER(ss.skill_name)=LOWER(req.skill_name)))
      ORDER BY s.name"""
    return db_call(lambda: ok(fetch_all(sql, (job_id,))))


@api_bp.patch("/jobs/<int:job_id>")
@roles_required("admin", "placement_officer")
def update_job(job_id):
    status=body().get("status")
    if status not in {"draft","open","closed"}:
        return fail("Job status must be draft, open, or closed.")
    return db_call(lambda: ok({"updated":execute("UPDATE jobs SET status=%s WHERE job_id=%s",(status,job_id))[1]>0}))


@api_bp.post("/jobs/<int:job_id>/apply")
@roles_required("student")
def apply_job(job_id):
    def apply():
        profile = fetch_one("SELECT student_id FROM students WHERE user_id=%s", (session["user_id"],))
        if not profile:
            return fail("Your student profile is missing. Contact an administrator.", 409, "profile_missing")
        eligible = fetch_one("SELECT s.student_id FROM students s JOIN academic_profiles ap ON ap.student_id=s.student_id JOIN jobs j ON j.job_id=%s WHERE s.student_id=%s AND j.status='open' AND (j.application_deadline IS NULL OR j.application_deadline>=CURRENT_DATE()) AND ap.cgpa>=j.minimum_cgpa AND ap.tenth_percentage>=j.minimum_tenth_percentage AND ap.twelfth_percentage>=j.minimum_twelfth_percentage AND ap.active_backlogs<=j.maximum_active_backlogs AND NOT EXISTS (SELECT 1 FROM job_required_skills req WHERE req.job_id=j.job_id AND NOT EXISTS (SELECT 1 FROM student_skills ss WHERE ss.student_id=s.student_id AND LOWER(ss.skill_name)=LOWER(req.skill_name)))", (job_id, profile["student_id"]))
        if not eligible:
            return fail("You are not eligible for this job or applications are closed.", 422, "not_eligible")
        application_id = execute("INSERT INTO applications (job_id,student_id,status) VALUES (%s,%s,'applied')", (job_id,profile["student_id"]))[0]
        return ok({"application_id": application_id, "status": "applied"}, 201)
    return db_call(apply)


@api_bp.get("/applications")
@roles_required("admin", "student", "placement_officer")
def applications():
    sql = "SELECT a.application_id,a.status,a.applied_at,s.student_id,s.name AS student_name,s.roll_no,j.job_id,j.title,c.company_name FROM applications a JOIN students s ON s.student_id=a.student_id JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id"
    params = ()
    if session["role"] == "student":
        sql += " WHERE s.user_id=%s"
        params = (session["user_id"],)
    sql += " ORDER BY a.applied_at DESC"
    return db_call(lambda: ok(fetch_all(sql, params)))


@api_bp.get("/applications/<int:application_id>/interviews")
@roles_required("admin", "student", "placement_officer")
def list_interviews(application_id):
    if session.get("role") == "student":
        owned = fetch_one("SELECT a.application_id FROM applications a JOIN students s ON s.student_id=a.student_id WHERE a.application_id=%s AND s.user_id=%s", (application_id,session["user_id"]))
        if not owned:
            return fail("Application not found.",404,"not_found")
    return db_call(lambda: ok(fetch_all("SELECT interview_id,application_id,round_number,scheduled_at,mode,location_or_link,status,notes FROM interviews WHERE application_id=%s ORDER BY round_number",(application_id,))))


@api_bp.patch("/applications/<int:application_id>")
@roles_required("admin", "placement_officer")
def update_application(application_id):
    status = str(body().get("status", "")).lower()
    allowed = {"applied", "shortlisted", "rejected", "withdrawn", "offered", "hired"}
    if status not in allowed:
        return fail("Choose a valid application status.")
    return db_call(lambda: ok({"updated": execute("UPDATE applications SET status=%s WHERE application_id=%s", (status,application_id))[1] > 0}))


@api_bp.post("/applications/<int:application_id>/interviews")
@roles_required("admin", "placement_officer")
def schedule_interview(application_id):
    data = body()
    try:
        round_number = positive_int(data.get("round_number"), "round_number")
        scheduled_at = datetime.fromisoformat(str(data.get("scheduled_at", "")))
        mode = str(data.get("mode", "online")).lower()
        if mode not in {"online", "in_person"}:
            raise ValueError("Mode must be online or in_person.")
        if scheduled_at <= datetime.now():
            raise ValueError("Interview time must be in the future.")
    except ValueError as ex:
        return fail(str(ex))
    sql = "INSERT INTO interviews (application_id,round_number,scheduled_at,mode,location_or_link,notes,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    params = (application_id,round_number,scheduled_at,mode,data.get("location_or_link"),data.get("notes"),session["user_id"])
    return db_call(lambda: ok({"interview_id": execute(sql,params)[0]}, 201))


@api_bp.patch("/interviews/<int:interview_id>")
@roles_required("admin", "placement_officer")
def update_interview(interview_id):
    data = body()
    status = str(data.get("status", "scheduled")).lower()
    if status not in {"scheduled", "completed", "cancelled", "no_show"}:
        return fail("Choose a valid interview status.")
    return db_call(lambda: ok({"updated": execute("UPDATE interviews SET status=%s,notes=COALESCE(%s,notes) WHERE interview_id=%s", (status,data.get("notes"),interview_id))[1] > 0}))


@api_bp.post("/applications/<int:application_id>/offers")
@roles_required("admin", "placement_officer")
def create_offer(application_id):
    data = body()
    try:
        package = float(data.get("package_amount"))
        if not math.isfinite(package) or package <= 0:
            raise ValueError("Package amount must be greater than zero.")
        currency = str(data.get("currency", "INR")).upper()
        if len(currency) != 3:
            raise ValueError("Currency must be a three-letter code.")
        offer_status = str(data.get("status", "extended")).lower()
        if offer_status not in {"extended", "accepted", "declined", "expired"}:
            raise ValueError("Choose a valid offer status.")
    except (TypeError, ValueError) as ex:
        return fail(str(ex) or "Enter a valid offer amount.")
    def create():
        with transaction(dictionary=False) as cur:
            cur.execute("INSERT INTO offers (application_id,package_amount,currency,offer_date,status) VALUES (%s,%s,%s,%s,%s)", (application_id,package,currency,data.get("offer_date"),offer_status))
            cur.execute("UPDATE applications SET status='offered' WHERE application_id=%s", (application_id,))
            return ok({"offer_id": cur.lastrowid}, 201)
    return db_call(create)


@api_bp.get("/offers")
@roles_required("admin", "student", "placement_officer")
def list_offers():
    sql = "SELECT o.offer_id,o.application_id,o.package_amount,o.currency,o.offer_date,o.status,j.title,c.company_name,s.student_id,s.name AS student_name FROM offers o JOIN applications a ON a.application_id=o.application_id JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id JOIN students s ON s.student_id=a.student_id"
    params = ()
    if session.get("role") == "student":
        sql += " WHERE s.user_id=%s"
        params = (session["user_id"],)
    return db_call(lambda: ok(fetch_all(sql,params)))


@api_bp.patch("/offers/<int:offer_id>")
@roles_required("admin", "placement_officer")
def update_offer(offer_id):
    status = str(body().get("status", "")).lower()
    if status not in {"accepted", "declined", "expired", "extended"}:
        return fail("Choose a valid offer status.")
    def update():
        with transaction(dictionary=False) as cur:
            cur.execute("UPDATE offers SET status=%s WHERE offer_id=%s",(status,offer_id))
            if not cur.rowcount:
                cur.execute("SELECT offer_id FROM offers WHERE offer_id=%s",(offer_id,))
                if not cur.fetchone(): return fail("Offer not found.",404,"not_found")
            if status == "accepted":
                cur.execute("UPDATE applications a JOIN offers o ON o.application_id=a.application_id SET a.status='hired' WHERE o.offer_id=%s",(offer_id,))
        return ok({"updated":True})
    return db_call(update)


@api_bp.get("/reports/overview")
@roles_required("admin", "placement_officer")
def report_overview():
    sql = """SELECT (SELECT COUNT(*) FROM students) AS total_students,
      (SELECT COUNT(*) FROM faculty) AS total_faculty,(SELECT COUNT(*) FROM departments) AS total_departments,
      (SELECT COUNT(*) FROM companies) AS total_companies,(SELECT COUNT(*) FROM jobs WHERE status='open') AS open_jobs,
      (SELECT COUNT(*) FROM applications) AS total_applications,
      (SELECT COUNT(DISTINCT a.student_id) FROM applications a JOIN offers o ON o.application_id=a.application_id WHERE o.status='accepted') AS placed_students,
      (SELECT COALESCE(AVG(package_amount),0) FROM offers WHERE status='accepted') AS average_package,
      (SELECT COALESCE(MAX(package_amount),0) FROM offers WHERE status='accepted') AS highest_package"""
    def load():
        result = fetch_one(sql)
        result["departments"] = fetch_all("SELECT d.department_name,COUNT(DISTINCT s.student_id) AS students,COUNT(DISTINCT CASE WHEN o.status='accepted' THEN s.student_id END) AS placed FROM departments d LEFT JOIN students s ON s.department_id=d.department_id LEFT JOIN applications a ON a.student_id=s.student_id LEFT JOIN offers o ON o.application_id=a.application_id GROUP BY d.department_id,d.department_name ORDER BY d.department_name")
        result["attendance"] = fetch_one("SELECT ROUND(100*SUM(status IN ('present','late'))/NULLIF(COUNT(*),0),1) AS attendance_rate,COUNT(*) AS attendance_records FROM attendance_records")
        return ok(result)
    return db_call(load)


@api_bp.get("/reports/placements")
@roles_required("admin", "placement_officer")
def report_placements():
    return db_call(lambda: ok(fetch_all("SELECT c.company_name,j.title,COUNT(DISTINCT a.student_id) AS applicants,COUNT(DISTINCT CASE WHEN o.status='accepted' THEN a.student_id END) AS placed,AVG(CASE WHEN o.status='accepted' THEN o.package_amount END) AS average_package,MAX(CASE WHEN o.status='accepted' THEN o.package_amount END) AS highest_package FROM jobs j JOIN companies c ON c.company_id=j.company_id LEFT JOIN applications a ON a.job_id=j.job_id LEFT JOIN offers o ON o.application_id=a.application_id GROUP BY j.job_id,c.company_name,j.title ORDER BY placed DESC,applicants DESC")))


@api_bp.get("/dashboard")
@login_required
def dashboard_data():
    role = session.get("role")
    if role in {"admin", "placement_officer"}:
        summary = fetch_one("SELECT (SELECT COUNT(*) FROM students) students,(SELECT COUNT(*) FROM faculty) faculty,(SELECT COUNT(*) FROM companies) companies,(SELECT COUNT(*) FROM jobs WHERE status='open') open_jobs,(SELECT COUNT(*) FROM applications) applications")
        return db_call(lambda: ok({"role": role, "summary": summary, "jobs": fetch_all("SELECT j.job_id,j.title,c.company_name,j.application_deadline FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.status='open' ORDER BY j.created_at DESC LIMIT 8")}))
    if role == "student":
        def student_data():
            student = fetch_one("SELECT student_id,name,roll_no,department_id FROM students WHERE user_id=%s", (session["user_id"],))
            if not student:
                return ok({"role": role, "profile_missing": True})
            return ok({"role": role, "student": student,
                "academic": fetch_one("SELECT cgpa,tenth_percentage,twelfth_percentage,active_backlogs FROM academic_profiles WHERE student_id=%s",(student["student_id"],)),
                "applications": fetch_all("SELECT a.application_id,a.status,j.title,c.company_name,a.applied_at FROM applications a JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id WHERE a.student_id=%s ORDER BY a.applied_at DESC LIMIT 10", (student["student_id"],)),
                "jobs": fetch_all("SELECT j.job_id,j.title,j.minimum_cgpa,j.minimum_tenth_percentage,j.minimum_twelfth_percentage,j.maximum_active_backlogs,j.application_deadline,c.company_name FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.status='open' AND (j.application_deadline IS NULL OR j.application_deadline>=CURRENT_DATE()) AND NOT EXISTS (SELECT 1 FROM applications a WHERE a.job_id=j.job_id AND a.student_id=%s) ORDER BY j.created_at DESC",(student["student_id"],))})
        return db_call(student_data)
    if role == "faculty":
        return db_call(lambda: ok({"role": role, "courses": fetch_all("SELECT c.course_code,c.course_name,COUNT(e.enrollment_id) AS enrolled FROM courses c LEFT JOIN enrollments e ON e.course_id=c.course_id WHERE c.department_id=(SELECT department_id FROM faculty WHERE user_id=%s) GROUP BY c.course_id ORDER BY c.course_code",(session["user_id"],))}))
    return fail("Unknown account role.", 403, "forbidden")
