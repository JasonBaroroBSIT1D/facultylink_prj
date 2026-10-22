# FacultyLink evaluation periods — frontend implementation

FacultyLink supports faculty self-assessment and advisory rank simulation. Evaluation-period settings do not confer an official academic rank or replace official reclassification.

## Interface

- The existing Admin Evaluation Schedule page now contains compact summary cards, a featured period, a filtered period register, and native create/edit/details/close dialogs. The meeting calendar has been replaced.
- Creation and editing require a name, academic year, semester, opening date/time and closing date/time. Description is optional. Invalid or equal/reversed date ranges and accidental duplicates are rejected inline. Overlapping windows require explicit acknowledgement. Early closing requires confirmation.
- Admin can enable or pause faculty submissions and reviewer activities independently within a period. Both are disabled outside its open window.
- The existing Reviewer Evaluation Schedule page displays the same browser-local periods, upcoming windows, and period-linked sample assignments. It has no period management controls. Assigned assessment links and document decision actions respect opening, closing, and review-enabled rules. Documents remain viewable as read-only outside an allowed review window.
- A shared mobile period card appears on the Faculty Dashboard, Upload Document, and KRA Assessment screens. It shows both dates, academic term, status, countdown, selection of available periods, and submission availability. Dashboard submission actions only appear when allowed; upload submission also checks the rule directly and during the simulated workflow.
- Web layouts use responsive cards, a scrollable compact register, responsive forms, accessible labels, native dialog focus behavior, and reduced-motion support. Existing FacultyLink colors and button styles are retained.

## Shared data and time rules

The canonical seed is `assets/data/evaluation-periods.json`, relative to this directory. Flutter bundles this **same file**, registered in the root `pubspec.yaml`. There are no separate hardcoded schedules for the three frontends.

Each period includes `id`, `name`, `academicYear`, `semester`, `opensAt`, `closesAt`, `description`, `submissionEnabled`, and `reviewEnabled`. Status is computed, never stored. Timestamps use ISO 8601 with an explicit `+08:00` offset. Display formatting always uses Asia/Manila, regardless of the computer or device timezone.

The window is **opening inclusive, closing exclusive**: Upcoming before opening, Open at opening until just before closing, and Closed at the closing instant. Early close replaces the closing instant with the current Manila time. Status and countdown displays refresh periodically and at boundaries; mobile also refreshes on app resume. Submission and review actions recheck access at use time.

If multiple periods are open, the featured default is the one closing first. Otherwise it is the next upcoming period, then the most recently closed period. Reviewer/mobile period selectors allow another period to be viewed explicitly. Sample reviewer assignments are linked by period ID and remain distinct from the period configuration.

## Frontend-only synchronization limits

- Web edits use `facultylink_evaluation_periods_v1` in localStorage. Admin and Reviewer tabs at the **same origin in the same browser profile** share edits, including live storage-event refresh. Other browsers, profiles, hosts, ports, and devices do not share this state.
- Native Faculty Mobile reads the bundled seed and shares its selection/state among its screens. It does **not** receive browser-local Admin edits. Rebuilding with a changed seed updates the mobile sample data. Actual cross-device synchronization requires the future shared API, which was not modified in this phase.
- If browser storage is blocked, edits remain in memory on the current page and the UI explains that limitation. The old meeting-schedule storage key is ignored; meeting records are not misinterpreted as evaluation periods.
- Access controls are frontend demonstration rules, not server-side authorization. OCR, uploads, review decisions, and official evaluations remain outside this implementation.
- Serve the web directory over HTTP using the existing `serve.py` or a static server so the shared JSON can be loaded. No new web build step or framework is required.

## Files changed in this phase

Paths below are relative to the repository root. Existing Phase 1 edits are preserved.

| Area | Files |
| --- | --- |
| Existing web pages | `admin_reviewer_web/admin/evaluation-schedule.html`, `admin_reviewer_web/reviewer/evaluation-schedule.html`, `admin_reviewer_web/reviewer/kra-assessment.html`, `admin_reviewer_web/reviewer/document-detail.html` |
| Shared web state and presentation | `admin_reviewer_web/assets/data/evaluation-periods.json` (new), `admin_reviewer_web/js/mock/evaluationScheduleStore.js`, `admin_reviewer_web/js/evaluation-period-ui.js` (new), `admin_reviewer_web/css/evaluation-periods.css` (new) |
| Web API adapters and sample assignments | `admin_reviewer_web/js/api/adminApi.js`, `admin_reviewer_web/js/api/reviewerApi.js`, `admin_reviewer_web/js/mock/reviewerMockData.js` |
| Web page logic | `admin_reviewer_web/js/admin/pages/evaluation-schedule.js`, `admin_reviewer_web/js/reviewer/pages/evaluation-schedule.js`, `admin_reviewer_web/js/reviewer/pages/kra-assessment.js`, `admin_reviewer_web/js/reviewer/pages/document-detail.js` |
| Mobile model and shared state | `lib/models/evaluation_period.dart` (new), `lib/services/evaluation_period_controller.dart` (new), `lib/services/api/faculty_api.dart`, `lib/widgets/fl_evaluation_period_card.dart` (new) |
| Existing mobile screens and assets | `lib/features/dashboard/faculty_dashboard_screen.dart`, `lib/features/documents/upload_document_screen.dart`, `lib/features/kra/kra_assessment_screen.dart`, `pubspec.yaml` |
| Verification and documentation | `admin_reviewer_web/tests/evaluation-periods.test.js` (new), `admin_reviewer_web/tests/frontend-regressions.test.js` (updated from Phase 1), `test/evaluation_period_test.dart` (new), `admin_reviewer_web/EVALUATION_PERIODS.md` (new) |

No new HTML pages, backend/database changes, or framework dependencies were added.

## Verification

From the repository root:

```text
node --test admin_reviewer_web/tests/*.test.js
flutter test --no-pub test/evaluation_period_test.dart test/widget_test.dart
flutter analyze --no-pub lib/models/evaluation_period.dart lib/services/evaluation_period_controller.dart lib/services/api/faculty_api.dart lib/widgets/fl_evaluation_period_card.dart lib/features/dashboard/faculty_dashboard_screen.dart lib/features/documents/upload_document_screen.dart lib/features/kra/kra_assessment_screen.dart test/evaluation_period_test.dart
git diff --check
```

The Node tests exercise state, page event handlers and generated markup using a lightweight test double, not a full browser DOM. They cover create/edit, inline validation, duplicate/overlap rules, status boundaries, early closing, cross-tab state, Reviewer permissions, invalid/direct navigation, and preserved Phase 1 document/faculty fixes. The same suite is run with `TZ=Asia/Manila`, `TZ=UTC`, and `TZ=America/Los_Angeles`.

Flutter tests cover shared-asset loading, date/status parity, mobile Upcoming/Open/Closed/paused/error/empty states, deadline transitions, submission gating, and 320px layouts at 1.3× text scale. The existing welcome-screen test is included.

Final results: 14 Node tests passed in each of the three timezones (42 executions); all 9 Flutter tests passed; analysis of the eight affected Dart source/test files reported no issues; `git diff --check` passed.

Browser visual inspection was unavailable because no browser was connected. Desktop responsive rules and generated web markup were inspected, but a real-browser visual/interaction pass remains a verification limitation.
