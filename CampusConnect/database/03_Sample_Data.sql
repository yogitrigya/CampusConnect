
USE campusconnect;
/*
INSERT INTO departments (department_name)
VALUES
('Computer Science Engineering'),
('Information Technology'),
('Electronics and Communication');


INSERT INTO users (email, password_hash, role)
VALUES
('student1@college.edu', 'demo_hash_1', 'student'),
('student2@college.edu', 'demo_hash_2', 'student'),
('faculty1@college.edu', 'demo_hash_3', 'faculty'),
('admin@college.edu', 'demo_hash_4', 'admin');


INSERT INTO students
(user_id, roll_no, name, department_id, admission_year)
VALUES
(1, '2501730045', 'Student One', 1, 2025),
(2, '2501730046', 'Student Two', 1, 2025);


INSERT INTO faculty
(user_id, department_id, designation)
VALUES
(3, 1, 'Assistant Professor');


INSERT INTO semesters (semester_number, academic_year)
VALUES
(3, '2026-2027'),
(4, '2026-2027');

INSERT INTO courses
(course_code, course_name, credits, department_id)
VALUES
('CS301', 'Database Management Systems', 4, 1),
('CS302', 'Data Structures', 4, 1),
('CS303', 'Operating Systems', 3, 1);

INSERT INTO enrollments
(student_id, course_id, semester_id)
VALUES
(1, 1, 1),
(1, 2, 1),
(2, 1, 1),
(2, 3, 1); */

SELECT * FROM departments;
SELECT * FROM students;
SELECT * FROM faculty;
SELECT * FROM courses;
SELECT * FROM enrollments;

