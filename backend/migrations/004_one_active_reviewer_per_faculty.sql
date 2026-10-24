-- One active reviewer per faculty (FacultyLink assignment policy).
-- Apply to facultylink_db only after backup + explicit approval.
-- Test DB: safe to apply (dedupes any duplicate actives, then adds partial unique index).

BEGIN;

-- Deactivate duplicate active rows per faculty, keeping the lowest assignment_id (stable tie-break).
WITH ranked AS (
    SELECT
        assignment_id,
        ROW_NUMBER() OVER (
            PARTITION BY faculty_id
            ORDER BY assignment_id ASC
        ) AS rn
    FROM reviewer_assignments
    WHERE is_active = TRUE
)
UPDATE reviewer_assignments AS ra
SET is_active = FALSE
FROM ranked AS r
WHERE ra.assignment_id = r.assignment_id
  AND r.rn > 1;

-- Explicit production correction (no-op if row already inactive):
-- Aime Jean Gumatay (77) stays with Jenny Baroro (147); drop Rissa (149) active link (assignment_id 13).
UPDATE reviewer_assignments
SET is_active = FALSE
WHERE assignment_id = 13
  AND faculty_id = 77
  AND reviewer_id = 149;

CREATE UNIQUE INDEX IF NOT EXISTS uq_reviewer_assignments_one_active_per_faculty
    ON reviewer_assignments (faculty_id)
    WHERE (is_active = TRUE);

COMMIT;
