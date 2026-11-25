-- Optional repeatable demonstration records. Use only in a development/demo DB.
-- Account password hashes are intentionally not seeded; create real accounts via scripts/create_user.py.
USE campusconnect;

INSERT IGNORE INTO departments (department_name) VALUES
('Computer Science Engineering'),('Information Technology');

INSERT IGNORE INTO semesters (semester_number, academic_year) VALUES
(1,'2026-2027'),(2,'2026-2027');

INSERT IGNORE INTO courses (course_code,course_name,credits,department_id)
SELECT 'DEMO-DBMS','Database Management Systems',4,department_id FROM departments WHERE department_name='Computer Science Engineering';

INSERT IGNORE INTO students (roll_no,name,department_id,admission_year)
SELECT 'DEMO-CC-001','Demo Student One',department_id,2025 FROM departments WHERE department_name='Computer Science Engineering';
INSERT IGNORE INTO students (roll_no,name,department_id,admission_year)
SELECT 'DEMO-CC-002','Demo Student Two',department_id,2025 FROM departments WHERE department_name='Computer Science Engineering';

INSERT IGNORE INTO academic_profiles(student_id,cgpa,tenth_percentage,twelfth_percentage,active_backlogs)
SELECT student_id,8.40,91.00,88.00,0 FROM students WHERE roll_no='DEMO-CC-001';
INSERT IGNORE INTO academic_profiles(student_id,cgpa,tenth_percentage,twelfth_percentage,active_backlogs)
SELECT student_id,7.10,82.00,79.00,1 FROM students WHERE roll_no='DEMO-CC-002';

INSERT IGNORE INTO student_skills(student_id,skill_name)
SELECT student_id,'Python' FROM students WHERE roll_no='DEMO-CC-001';
INSERT IGNORE INTO student_skills(student_id,skill_name)
SELECT student_id,'SQL' FROM students WHERE roll_no='DEMO-CC-001';

INSERT IGNORE INTO companies(company_name,website,industry)
VALUES('CampusConnect Demo Systems','https://example.com','Software');
INSERT INTO jobs(company_id,title,description,location,minimum_cgpa,minimum_tenth_percentage,minimum_twelfth_percentage,maximum_active_backlogs,status)
SELECT company_id,'Graduate Software Engineer','Demonstration placement opening.','India',7.50,75,75,0,'open'
FROM companies WHERE company_name='CampusConnect Demo Systems'
AND NOT EXISTS (SELECT 1 FROM jobs j WHERE j.company_id=companies.company_id AND j.title='Graduate Software Engineer');
INSERT IGNORE INTO job_required_skills(job_id,skill_name)
SELECT job_id,'Python' FROM jobs WHERE title='Graduate Software Engineer';

INSERT IGNORE INTO enrollments(student_id,course_id,semester_id)
SELECT s.student_id,c.course_id,se.semester_id FROM students s JOIN courses c ON c.course_code='DEMO-DBMS'
JOIN semesters se ON se.semester_number=1 AND se.academic_year='2026-2027' WHERE s.roll_no='DEMO-CC-001';
