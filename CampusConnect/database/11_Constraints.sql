
-- =============================================
-- CAMPUSCONNECT - SQL CONSTRAINTS
-- =============================================

USE campusconnect;


-- 1. CREATE TABLE WITH CONSTRAINTS

CREATE TABLE IF NOT EXISTS constraint_demo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INT CHECK (age >= 18),
    city VARCHAR(50) DEFAULT 'Delhi'
);


-- 2. INSERT VALID DATA

INSERT IGNORE INTO constraint_demo (email, age)
VALUES ('student1@example.com', 20);

INSERT IGNORE INTO constraint_demo (email, age, city)
VALUES ('student2@example.com', 22, 'Mumbai');


-- 3. DISPLAY DATA

SELECT * FROM constraint_demo;


-- 4. TEST UNIQUE CONSTRAINT

-- Uncomment to test duplicate email error

/*
INSERT INTO constraint_demo (email, age)
VALUES ('student1@example.com', 21);
*/


-- 5. TEST CHECK CONSTRAINT

-- Uncomment to test age validation

/*
INSERT INTO constraint_demo (email, age)
VALUES ('student3@example.com', 15);
*/


-- 6. TEST NOT NULL CONSTRAINT

-- Uncomment to test NOT NULL

/*
INSERT INTO constraint_demo (email, age)
VALUES (NULL, 20);
*/


-- 7. DISPLAY TABLE STRUCTURE

DESCRIBE constraint_demo;


-- 8. DISPLAY ALL CONSTRAINTS

SELECT *
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'campusconnect'
AND TABLE_NAME = 'constraint_demo';
