-- Phase 1: evaluation-period linkage + score contribution ledger (additive only).
-- Credit uniqueness is indicator-configurable (see kra_indicators.credit_uniqueness).

BEGIN;

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS period_id BIGINT REFERENCES evaluation_periods (period_id);

CREATE INDEX IF NOT EXISTS idx_documents_period_id ON documents (period_id);

COMMENT ON COLUMN documents.period_id IS
    'Evaluation period active when the faculty submitted this document.';

-- per_evidence_hash (default): multiple distinct files may each credit for the same indicator/term.
-- one_active_credit_per_term: at most one credited row per faculty/indicator/AY/semester (e.g. SET/SEF).
ALTER TABLE kra_indicators
    ADD COLUMN IF NOT EXISTS credit_uniqueness VARCHAR(40) NOT NULL DEFAULT 'per_evidence_hash'
        CHECK (credit_uniqueness IN ('per_evidence_hash', 'one_active_credit_per_term'));

COMMENT ON COLUMN kra_indicators.credit_uniqueness IS
    'Controls how document_score_contributions.credit_uniqueness_key is built at credit time.';

CREATE TABLE IF NOT EXISTS document_score_contributions (
    contribution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents (document_id) ON DELETE CASCADE,
    faculty_id BIGINT NOT NULL REFERENCES faculty_profiles (faculty_id),
    kra_id BIGINT REFERENCES kra_configurations (kra_id),
    indicator_id BIGINT REFERENCES kra_indicators (indicator_id),
    period_id BIGINT REFERENCES evaluation_periods (period_id),
    academic_year VARCHAR(40) NOT NULL,
    semester VARCHAR(60) NOT NULL,
    evidence_sha256 CHAR(64),
    credit_uniqueness_mode VARCHAR(40) NOT NULL DEFAULT 'per_evidence_hash'
        CHECK (credit_uniqueness_mode IN ('per_evidence_hash', 'one_active_credit_per_term')),
    credit_uniqueness_key VARCHAR(220),
    guideline_version VARCHAR(100),
    rule_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    system_calculated_points NUMERIC(12, 4) NOT NULL DEFAULT 0
        CHECK (system_calculated_points >= 0),
    provisional_points NUMERIC(12, 4) NOT NULL DEFAULT 0
        CHECK (provisional_points >= 0),
    reviewer_assigned_points NUMERIC(12, 4)
        CHECK (reviewer_assigned_points IS NULL OR reviewer_assigned_points >= 0),
    credited_points NUMERIC(12, 4) NOT NULL DEFAULT 0
        CHECK (credited_points >= 0),
    credit_state VARCHAR(20) NOT NULL DEFAULT 'none'
        CHECK (credit_state IN ('none', 'credited', 'revoked')),
    system_decision VARCHAR(40),
    version_no INTEGER NOT NULL DEFAULT 1 CHECK (version_no >= 1),
    supersedes_contribution_id BIGINT REFERENCES document_score_contributions (contribution_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    credited_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revoke_reason TEXT,
    reviewer_id BIGINT REFERENCES users (user_id),
    reviewer_reason TEXT
);

COMMENT ON COLUMN document_score_contributions.credit_uniqueness_key IS
    'Stable slot id for active-credit uniqueness; prior versions remain as revoked rows.';

CREATE INDEX IF NOT EXISTS idx_doc_score_contrib_document
    ON document_score_contributions (document_id);

CREATE INDEX IF NOT EXISTS idx_doc_score_contrib_faculty_period
    ON document_score_contributions (faculty_id, academic_year, semester);

-- Enforces indicator-specific rules via credit_uniqueness_key (Phase 2+ sets key when crediting).
CREATE UNIQUE INDEX IF NOT EXISTS uq_doc_score_active_credit_slot
    ON document_score_contributions (credit_uniqueness_key)
    WHERE credit_state = 'credited'
      AND credited_points > 0
      AND credit_uniqueness_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_faculty_sha256_active
    ON documents (faculty_id, sha256_hash)
    WHERE sha256_hash IS NOT NULL
      AND status NOT IN ('rejected', 'upload_failed');

COMMIT;
