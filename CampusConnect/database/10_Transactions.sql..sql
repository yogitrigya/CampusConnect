
-- =============================================
-- CAMPUSCONNECT - SQL TRANSACTIONS
-- =============================================

USE campusconnect;


-- =============================================
-- 1. START TRANSACTION
-- =============================================

/*
-- Execute this entire demonstration manually against disposable test rows only.
START TRANSACTION;

UPDATE students
SET admission_year = 2024
WHERE student_id = 1;

SELECT * FROM students;


-- =============================================
-- 2. ROLLBACK
-- Undo the above update
-- =============================================

ROLLBACK;

SELECT * FROM students;


-- =============================================
-- 3. COMMIT
-- Permanently save changes
-- =============================================

START TRANSACTION;

UPDATE students
SET admission_year = 2025
WHERE student_id = 1;

COMMIT;

SELECT * FROM students;


-- =============================================
-- 4. SAVEPOINT
-- =============================================

START TRANSACTION;

UPDATE students
SET admission_year = 2024
WHERE student_id = 1;

SAVEPOINT sp1;

UPDATE students
SET admission_year = 2023
WHERE student_id = 2;

ROLLBACK TO sp1;

COMMIT;

SELECT * FROM students;
*/
