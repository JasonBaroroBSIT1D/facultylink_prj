-- KRA I Criterion A operational validation settings (admin-editable OCR confidence thresholds).
-- Apply to facultylink_db only after backup + explicit approval.

BEGIN;

CREATE TABLE IF NOT EXISTS kra_criterion_operational_settings (
    criterion_id BIGINT PRIMARY KEY REFERENCES kra_criteria (criterion_id) ON DELETE CASCADE,
    confidence_thresholds JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT REFERENCES users (user_id)
);

COMMIT;
