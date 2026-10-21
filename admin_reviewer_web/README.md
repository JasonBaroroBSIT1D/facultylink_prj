# FacultyLink — Admin & Reviewer Web Portal

Static frontend aligned with Chapter III (HTML, CSS, vanilla JavaScript). No npm or build step required.

## Structure

```
admin_reviewer_web/
├── index.html          Landing page
├── login.html          Admin / Reviewer sign-in
├── admin/              Admin portal pages (dashboard, faculty, KRA config, …)
├── reviewer/           Reviewer portal pages (dashboard, document review, KRA assessment, …)
├── css/                Stylesheets
├── js/                 Scripts (mock auth, UI helpers)
├── assets/             Icons and static media
└── serve.py            Local static server
```

## Run locally

```bash
cd facultylink_prj/admin_reviewer_web
python serve.py
```

Or:

```bash
python -m http.server 8765
```

Open http://localhost:8765/

## Mock authentication

Demo accounts (UI testing only) — see `js/mockAuth.js`. Future integration: shared Flask backend in `../backend/`.
