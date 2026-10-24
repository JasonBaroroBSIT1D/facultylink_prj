# KRA I Criterion A — Section 10 (Future Scoring Engine)

**Guideline:** DBM–CHED Joint Circular No. 01, series of 2026 (Secs. 5–10, pp. 3–6).  
**Status:** Configuration reference only — **no scoring engine implementation** in Phase 1.  
**Indicator keys:** FacultyLink internal codes `A.1` (SET), `A.2` (SEF); not official instrument numbering.

## Confirmed point structure (Secs. 5–10)

| Component | Weight / cap | Formula (per rating period inputs) |
|-----------|--------------|-------------------------------------|
| Criterion A — Teaching Effectiveness | **60 points** max | SET points + SEF points (≤ 60) |
| SET — Student Evaluation of Teachers | **60%** of Criterion A → **36** max | `(Overall SET Rating / 100) × 36` |
| SEF — Supervisor's Evaluation of Faculty | **40%** of Criterion A → **24** max | `(Overall SEF Rating / 100) × 24` |

Phase 2+ must read `overall_set_rating` / `overall_sef_rating` (0–100) from validated evidence or reviewer-confirmed values before applying `percentage_of_max` rules in PostgreSQL.

## Section 10 — engine responsibilities (transcribe from official PDF)

Implementers must copy **exact** text and conditions from **Section 10** of JC No. 01, s. 2026 into engine configuration. This document records **categories** only (no invented rules):

1. **Multi-semester averaging**  
   - How many semesters enter the average for SET and/or SEF within an academic year or evaluation cycle.  
   - Whether averages are unweighted or weighted.  
   - Minimum number of valid semester ratings required before a composite “overall” rating is computed.

2. **Special circumstances**  
   - Leave, absence, or incomplete teaching load during a semester.  
   - Newly hired faculty within the evaluation window.  
   - Program/department transfers mid-year.  
   - Any exclusion or proration the circular allows (document citation + condition per row).

3. **Outputs for Criterion A**  
   - Single **Overall SET Rating** and **Overall SEF Rating** (0–100) per faculty per evaluation cycle **after** Section 10 processing.  
   - Those values feed the stored scoring rules (`percentage_of_max`); do not apply formulas on raw single-semester scores unless Section 10 permits.

4. **Audit**  
   - Persist semester-level inputs, averaging method version, and Section 10 branch taken in `rule_snapshot` / contribution metadata when crediting (Phase 2+).

## PostgreSQL linkage

- `scoring_rules.rule_config` includes `section_10_engine_ref`: this file.  
- `effective_from` / `effective_to` on rules remain **NULL** until the circular’s effectivity clause is recorded separately.

## Not in scope (Phase 1)

Automatic approval, OCR extraction of ratings, reviewer override math, rank simulation, and live crediting.
