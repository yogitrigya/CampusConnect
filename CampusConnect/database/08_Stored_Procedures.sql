
-- =============================================
-- CAMPUSCONNECT - STORED PROCEDURES
-- =============================================

USE campusconnect;


-- =============================================
-- 1. CREATE PROCEDURE
-- GET STUDENTS BY DEPARTMENT
-- =============================================

DROP PROCEDURE IF EXISTS GetStudentsByDepartment;

DELIMITER //

CREATE PROCEDURE GetStudentsByDepartment(
    IN dept_id INT
)
BEGIN
    SELECT
        s.student_id,
        s.roll_no,
        s.name AS student_name,
        d.department_name
    FROM students s
    INNER JOIN departments d
        ON s.department_id = d.department_id
    WHERE s.department_id = dept_id;
END //

DELIMITER ;


-- =============================================
-- 2. CALL THE PROCEDURE
-- =============================================

CALL GetStudentsByDepartment(1);


-- =============================================
-- 3. VERIFY PROCEDURE
-- =============================================

SHOW PROCEDURE STATUS
WHERE Db = 'campusconnect';




-- =============================================
-- 4. PROCEDURE WITH OUT PARAMETER
-- COUNT STUDENTS BY DEPARTMENT
-- =============================================

DROP PROCEDURE IF EXISTS CountStudentsByDepartment;

DELIMITER //

CREATE PROCEDURE CountStudentsByDepartment(
    IN dept_id INT,
    OUT total_students INT
)
BEGIN
    SELECT COUNT(*)
    INTO total_students
    FROM students
    WHERE department_id = dept_id;
END //

DELIMITER ;


-- =============================================
-- 5. EXECUTE PROCEDURE
-- =============================================

CALL CountStudentsByDepartment(1, @total);

-- Display returned value

SELECT @total AS total_students;
