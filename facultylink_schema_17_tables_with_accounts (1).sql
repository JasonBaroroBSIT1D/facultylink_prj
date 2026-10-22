-- FacultyLink PostgreSQL schema — proposed 17-table design (includes reviewer feedback and 3 demo accounts)
-- Run only in a NEW, EMPTY database (suggested name: facultylink_db).
-- Includes 17 tables and 3 TEST accounts. This is a proposed starter schema; verify against the existing project/manuscript before production use.
-- PostgreSQL 18 compatible. Does not create/drop the database.
BEGIN;

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin','reviewer','faculty')),
    full_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE faculty_profiles (
    faculty_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(user_id),
    employee_number VARCHAR(50) NOT NULL UNIQUE,
    college VARCHAR(160),
    department VARCHAR(160),
    current_rank VARCHAR(120),
    employment_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reviewer_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id),
    faculty_id BIGINT NOT NULL REFERENCES faculty_profiles(faculty_id),
    assigned_by BIGINT REFERENCES users(user_id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (reviewer_id, faculty_id)
);

CREATE TABLE kra_configurations (
    kra_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kra_code VARCHAR(20) NOT NULL UNIQUE,
    kra_name VARCHAR(200) NOT NULL,
    description TEXT,
    guideline_version VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE kra_criteria (
    criterion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kra_id BIGINT NOT NULL REFERENCES kra_configurations(kra_id),
    criterion_code VARCHAR(30) NOT NULL,
    criterion_name VARCHAR(200) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE (kra_id, criterion_code)
);

CREATE TABLE kra_indicators (
    indicator_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    criterion_id BIGINT NOT NULL REFERENCES kra_criteria(criterion_id),
    indicator_code VARCHAR(30) NOT NULL,
    indicator_name VARCHAR(200) NOT NULL,
    required_evidence TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE (criterion_id, indicator_code)
);

CREATE TABLE scoring_rules (
    rule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    indicator_id BIGINT NOT NULL REFERENCES kra_indicators(indicator_id),
    rule_name VARCHAR(160) NOT NULL,
    rule_type VARCHAR(60) NOT NULL,
    rule_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    guideline_version VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE,
    effective_to DATE,
    CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from)
);

CREATE TABLE documents (
    document_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    faculty_id BIGINT NOT NULL REFERENCES faculty_profiles(faculty_id),
    criterion_id BIGINT NOT NULL REFERENCES kra_criteria(criterion_id),
    indicator_id BIGINT REFERENCES kra_indicators(indicator_id),
    title VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_key TEXT NOT NULL,
    mime_type VARCHAR(120),
    file_size_bytes BIGINT CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    sha256_hash CHAR(64),
    status VARCHAR(40) NOT NULL DEFAULT 'uploaded' CHECK (status IN
        ('uploaded','processing','system_approved','needs_verification','needs_revision','rejected','upload_failed')),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE document_extractions (
    extraction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(document_id),
    extracted_text TEXT,
    extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    ocr_confidence NUMERIC(5,2) CHECK (ocr_confidence BETWEEN 0 AND 100),
    extraction_status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (extraction_status IN ('pending','processing','completed','failed')),
    engine_version VARCHAR(80),
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE validation_results (
    validation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(document_id),
    extraction_id BIGINT REFERENCES document_extractions(extraction_id),
    result VARCHAR(40) NOT NULL CHECK (result IN ('passed','needs_verification','needs_revision','failed')),
    checks JSONB NOT NULL DEFAULT '{}'::jsonb,
    explanation TEXT,
    rule_version VARCHAR(100),
    validated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE evaluation_records (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    faculty_id BIGINT NOT NULL REFERENCES faculty_profiles(faculty_id),
    indicator_id BIGINT NOT NULL REFERENCES kra_indicators(indicator_id),
    document_id BIGINT NOT NULL REFERENCES documents(document_id),
    academic_year VARCHAR(20) NOT NULL,
    semester VARCHAR(30) NOT NULL,
    rating NUMERIC(8,4),
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','verified','rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (faculty_id, indicator_id, academic_year, semester)
);

CREATE TABLE review_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(document_id),
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id),
    decision VARCHAR(30) NOT NULL CHECK (decision IN ('approved','needs_revision','rejected','needs_verification')),
    remarks TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_feedback (
    feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(document_id),
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id),
    decision_id BIGINT REFERENCES review_decisions(decision_id),
    feedback_type VARCHAR(30) NOT NULL CHECK (
        feedback_type IN ('revision','rejection','clarification','general_comment')
    ),
    message TEXT NOT NULL CHECK (length(trim(message)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE kra_scores (
    score_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    faculty_id BIGINT NOT NULL REFERENCES faculty_profiles(faculty_id),
    kra_id BIGINT NOT NULL REFERENCES kra_configurations(kra_id),
    assessment_period VARCHAR(100) NOT NULL,
    eligible_points NUMERIC(12,4) NOT NULL DEFAULT 0 CHECK (eligible_points >= 0),
    calculation_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    guideline_version VARCHAR(100),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (faculty_id, kra_id, assessment_period)
);

CREATE TABLE rank_simulations (
    simulation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    faculty_id BIGINT NOT NULL REFERENCES faculty_profiles(faculty_id),
    assessment_period VARCHAR(100) NOT NULL,
    current_rank VARCHAR(120),
    simulated_rank VARCHAR(120),
    total_eligible_points NUMERIC(12,4) CHECK (total_eligible_points >= 0),
    simulation_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    guideline_version VARCHAR(100),
    simulated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_official BOOLEAN NOT NULL DEFAULT FALSE CHECK (is_official = FALSE)
);

CREATE TABLE notifications (
    notification_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(60),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    action VARCHAR(120) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_assignments_faculty ON reviewer_assignments(faculty_id);
CREATE INDEX idx_documents_faculty_status ON documents(faculty_id, status);
CREATE INDEX idx_documents_criterion ON documents(criterion_id);
CREATE INDEX idx_extractions_document ON document_extractions(document_id);
CREATE INDEX idx_validations_document ON validation_results(document_id);
CREATE INDEX idx_evaluations_faculty ON evaluation_records(faculty_id);
CREATE INDEX idx_reviews_document ON review_decisions(document_id);
CREATE INDEX idx_feedback_document_created ON review_feedback(document_id, created_at DESC);
CREATE INDEX idx_feedback_reviewer ON review_feedback(reviewer_id);
CREATE INDEX idx_rank_simulations_faculty ON rank_simulations(faculty_id);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);

-- DEVELOPMENT/TESTING ONLY: remove these seed accounts before production deployment.
-- Password hashes use Werkzeug-compatible pbkdf2:sha256:600000 format.
-- Real Flask login must use werkzeug.security.check_password_hash to verify them.
-- Temporary demo credentials: admin/demo-admin, reviewer/demo-reviewer, faculty/demo-faculty.
INSERT INTO users (email, password_hash, role, full_name)
VALUES
    ('admin@facultylink.edu', 'pbkdf2:sha256:600000$FNS2rezup35cTCyl$d97f26410e346026264ea826f9875b5eeba0d2d6dd3e753c78b82a17ff6e4f88', 'admin', 'System Administrator'),
    ('reviewer@facultylink.edu', 'pbkdf2:sha256:600000$xU1DOIBgz2ShRQ0z$6a24616177a785d666dd8078b38cce085518f1e516f4a645692807226eaba423', 'reviewer', 'Faculty Reviewer'),
    ('faculty@facultylink.edu', 'pbkdf2:sha256:600000$JhJfOrY200n1SQL8$4d78c448cde855e73371ffb3b5272fbf3b1a242d839f19675faa24d1ade99713', 'faculty', 'Demo Faculty');

-- One faculty profile for the seeded faculty user.
INSERT INTO faculty_profiles (user_id, employee_number, college, department, current_rank)
SELECT user_id, 'FAC-DEMO-001', 'For Testing', 'For Testing', NULL
FROM users WHERE email = 'faculty@facultylink.edu' AND role = 'faculty';

COMMIT;
