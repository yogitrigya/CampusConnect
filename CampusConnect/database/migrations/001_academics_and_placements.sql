CREATE TABLE IF NOT EXISTS academic_profiles (
    student_id INT PRIMARY KEY,
    cgpa DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    tenth_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    twelfth_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    active_backlogs INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_academic_profiles_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT chk_profile_cgpa CHECK (cgpa BETWEEN 0 AND 10),
    CONSTRAINT chk_profile_tenth CHECK (tenth_percentage BETWEEN 0 AND 100),
    CONSTRAINT chk_profile_twelfth CHECK (twelfth_percentage BETWEEN 0 AND 100),
    CONSTRAINT chk_profile_backlogs CHECK (active_backlogs >= 0)
);

CREATE TABLE IF NOT EXISTS student_skills (
    student_id INT NOT NULL,
    skill_name VARCHAR(80) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, skill_name),
    CONSTRAINT fk_student_skills_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance_records (
    attendance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('present','absent','late','excused') NOT NULL,
    recorded_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_attendance_enrollment_date (enrollment_id, attendance_date),
    CONSTRAINT fk_attendance_enrollment FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT fk_attendance_recorder FOREIGN KEY (recorded_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS exam_results (
    result_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT NOT NULL,
    assessment_name VARCHAR(100) NOT NULL,
    score DECIMAL(7,2) NOT NULL,
    maximum_score DECIMAL(7,2) NOT NULL,
    recorded_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_exam_enrollment_assessment (enrollment_id, assessment_name),
    CONSTRAINT chk_exam_score CHECK (score >= 0 AND maximum_score > 0 AND score <= maximum_score),
    CONSTRAINT fk_exam_enrollment FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT fk_exam_recorder FOREIGN KEY (recorded_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(150) NOT NULL,
    website VARCHAR(255) NULL,
    industry VARCHAR(100) NULL,
    description TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_company_name (company_name)
);

CREATE TABLE IF NOT EXISTS recruiters (
    recruiter_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_recruiter_email (email),
    KEY idx_recruiters_company (company_id),
    CONSTRAINT fk_recruiter_company FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NULL,
    location VARCHAR(150) NULL,
    minimum_cgpa DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    minimum_tenth_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    minimum_twelfth_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    maximum_active_backlogs INT NOT NULL DEFAULT 0,
    application_deadline DATE NULL,
    status ENUM('draft','open','closed') NOT NULL DEFAULT 'open',
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_jobs_status_deadline (status, application_deadline),
    KEY idx_jobs_company (company_id),
    CONSTRAINT chk_job_cgpa CHECK (minimum_cgpa BETWEEN 0 AND 10),
    CONSTRAINT chk_job_tenth CHECK (minimum_tenth_percentage BETWEEN 0 AND 100),
    CONSTRAINT chk_job_twelfth CHECK (minimum_twelfth_percentage BETWEEN 0 AND 100),
    CONSTRAINT chk_job_backlogs CHECK (maximum_active_backlogs >= 0),
    CONSTRAINT fk_job_company FOREIGN KEY (company_id) REFERENCES companies(company_id),
    CONSTRAINT fk_job_creator FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS job_required_skills (
    job_id INT NOT NULL,
    skill_name VARCHAR(80) NOT NULL,
    PRIMARY KEY (job_id, skill_name),
    CONSTRAINT fk_required_skill_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS applications (
    application_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    student_id INT NOT NULL,
    status ENUM('applied','shortlisted','rejected','withdrawn','offered','hired') NOT NULL DEFAULT 'applied',
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_application_student_job (student_id, job_id),
    KEY idx_applications_status (status),
    KEY idx_applications_job (job_id),
    CONSTRAINT fk_application_job FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    CONSTRAINT fk_application_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS interviews (
    interview_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    application_id BIGINT NOT NULL,
    round_number INT NOT NULL,
    scheduled_at DATETIME NOT NULL,
    mode ENUM('online','in_person') NOT NULL DEFAULT 'online',
    location_or_link VARCHAR(500) NULL,
    status ENUM('scheduled','completed','cancelled','no_show') NOT NULL DEFAULT 'scheduled',
    notes TEXT NULL,
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_interview_round (application_id, round_number),
    CONSTRAINT chk_interview_round CHECK (round_number > 0),
    CONSTRAINT fk_interview_application FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE,
    CONSTRAINT fk_interview_creator FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS offers (
    offer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    application_id BIGINT NOT NULL,
    package_amount DECIMAL(12,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    offer_date DATE NULL,
    status ENUM('extended','accepted','declined','expired') NOT NULL DEFAULT 'extended',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_offer_application (application_id),
    CONSTRAINT chk_offer_amount CHECK (package_amount > 0),
    CONSTRAINT fk_offer_application FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE
);
