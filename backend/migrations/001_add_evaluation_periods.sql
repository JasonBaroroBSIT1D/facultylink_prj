-- Additive migration: evaluation schedule windows (no DROP / TRUNCATE).
BEGIN;

CREATE TABLE IF NOT EXISTS evaluation_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_code VARCHAR(40) UNIQUE,
    name VARCHAR(200) NOT NULL,
    academic_year VARCHAR(40) NOT NULL,
    semester VARCHAR(60) NOT NULL,
    opens_at TIMESTAMPTZ NOT NULL,
    closes_at TIMESTAMPTZ NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Manila',
    description TEXT,
    submission_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    review_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (closes_at > opens_at)
);

CREATE INDEX IF NOT EXISTS idx_evaluation_periods_window ON evaluation_periods (opens_at, closes_at);

COMMIT;
