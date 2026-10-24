-- For databases that applied an earlier 002 without indicator-scoped credit slots.
BEGIN;

ALTER TABLE kra_indicators
    ADD COLUMN IF NOT EXISTS credit_uniqueness VARCHAR(40) NOT NULL DEFAULT 'per_evidence_hash'
        CHECK (credit_uniqueness IN ('per_evidence_hash', 'one_active_credit_per_term'));

ALTER TABLE document_score_contributions
    ADD COLUMN IF NOT EXISTS credit_uniqueness_mode VARCHAR(40) NOT NULL DEFAULT 'per_evidence_hash'
        CHECK (credit_uniqueness_mode IN ('per_evidence_hash', 'one_active_credit_per_term'));

ALTER TABLE document_score_contributions
    ADD COLUMN IF NOT EXISTS credit_uniqueness_key VARCHAR(220);

DROP INDEX IF EXISTS uq_doc_score_active_credit_evidence;

CREATE UNIQUE INDEX IF NOT EXISTS uq_doc_score_active_credit_slot
    ON document_score_contributions (credit_uniqueness_key)
    WHERE credit_state = 'credited'
      AND credited_points > 0
      AND credit_uniqueness_key IS NOT NULL;

COMMIT;
