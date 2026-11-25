-- Create student details view
/*
CREATE VIEW student_details AS
SELECT
    s.student_id,
    s.roll_no,
    s.name AS student_name,
    d.department_name
FROM students s
INNER JOIN departments d
    ON s.department_id = d.department_id;
*/



USE campusconnect;

-- Create or update student details view

CREATE OR REPLACE VIEW student_details AS
SELECT
    s.student_id,
    s.roll_no,
    s.name AS student_name,
    d.department_name
FROM students s
INNER JOIN departments d
    ON s.department_id = d.department_id;

-- Display view data

SELECT * FROM student_details;
