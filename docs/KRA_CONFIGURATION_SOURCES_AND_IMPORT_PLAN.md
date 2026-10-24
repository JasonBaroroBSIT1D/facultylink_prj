# KRA Configuration — Data Sources & PostgreSQL Import Plan

**Status:** Report only — **no database inserts have been run.** Await explicit approval before importing.

## 1. Where the “missing” criteria and indicators came from

| Source | Role | In PostgreSQL today? |
|--------|------|----------------------|
| `admin_reviewer_web/js/kraStructure.js` | **Primary UI source** before API switch | **No** — never written to DB |
| `admin_reviewer_web/js/api/adminApi.js` (pre-change) | `getKraConfig()` returned `{ _mock: true, kras: buildAdminKras() }` | **No** |
| `admin_reviewer_web/js/admin/pages/kra-config.js` (Phase 4.5 commit) | Fallback: `cfg.kras.length ? cfg.kras : loadKras()` from `kraStructure.js` | **No** |
| `admin_reviewer_web/js/mock/adminMockData.js` | Same `buildAdminKras()` for mock dashboard | **No** |
| `lib/core/kra/kra_structure.dart` | **Structural only:** KRA titles + criterion letters (A–C / A–D) | **No** |
| `facultylink_complete_schema.sql` | Tables: `kra_configurations`, `kra_criteria`, `kra_indicators`, `scoring_rules` | **Schema only — no seed rows** |
| Official DBM–CHED guideline files in repo | **Not found** (no PDF/JSON/XLS guideline bundle in project) | N/A |

**Conclusion:** The previous admin KRA page showed **hardcoded frontend sample data** from `kraStructure.js`, tagged in UI as **“Sample configuration data”** with **mock / placeholder** notes. It was **not** loaded from PostgreSQL. After switching `getKraConfig()` to `GET /api/v1/admin/kra-configuration`, the UI correctly shows empty content because **`kra_*` tables have zero rows**.

## 2. Classification: verified vs placeholder

### Verified (project-wide structural convention — not point values)

These align across `kraStructure.js` `KRA_META` and `lib/core/kra/kra_structure.dart`:

| Code | Display title (project convention) | Criterion letters |
|------|-----------------------------------|-------------------|
| KRA I | Instruction | A, B, C |
| KRA II | Research and Innovation | A, B, C |
| KRA III | Extension or Community Services | A, B, C, D |
| KRA IV | Professional Development | A, B, C, D |

**Total:** 14 criterion *slots* (3+3+4+4). **No official maximum points or rank formulas** are stored in repo sources.

### Placeholder / illustrative only (`ADMIN_KRA_DETAILS` in `kraStructure.js`)

**Do not treat as official CHED/DBM data.** Examples:

| Location | Content | Notes in source |
|----------|---------|-----------------|
| KRA I — A | “Teaching Load & Quality”, SET/SEF indicators | Partial; KRA I B/C use samples or shells |
| KRA I — B | “Course Development” | Sample list |
| KRA II — A | “Research Output” | Only one criterion populated for KRA II |
| KRA III — A | “Community Extension” | Only one criterion populated |
| KRA IV — A | “Advanced Studies & Certifications” | Only one criterion populated |
| All other letters | `shellCriterion()` → “Criterion X”, “Indicators configured via backend” | Explicit shell |
| Scoring | `capNote` fields | “Mock placeholder — no official CHED points displayed” |

Reviewer tree (`buildReviewerKras()`) adds more **mock** SET/SEF detail under KRA I A only; remainder is shell indicators.

## 3. What is missing for a verified PostgreSQL configuration

To populate PostgreSQL without guessing:

1. **Authoritative guideline document** (DBM–CHED faculty evaluation instrument version your institution adopts), including:
   - Official criterion names and descriptions per KRA
   - Indicator codes, names, and definitions
   - Evidence requirements per indicator
   - Scoring rules, weights, caps, and contribution logic
2. **`guideline_version`** string (e.g. instrument revision date or memo number) for audit.
3. **Institutional approval** that the extracted rows match the adopted guideline.

**Not in repository:** any file that satisfies (1). Cannot invent indicator names or point values.

## 4. Proposed verified import structure (pending your data)

**Tier A — Safe to import after you approve wording** (structural shell only):

- 4 rows in `kra_configurations` (codes KRA I–IV, names from table above, `guideline_version` = TBD).
- 14 rows in `kra_criteria` (letters A–D per KRA, names like **“Criterion A (pending official label)”** OR official names once transcribed from guideline).
- **No** `kra_indicators` or `scoring_rules` until transcribed from official source.

**Tier B — Full configuration** (required for scoring engine + mobile parity):

- All indicators per criterion with `indicator_code`, `indicator_name`, `required_evidence`.
- `scoring_rules` with `rule_type` + `rule_config` JSONB matching backend scoring engine expectations.

See template: `backend/scripts/kra_seed_template.sql.example` (commented SQL — **do not run** until approved).

## 5. API and clients after import

- **Admin web:** `GET /api/v1/admin/kra-configuration` (existing) — UI already merges API data by `kra_code`.
- **Reviewer / faculty:** `GET /api/v1/kra-configuration` (existing).
- **Mobile:** Should consume the same API (or shared JSON export generated from DB) — `KraStructure` in Dart remains fallback for letters only until API is wired on mobile.

## 6. Recommended approval workflow

1. You provide or attach the official guideline extract (or approve Tier A structural seed only).
2. Review generated SQL / CSV in `backend/scripts/kra_seed_template.sql.example`.
3. Explicit approval to run import (one environment at a time).
4. Re-open KRA Configuration — criteria/indicators appear from PostgreSQL only.

## 7. UI behavior (current)

- **Empty DB:** Four KRA cards, structural criterion letter panels (no fabricated official titles), sections show “Not configured yet” where DB has no rows.
- **Partial/full DB:** Expandable panels filled from API only.
- **No** reintroduction of “Sample configuration data” or mock scoring values in admin KRA page.
