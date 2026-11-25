USE campusconnect;

-- =====================================
-- 1. CREATE INDEX
-- =====================================

CREATE INDEX idx_students_admission_year
ON students(admission_year);


-- =====================================
-- 2. DISPLAY INDEXES
-- =====================================

SHOW INDEX FROM students;


-- =====================================
-- 3. CHECK QUERY EXECUTION PLAN
-- =====================================

EXPLAIN
SELECT *
FROM students
WHERE admission_year = 2025;

