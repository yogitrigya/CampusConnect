
-- =============================================
-- CAMPUSCONNECT - SQL TRIGGERS
-- =============================================

USE campusconnect;

/*
-- =============================================
-- 1. CREATE ENROLLMENT AUDIT TABLE
-- =============================================

CREATE TABLE IF NOT EXISTS enrollment_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT,
    student_id INT,
    course_id INT,
    action_type VARCHAR(20),
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================
-- 2. CREATE AFTER INSERT TRIGGER
-- =============================================

DROP TRIGGER IF EXISTS after_enrollment_insert;

DELIMITER //

CREATE TRIGGER after_enrollment_insert
AFTER INSERT ON enrollments
FOR EACH ROW
BEGIN
    INSERT INTO enrollment_audit (
        enrollment_id,
        student_id,
        course_id,
        action_type
    )
    VALUES (
        NEW.enrollment_id,
        NEW.student_id,
        NEW.course_id,
        'INSERT'
    );
END //

DELIMITER ;


-- =============================================
-- 3. TEST THE TRIGGER
-- Execute this INSERT only once
-- =============================================

INSERT INTO enrollments (
    student_id,
    course_id,
    semester_id
)
VALUES (
    1,
    3,
    1
);


-- =============================================
-- 4. DISPLAY AUDIT LOG
-- =============================================

SELECT * FROM enrollment_audit;


-- =============================================
-- 5. VERIFY TRIGGER
-- =============================================

SHOW TRIGGERS;

*/
/*

-- =============================================
-- 6. AFTER UPDATE TRIGGER
-- =============================================

DROP TRIGGER IF EXISTS after_enrollment_update;

DELIMITER //

CREATE TRIGGER after_enrollment_update
AFTER UPDATE ON enrollments
FOR EACH ROW
BEGIN
    INSERT INTO enrollment_audit (
        enrollment_id,
        student_id,
        course_id,
        action_type
    )
    VALUES (
        NEW.enrollment_id,
        NEW.student_id,
        NEW.course_id,
        'UPDATE'
    );
END //

DELIMITER ;


-- Test the UPDATE trigger

UPDATE enrollments
SET semester_id = 2
WHERE enrollment_id = 5;

-- Check audit records

SELECT * FROM enrollment_audit;



-- =============================================
-- 7. AFTER DELETE TRIGGER
-- =============================================

DROP TRIGGER IF EXISTS after_enrollment_delete;

DELIMITER //

CREATE TRIGGER after_enrollment_delete
AFTER DELETE ON enrollments
FOR EACH ROW
BEGIN
    INSERT INTO enrollment_audit (
        enrollment_id,
        student_id,
        course_id,
        action_type
    )
    VALUES (
        OLD.enrollment_id,
        OLD.student_id,
        OLD.course_id,
        'DELETE'
    );
END //

DELIMITER ;

-- Test the DELETE trigger

DELETE FROM enrollments
WHERE enrollment_id = 5;

-- Verify audit history

SELECT * FROM enrollment_audit;
*/

-- The data-changing trigger demonstrations above are intentionally commented
-- out. Run them manually against disposable records in a test database only.
