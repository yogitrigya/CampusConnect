
-- =============================================
-- CAMPUSCONNECT - STORED FUNCTIONS
-- =============================================

USE campusconnect;


-- =============================================
-- 1. CREATE FUNCTION
-- COUNT STUDENTS BY DEPARTMENT
-- =============================================

DROP FUNCTION IF EXISTS GetDepartmentStudentCount;

DELIMITER //

CREATE FUNCTION GetDepartmentStudentCount(
    dept_id INT
)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE total INT;

    SELECT COUNT(*)
    INTO total
    FROM students
    WHERE department_id = dept_id;

    RETURN total;
END //

DELIMITER ;


-- =============================================
-- 2. CALL THE FUNCTION
-- =============================================

SELECT GetDepartmentStudentCount(1)
AS total_students;


-- =============================================
-- 3. VERIFY FUNCTION
-- =============================================

SHOW FUNCTION STATUS
WHERE Db = 'campusconnect';
