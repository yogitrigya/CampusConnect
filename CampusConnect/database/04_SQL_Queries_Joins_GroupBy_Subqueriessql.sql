USE campusconnect;

/*
SELECT
    s.roll_no,
    s.name AS student_name,
    d.department_name
FROM students s
INNER JOIN departments d
ON s.department_id = d.department_id;
*/

/*
SELECT
    s.name AS student_name,
    s.roll_no,
    c.course_name,
    c.credits
FROM students s
INNER JOIN enrollments e
    ON s.student_id = e.student_id
INNER JOIN courses c
    ON e.course_id = c.course_id;
*/

-- GROUP BY and COUNT()

-- Count students enrolled in each course
/*
SELECT
    c.course_name,
    COUNT(e.student_id) AS total_students
FROM courses c
LEFT JOIN enrollments e
    ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name;


-- Find courses having more than one student

SELECT
    c.course_name,
    COUNT(e.student_id) AS total_students
FROM courses c
LEFT JOIN enrollments e
    ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name
HAVING COUNT(e.student_id) > 1;

*/


-- Find students enrolled in DBMS

SELECT name, roll_no
FROM students
WHERE student_id IN (
    SELECT student_id
    FROM enrollments
    WHERE course_id = (
        SELECT course_id
        FROM courses
        WHERE course_name = 'Database Management Systems'
    )
);




SELECT course_name
FROM courses
WHERE course_id IN (
    SELECT course_id
    FROM enrollments
    GROUP BY course_id
    HAVING COUNT(*) > (
        SELECT AVG(total)
        FROM (
            SELECT COUNT(*) AS total
            FROM enrollments
            GROUP BY course_id
        ) AS course_counts
    )
);


