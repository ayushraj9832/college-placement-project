# College Placement and Recruitment Management System

A complete, role-based campus placement portal built for an MCA DBMS project.
It uses **MySQL 8**, **Python Flask**, **mysql-connector-python**, **Jinja2**,
plain **HTML5 / CSS3 / JavaScript**, and **Chart.js** — no front-end framework,
no ORM, and exactly **nine relational tables**.

The system replaces spreadsheets and notice boards with one place where students
apply to verified jobs, recruiters run their hiring pipeline, and the placement
cell tracks every offer in real time.

---

## Table of Contents

1. [Highlights](#highlights)
2. [Roles and features](#roles-and-features)
3. [Technology stack](#technology-stack)
4. [Folder structure](#folder-structure)
5. [Setup guide](#setup-guide)
6. [Demo accounts](#demo-accounts)
7. [Database design](#database-design)
8. [Advanced SQL objects](#advanced-sql-objects)
9. [Application routes](#application-routes)
10. [Security practices](#security-practices)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)
13. [Documentation index](#documentation-index)
14. [Limitations and future scope](#limitations-and-future-scope)

---

## Highlights

- **Four dashboards** — Student, Recruiter, Placement Officer, Administrator —
  all driven by live SQL, no hard-coded numbers.
- **Nine exactly specified tables** with primary keys, foreign keys,
  `UNIQUE`, `CHECK`, `ENUM`, and `ON DELETE` rules.
- **Centralised placement cell** that approves companies, manages students and
  rounds, creates offers, and generates reports.
- **Live eligibility engine:** CGPA plus branch list (`FIND_IN_SET`) decides
  whether a student may apply.
- **Charts** for branch placement share, application funnel, package bands and
  status mix, with graceful offline fallback.
- **Search, filters, pagination-free compact tables, responsive layout** down to
  phone width.
- **Security basics:** PBKDF2 password hashes, parameterised SQL everywhere,
  server-side role checks on every protected route, POST-only mutations.
- **Realistic demo data:** 20 students, 5 companies, 10 jobs, 43 applications,
  24 rounds, 38 interviews, 10 offers, 3 placement-cell accounts, 5 reports.

---

## Roles and features

### Student

| Feature | Description |
|---|---|
| Register / login | Self-registration with hashed password, CGPA and branch captured. |
| Dashboard | Profile summary, application counts, status doughnut chart, latest offers. |
| Browse jobs | Only **open** jobs whose deadline has not passed; eligibility badge on each. |
| Filter | Search by title/company/location, filter by branch and "eligible only". |
| Apply | One application per job, blocked when ineligible, closed, or already placed. |
| Applications | Track status timeline and withdraw an active application. |
| Interviews | See scheduled rounds with date, time, interviewer and marks. |
| Offers | View all offers, accept or decline. |
| Profile | Update phone, address and CGPA (branch is locked after registration). |
| Companies | Browse approved company profiles. |

### Recruiter (Company)

| Feature | Description |
|---|---|
| Register / login | Company account starts as **Pending** until the placement cell approves it. |
| Dashboard | Open jobs, application funnel, upcoming interviews, offers released. |
| Job management | Create, edit and delete openings with branch and CGPA eligibility. |
| Applicants | Per-job applicant list with CGPA, branch and status controls. |
| Shortlist / reject | Move an application through the defined status values. |
| Rounds | Define aptitude / technical / HR / coding rounds per job. |
| Interviews | Schedule an interview for an applicant in a round and record marks/result. |
| Offers | Release an offer; it becomes a placement record and the application becomes Selected. |
| Placements | Track acceptance, joining and decline for every offer. |
| Profile | Maintain company and HR contact details. |

### Placement Officer

| Feature | Description |
|---|---|
| Dashboard | College-wide stats, branch chart, status mix, pending approvals, top recruiters. |
| Students | Search/filter, inspect full record, edit academic data, delete with cascade warning. |
| Companies | Approve or reject recruiter accounts, inspect jobs and offers per company. |
| Eligibility | For any job, list every eligible student and whether they applied. |
| Applications | Audit every application across the college with filters. |
| Rounds | View all rounds and add a missing round on a recruiter's behalf. |
| Interviews | Inspect upcoming, past or all interviews. |
| Placements | Create an offer directly and delete erroneous records (reverts the application). |
| Reports | Generate and reopen reports; print-friendly detail pages. |

### Administrator

| Feature | Description |
|---|---|
| Dashboard | Whole-college placement rate, package distribution, branch performance. |
| Approvals | Approve or reject companies (shared with the officer workflow). |
| Officers | Create Officer/Admin accounts and activate or deactivate them. |
| Reports | Access the same report centre through the officer routes. |

> Administrators are stored in `Placement_Officer` with
> `Account_Role = 'Admin'`. This keeps the schema at exactly nine tables while
> still giving the administrator a separate login, dashboard and user management.

---

## Technology stack

| Layer | Choice | Version note |
|---|---|---|
| Database | MySQL Server | 8.0.16+ (CHECK constraints enforced) |
| DB tool | MySQL Workbench | 8.0 |
| Language | Python | 3.10+ |
| Web framework | Flask | 3.x |
| DB driver | mysql-connector-python | 8.x+ |
| Templating | Jinja2 | bundled with Flask |
| Styling | Hand-written CSS3 | `static/css/style.css` |
| Interactivity | Vanilla JavaScript | `static/js/main.js` |
| Charts | Chart.js | CDN, degrades gracefully offline |
| Icons | Bootstrap Icons | CDN |
| Passwords | Werkzeug PBKDF2-SHA256 | 600,000 iterations in demo data |
| Editor | VS Code | `.vscode/` settings included |

---

## Folder structure

```
CollegePlacementSystem/
│
├── app.py                     # All Flask routes, validation, helpers, reports
├── database.py                # Connection helpers + placement transactions
├── requirements.txt           # Python dependencies
├── run.bat                    # One-click Windows setup and run
├── start_database.bat         # Starts the bundled MySQL instance (port 3307)
├── stop_database.bat          # Stops the bundled MySQL instance
├── mysql-data/                # Local MySQL data files (created on first run)
├── .env.example               # Template for local configuration
├── .gitignore
│
├── database/
│   ├── schema.sql             # Database + 9 tables, keys, checks, indexes
│   ├── sample_data.sql        # 20 students, 5 companies, 10 jobs, 43 applications ...
│   └── advanced_objects.sql   # 5 views, 1 function, 2 procedures, 4 triggers
│
├── static/
│   ├── css/style.css          # Design system and responsive layout
│   └── js/main.js             # Sidebar, flash dismissal, filters, confirms
│
├── templates/
│   ├── base.html              # Public site shell
│   ├── dashboard_base.html    # Authenticated portal shell + sidebar
│   ├── _macros.html           # badge / stat / empty macros
│   ├── _flash.html
│   ├── index.html about.html companies.html jobs.html error.html
│   ├── auth/                  # 4 logins + 2 registrations
│   ├── student/               # 8 pages
│   ├── recruiter/             # 10 pages
│   ├── officer/               # 13 pages
│   └── admin/                 # 2 pages
│
├── tools/
│   ├── hash_password.py       # Generate a Werkzeug hash for SQL
│   └── check_db.py            # Verify connection, table counts, views, triggers
│
├── docs/
│   ├── PROJECT_REPORT.md      # Full academic report
│   ├── ER_DIAGRAM.md          # Mermaid ER diagram and relationship notes
│   ├── VIVA_QUERIES.md        # 40+ SQL queries with explanations
│   └── TESTING.md             # Test plan, cases and validation results
│
├── screenshots/               # Put your own screenshots here
└── .vscode/
    ├── launch.json            # F5 Flask debug configuration
    └── settings.json          # Interpreter and Jinja HTML association
```

---

## Setup guide

### Step 1 — Install prerequisites

1. **MySQL Server 8.0+** and **MySQL Workbench**.
2. **Python 3.10+** with *"Add python.exe to PATH"* ticked.
3. **VS Code** (recommended) with the *Python* and *Jinja* extensions.

Check that MySQL is running:

```powershell
Get-Service MySQL80
```

### Step 2 — Create the database

Open **MySQL Workbench** and connect to your local instance (`root`).

Run these files **in order** (open each file, then press
`Ctrl + Shift + Enter`):

1. `database/schema.sql` — creates `college_placement_db` and all 9 tables.
2. `database/sample_data.sql` — loads the demo records.
3. `database/advanced_objects.sql` — views, function, procedures, triggers.

Verify:

```sql
USE college_placement_db;
SHOW TABLES;          -- 9 tables
SELECT COUNT(*) FROM Student;   -- 20
```

> `schema.sql` starts with `DROP TABLE IF EXISTS` statements. Running it again
> erases existing data. Remove those lines once you enter real records.

### Step 3 — Configure the environment

Copy `.env.example` to `.env` and edit it:

```ini
SECRET_KEY=some-long-random-text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-mysql-root-password
DB_NAME=college_placement_db
```

> If your root account uses `caching_sha2_password` (the default on MySQL 8),
> the connector handles it automatically. If you prefer a dedicated user,
> uncomment the `CREATE USER` block at the end of `schema.sql`.

### Step 4 — Install Python packages

**Option A — one click (Windows)**

Double-click `run.bat`. It creates `.venv`, installs the requirements, copies
`.env` if missing, then starts the server.

**Option B — manual**

```powershell
cd C:\Users\<you>\Desktop\CollegePlacementSystem
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Option C — use the bundled local MySQL (this copy of the project)**

This folder already contains `mysql-data/` with the schema and demo data loaded,
running on `127.0.0.1:3307` with `root` and an empty password. `.env` is set up
for it, so no MySQL Workbench import is needed to demonstrate the site.

- `start_database.bat` starts it (safe to run repeatedly).
- `stop_database.bat` stops it.
- `run.bat` starts it automatically when `mysql-data\data` exists.

To point the app at your own MySQL 8 service instead, edit `.env`:
`DB_PORT=3306`, `DB_PASSWORD=<your root password>`, then run the three SQL
scripts in Workbench as described in Step 2.

### Step 5 — Run

```powershell
python app.py
```

Open **http://127.0.0.1:5000**.

For VS Code, press **F5** — `.vscode/launch.json` starts Flask with the
debugger attached.

### Step 6 — Verify the database link (optional)

```powershell
.\.venv\Scripts\python.exe tools\check_db.py
```

Expected: `[OK] MySQL 8.x ...` followed by the nine table counts, five views,
two procedures, one function and four triggers.

---

## Demo accounts

All demo accounts use the same password pattern. Passwords are stored only as
PBKDF2-SHA256 hashes.

| Role | Email / login | Password |
|---|---|---|
| Student | `aarav.sharma@college.edu` | `Student@123` |
| Student (2nd offer example) | `priya.menon@college.edu` | `Student@123` |
| Recruiter | `hr@technova.example.com` | `Recruiter@123` |
| Recruiter | `careers@databridge.example.com` | `Recruiter@123` |
| Placement Officer | `suresh.kulkarni@college.edu` | `Officer@123` |
| Administrator | `admin@college.edu` | `Admin@123` |

Every student email follows `firstname.lastname@college.edu`; every recruiter
email is listed in `sample_data.sql`. Use the `tools/hash_password.py` script if
you want to create accounts manually in SQL.

**Demonstration tip:** log in as `priya.menon@college.edu` to show multiple
offers (one declined, one accepted) in the student offers page.

---

## Database design

Exactly nine tables:

| # | Table | Purpose | Key relationships |
|---|---|---|---|
| 1 | `Student` | Student master + login | 1:N Application, 1:N Placement |
| 2 | `Company` | Company master + recruiter login | 1:N Job, 1:N Placement |
| 3 | `Placement_Officer` | Officers **and** administrators | 1:N Report |
| 4 | `Job` | Job openings | N:1 Company; 1:N Application, Round, Placement |
| 5 | `Application` | Bridge Student ↔ Job | N:1 Student, Job; 1:N Interview |
| 6 | `Recruitment_Round` | Rounds per job | N:1 Job; 1:N Interview |
| 7 | `Interview` | Candidate × round result | N:1 Application, Round |
| 8 | `Placement` | Final offers | N:1 Student, Job, Company |
| 9 | `Report` | Saved report metadata | N:1 Placement_Officer |

Key constraints:

- `UNIQUE (Student_ID, Job_ID)` on `Application` — no duplicate applications.
- `UNIQUE (Student_ID, Job_ID)` on `Placement` — no duplicate offer for a job,
  while still allowing offers from different companies.
- `UNIQUE (Application_ID, Round_ID)` on `Interview`.
- `CHECK` constraints on CGPA, salary, package, marks and dates.
- `ON DELETE CASCADE` from `Student`/`Job` down to applications, interviews and
  placements; `ON DELETE RESTRICT` protects `Job`/`Company` referenced by an
  offer and officer-referenced reports.

Full column-by-column documentation and the Mermaid ER diagram are in
[`docs/ER_DIAGRAM.md`](docs/ER_DIAGRAM.md). The academic write-up is in
[`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md).

---

## Advanced SQL objects

`database/advanced_objects.sql` creates:

**Views**

| View | Shows |
|---|---|
| `vw_job_details` | Job + company + application count + days to deadline |
| `vw_student_applications` | Student, job, company, status in one row |
| `vw_branch_placement_stats` | Students, placed count, placement %, average package per branch |
| `vw_company_selection_stats` | Jobs, applications, selections, average package per company |
| `vw_unplaced_students` | Students with no accepted/joined offer |

**Function**

- `fn_placement_percentage()` — returns the college placement rate as
  `DECIMAL(5,2)`, counting only `Offer Accepted` / `Joined`.

**Procedures**

- `sp_eligible_students(IN p_job_id INT)` — eligible students for a job using
  `FIND_IN_SET` and CGPA, with an `applied` flag.
- `sp_company_selection_summary()` — per-company application/selection funnel.

**Triggers**

| Trigger | Event | Purpose |
|---|---|---|
| `trg_placement_company_check` | BEFORE INSERT on Placement | Rejects a Company_ID that differs from the job's owner. |
| `trg_placement_company_check_update` | BEFORE UPDATE on Placement | Same check on updates. |
| `trg_application_deadline_check` | BEFORE INSERT on Application | Blocks applications after the job deadline. |
| `trg_placement_select_application` | AFTER INSERT on Placement | Forces the matching application to `Selected`. |

The app also demonstrates **transactions** in `database.py`:

- `create_placement()` inserts the offer and marks the application Selected.
- `delete_placement()` deletes the offer and reverts the application to
  Shortlisted, both or neither.

---

## Application routes

62 routes in total. The most important ones:

| Area | Method & path | Endpoint |
|---|---|---|
| Public | GET `/` | `index` |
| Public | GET `/about`, `/companies`, `/jobs` | `about`, `public_companies`, `public_jobs` |
| Auth | GET/POST `/student/login`, `/student/register` | `student_login`, `student_register` |
| Auth | GET/POST `/recruiter/login`, `/recruiter/register` | `recruiter_login`, `recruiter_register` |
| Auth | GET/POST `/officer/login`, `/admin/login` | `officer_login`, `admin_login` |
| Student | GET `/student/dashboard` | `student_dashboard` |
| Student | GET `/student/jobs`, `/student/jobs/<id>` | `student_jobs`, `student_job_detail` |
| Student | POST `/student/apply/<job_id>` | `student_apply` |
| Student | GET `/student/applications`, `/student/interviews`, `/student/placements` | `student_*` |
| Student | POST `/student/applications/<id>/withdraw` | `student_application_withdraw` |
| Student | POST `/student/placements/<id>/status` | `student_placement_status` |
| Recruiter | GET `/recruiter/dashboard` | `recruiter_dashboard` |
| Recruiter | GET/POST `/recruiter/jobs/new`, `/recruiter/jobs/<id>/edit` | `recruiter_job_new`, `recruiter_job_edit` |
| Recruiter | GET `/recruiter/jobs/<id>/applicants` | `recruiter_applicants` |
| Recruiter | POST `/recruiter/applications/<id>/status` | `recruiter_application_status` |
| Recruiter | GET/POST `/recruiter/applications/<id>/interview` | `recruiter_interview_new` |
| Recruiter | GET/POST `/recruiter/applications/<id>/offer` | `recruiter_offer_new` |
| Officer | GET `/officer/dashboard` | `officer_dashboard` |
| Officer | GET/POST `/officer/students`, `/officer/students/<id>/edit` | `officer_students`, `officer_student_edit` |
| Officer | GET `/officer/companies`, `/officer/companies/<id>` | `officer_companies`, `officer_company_detail` |
| Officer | GET/POST `/officer/placements` | `officer_placements` |
| Officer | GET/POST `/officer/reports`, GET `/officer/reports/<id>` | `officer_reports`, `officer_report_detail` |
| Admin | GET `/admin/dashboard`, `/admin/officers` | `admin_dashboard`, `admin_officers` |
| Admin | POST `/admin/officers/add`, `/admin/officers/<id>/toggle` | `admin_officer_add`, `admin_officer_toggle` |

Every mutating route is POST-only and decorated with `@roles_required(...)`.

---

## Security practices

- **Password hashing:** `werkzeug.security.generate_password_hash` /
  `check_password_hash`. Demo data ships PBKDF2-SHA256 hashes (600,000
  iterations). Plain passwords never enter the database.
- **SQL injection:** every query uses `%s` placeholders and a parameter tuple.
  Dynamic `IN (...)` lists are built from generated placeholders, not strings.
- **Role-based access:** `roles_required` compares `session["role"]` on the
  server; hiding a link is never the only defence.
- **Ownership checks:** a recruiter can only touch jobs/applications belonging
  to their own `Company_ID`; a student can only withdraw their own application.
- **Session:** signed Flask cookie session with a configurable `SECRET_KEY`.
- **Input validation:** numeric bounds, date order, enum membership and branch
  token validation are enforced server-side as well as in HTML.
- **Transactions:** offer creation/deletion use explicit transactions with
  rollback on failure.
- **Audit trail:** `Report` rows store who generated a report; officer accounts
  are deactivated rather than deleted so history stays valid.

---

## Testing

Static and dynamic validation performed on the final build:

- The three SQL scripts load cleanly into MySQL 8.0.46: 9 tables, exact
  sample counts, 5 views, 1 function, 2 procedures and 4 triggers.
- 49 Jinja templates compile in the real Flask environment and every
  `url_for` endpoint resolves.
- 62 routes registered; all `render_template` targets exist.
- A 62-check end-to-end route sweep passed against the live database,
  including apply/withdraw, offer accept, job creation, placement
  create/delete with status revert, report generation and role checks.
- All four demo password hashes verify against their documented passwords.
- 403/404/logout flows and role redirects checked with Flask's test client.
- SQL scripts also parse as valid MySQL with a generic parser (22 schema
  statements, 28 sample-data statements).

The full test case table is in [`docs/TESTING.md`](docs/TESTING.md).

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `1045 Access denied for user 'root'@'localhost'` | Wrong `.env` password | Re-enter the MySQL root password; test with `mysql -u root -p`. |
| `Can't connect to MySQL server on 'localhost'` | Service stopped | `Start-Service MySQL80` (admin PowerShell). |
| `Unknown database 'college_placement_db'` | Schema not run | Execute `database/schema.sql` in Workbench. |
| `Table 'college_placement_db.student' doesn't exist` | Wrong database selected or schema missing | Run `USE college_placement_db; SHOW TABLES;`. |
| Login fails for a demo account | Sample data not loaded | Run `database/sample_data.sql`, then check `SELECT COUNT(*) FROM Student;`. |
| Charts do not render | No internet (Chart.js CDN) | Charts are hidden gracefully; connect to the internet to see them. |
| `ModuleNotFoundError: flask` | Dependencies not installed | Activate `.venv` and `pip install -r requirements.txt`. |
| `UnicodeDecodeError` on Windows | Console encoding | Files are UTF-8; use Windows Terminal or PowerShell 7. |
| `RuntimeError: Working outside of request context` | Calling a DB helper at import time | All helpers belong inside route functions. |

MySQL root password reset (only if you truly need it):

```powershell
Stop-Service MySQL80
mysqld --skip-grant-tables
# in another admin terminal:
mysql -u root
ALTER USER 'root'@'localhost' IDENTIFIED BY 'NewPassword@123';
FLUSH PRIVILEGES;
# then restart the service
```

---

## Documentation index

| File | Contents |
|---|---|
| [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) | Abstract, SRS, ER model, table structures, normalization, implementation, testing, conclusion |
| [`docs/ER_DIAGRAM.md`](docs/ER_DIAGRAM.md) | Mermaid ER diagram, relationship cardinalities, constraint list |
| [`docs/VIVA_QUERIES.md`](docs/VIVA_QUERIES.md) | 40+ SQL queries for the viva, from basic SELECT to triggers and transactions |
| [`docs/TESTING.md`](docs/TESTING.md) | Test strategy, 40+ manual cases, validation commands, results |

---

## Limitations and future scope

**Known limitations**

- No CSRF tokens on forms (session cookie uses `SameSite=Lax`; add Flask-WTF
  CSRF for production).
- No email/SMS notifications; status changes are visible only in the portal.
- No file uploads (resumes) — the nine-table requirement excludes a documents
  table.
- Chart.js and Bootstrap Icons load from CDNs; offline use hides charts but the
  site remains functional.
- Development server only; use Gunicorn/Waitress behind a reverse proxy for real
  deployment.

**Future scope**

- Resume uploads and verification workflow.
- Email notifications on shortlist/offer/interview.
- Resume parsing and automated eligibility screening.
- Excel/PDF exports for reports (currently print-friendly HTML).
- Interview scheduling calendar with conflict detection.
- Alumni placement history and multi-year analytics.
- REST API for a mobile app.
- CSRF protection, rate limiting and password-reset flow.

---

*Built as a single-semester MCA DBMS project. All data in `sample_data.sql` is
fictional.*
