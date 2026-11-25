CREATE TABLE IF NOT EXISTS enrollment_audit (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT NULL,
    student_id INT NULL,
    course_id INT NULL,
    action_type VARCHAR(20) NOT NULL,
    action_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_enrollment_audit_time (action_time),
    KEY idx_enrollment_audit_enrollment (enrollment_id)
);
