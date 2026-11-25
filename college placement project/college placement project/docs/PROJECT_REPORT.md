# College Placement and Recruitment Management System

### Project Report

**Course:** Master of Computer Applications (MCA)
**Subject:** Database Management Systems
**Academic year:** 2026–27
**Submitted by:** ____________________
**Roll number:** ____________________
**Guide:** ____________________

---

## Abstract

Campus placement is one of the most data-intensive activities in a college.
Student records, company profiles, job openings, eligibility rules, selection
rounds, interview results, offers and management reports all change constantly
and are usually scattered across spreadsheets, email threads and notice boards.
This project replaces that fragmented process with a single web application
backed by a normalised MySQL database.

The system is implemented with **Python Flask** and **MySQL 8** and provides
four role-specific portals: **Student**, **Recruiter**, **Placement Officer**
and **Administrator**. Students browse verified openings, are filtered by a
live eligibility rule (CGPA and branch), apply once per job, track their
selection status and respond to offers. Recruiters manage their company
profile, publish jobs, define recruitment rounds, shortlist applicants,
schedule interviews, record marks and release offers. The placement cell
approves companies, maintains student and round data, monitors every
application, records or removes offers, and generates saved reports. The
administrator sees whole-college analytics and manages placement-cell accounts.

The database contains exactly **nine tables** — `Student`, `Company`, `Job`,
`Application`, `Recruitment_Round`, `Interview`, `Placement`,
`Placement_Officer` and `Report` — with primary keys, foreign keys, unique
constraints, check constraints, indexes, five views, one stored function, two
stored procedures, four triggers and explicit transactions. Passwords are
stored as PBKDF2 hashes, every query is parameterised, and every protected
route is guarded by a server-side role check. The result is a compact but
realistic DBMS project that demonstrates the complete database lifecycle from
conceptual design to a working, responsive application.

---

## 1. Introduction

### 1.1 Background

A placement cell coordinates three groups with different needs:

- **Students** want to know which companies are visiting, whether they are
  eligible, where their application stands and whether they have an offer.
- **Recruiters** want a short, filtered applicant list and a simple way to
  schedule rounds and record outcomes.
- **The placement cell and administration** want accurate, real-time numbers
  for branch-wise placement percentage, company participation and pending
  approvals.

When these needs are handled through spreadsheets, the same fact is stored in
several files. A student's CGPA is updated in one sheet but not another; a
company is told it is approved although the master list still says pending; a
final report is assembled by copying numbers from three sources. The database
approach solves this by making each fact live in exactly one place and by
enforcing the rules at the database level.

### 1.2 Problem statement

Design and implement a database-backed web system that:

1. Stores students, companies, jobs, applications, rounds, interviews, offers,
   officers and reports in a well-structured relational schema.
2. Enforces eligibility, uniqueness, referential integrity and date/score
   validity.
3. Gives each stakeholder a focused interface rather than one overloaded admin
   screen.
4. Produces live analytics and saved reports without manual calculation.
5. Demonstrates advanced SQL: joins, subqueries, `EXISTS`, `UNION`, views,
   stored procedures, functions, triggers and transactions.

### 1.3 Objectives

- Model the placement domain in **nine tables** in third normal form.
- Implement role-based authentication and authorisation.
- Automate job eligibility from CGPA and branch.
- Track the complete funnel: application → shortlist → interview → offer →
  acceptance/joining.
- Provide live dashboards and printable reports.
- Apply security fundamentals: hashed passwords, parameterised SQL, ownership
  checks and POST-only mutations.

### 1.4 Scope

**Included:** student and recruiter self-registration, company approval, job
posting, eligibility filtering, applications, rounds, interviews with marks,
offers, placement tracking, officer data management, administrator account
management, reports and charts.

**Excluded (deliberately):** resume file uploads, email/SMS notifications,
online payment, external job-board integration, mobile apps and multi-college
tenancy. These would require extra tables or services beyond the nine-table
scope.

---

## 2. Existing system and limitations

A typical manual or spreadsheet-based process has these weaknesses:

| Limitation | Consequence |
|---|---|
| Data duplicated across files | Inconsistent CGPA, package and status values |
| No enforced eligibility | Ineligible students apply and are rejected manually |
| No unique application rule | Duplicate applications and duplicated effort |
| Status updated by email | Students do not know their real status |
| Reports assembled by hand | Slow, error-prone, quickly outdated |
| No audit trail | Cannot tell who approved a company or generated a report |
| Weak access control | Everyone with the file can see every student's data |

The proposed system addresses each limitation with a constraint, a transaction,
a role check or a view.

---

## 3. System analysis

### 3.1 Functional requirements

**FR-1 Authentication**

- FR-1.1 Students and recruiters can register; officers/admins are created by
  an administrator or seeded in SQL.
- FR-1.2 Login checks a hashed password and the account's active/approval
  state.
- FR-1.3 A session stores user id, role and display name.
- FR-1.4 Logout clears the session.

**FR-2 Student functions**

- FR-2.1 View and edit own profile.
- FR-2.2 Browse open jobs with search and filters.
- FR-2.3 See a live eligibility result per job.
- FR-2.4 Apply once per job; withdraw an active application.
- FR-2.5 Track applications, interviews and offers.
- FR-2.6 Accept or decline an offer.

**FR-3 Recruiter functions**

- FR-3.1 Maintain the company profile.
- FR-3.2 Create, edit and delete own job openings.
- FR-3.3 Define recruitment rounds per job.
- FR-3.4 View applicants and update their status.
- FR-3.5 Schedule interviews and record marks/results.
- FR-3.6 Release offers and update their status.

**FR-4 Placement officer functions**

- FR-4.1 Approve or reject companies.
- FR-4.2 Search, inspect, edit and delete student records.
- FR-4.3 Inspect companies, jobs and offers.
- FR-4.4 View all applications, rounds and interviews.
- FR-4.5 Create and delete placement records.
- FR-4.6 Generate and reopen reports.

**FR-5 Administrator functions**

- FR-5.1 View whole-college analytics.
- FR-5.2 Create officer/admin accounts.
- FR-5.3 Activate or deactivate accounts.
- FR-5.4 Access reports and company approvals.

**FR-6 Reports and analytics**

- FR-6.1 Placement summary, branch-wise, company-wise, unplaced-students and
  recruitment-summary reports.
- FR-6.2 Dashboard charts for branch placement, application status, package
  bands and recruiter funnel.

### 3.2 Non-functional requirements

| Category | Requirement |
|---|---|
| Usability | Responsive layout, clear labels, flash messages, confirmation dialogs |
| Performance | Dashboard queries under 100 ms with the demo dataset |
| Integrity | Foreign keys, checks and transactions preserve consistency |
| Security | Hashed passwords, parameterised SQL, role checks, ownership checks |
| Maintainability | Single `app.py`, shared macros, commented SQL, documented schema |
| Portability | Windows/Linux/macOS; only MySQL and Python required |
| Availability | Clear error pages when MySQL is down |

### 3.3 Feasibility study

- **Technical:** Flask and MySQL are free, well documented and run on a laptop.
- **Economic:** no licence cost; open-source stack only.
- **Operational:** the interface mirrors existing placement-cell tasks, so
  training effort is low.
- **Schedule:** the module breakdown fits a single semester.

---

## 4. System design

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│   HTML5 + CSS3 + vanilla JS + Chart.js (CDN)                │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (Jinja-rendered pages)
┌───────────────────────────▼─────────────────────────────────┐
│                    Flask application                        │
│  app.py                                                     │
│   ├── public routes        (/, /about, /jobs, /companies)   │
│   ├── auth routes          (4 logins, 2 registrations)      │
│   ├── student routes       (dashboard, jobs, applications…) │
│   ├── recruiter routes     (jobs, applicants, rounds…)      │
│   ├── officer routes       (students, companies, reports…)  │
│   ├── admin routes         (dashboard, officers)            │
│   └── helpers              (roles, eligibility, stats)      │
│  database.py                                                │
│   ├── query_all / query_one / execute                       │
│   └── create_placement / delete_placement (transactions)    │
└───────────────────────────┬─────────────────────────────────┘
                            │ mysql-connector-python, %s params
┌───────────────────────────▼─────────────────────────────────┐
│                     MySQL 8 database                        │
│  college_placement_db                                       │
│   9 tables • 10 FKs • 9 CHECKs • 9 UNIQUE keys • 2 indexes  │
│   5 views • 1 function • 2 procedures • 4 triggers          │
└─────────────────────────────────────────────────────────────┘
```

The application follows a **three-tier** structure: presentation (templates and
CSS), application logic (Flask routes and helpers), and data (MySQL). SQL is
written explicitly; no ORM hides the database concepts being assessed.

### 4.2 Module design

| Module | Files | Responsibility |
|---|---|---|
| Public site | `index`, `about`, `companies`, `jobs` | Marketing pages, live counts, open jobs |
| Authentication | `auth/*.html`, login routes | Register, hash, verify, session, approval checks |
| Student portal | `student/*.html` | Profile, jobs, applications, interviews, offers |
| Recruiter portal | `recruiter/*.html` | Company, jobs, rounds, applicants, interviews, offers |
| Officer portal | `officer/*.html` | Students, companies, applications, rounds, placements, reports |
| Admin portal | `admin/*.html` | College analytics, account management |
| Shared UI | `base.html`, `dashboard_base.html`, `_macros.html`, `style.css`, `main.js` | Layout, badges, empty states, sidebar, dialogs |
| Data access | `database.py` | Connections, parameterised queries, transactions |
| SQL assets | `database/*.sql` | Schema, demo data, advanced objects |

### 4.3 Entity–relationship model

The full Mermaid diagram is in [`ER_DIAGRAM.md`](ER_DIAGRAM.md). In text:

- A **Student** submits many **Applications**; each application belongs to one
  **Job**.
- A **Company** posts many **Jobs**; each job belongs to one company.
- A **Job** defines many **Recruitment_Rounds**.
- An **Application** attends many **Interviews**; each interview belongs to one
  round.
- A **Student** may receive many **Placements** (offers), but at most one per
  job.
- A **Placement** refers to a Student, a Job and the Company that owns the job.
- A **Placement_Officer** (officer or administrator) generates many
  **Reports**.

Cardinalities:

| Relationship | Cardinality | Implementation |
|---|---|---|
| Company–Job | 1:N | `Job.Company_ID` FK |
| Student–Application | 1:N | `Application.Student_ID` FK |
| Job–Application | 1:N | `Application.Job_ID` FK |
| Job–Recruitment_Round | 1:N | `Recruitment_Round.Job_ID` FK |
| Application–Interview | 1:N | `Interview.Application_ID` FK |
| Round–Interview | 1:N | `Interview.Round_ID` FK |
| Student–Placement | 1:N | `Placement.Student_ID` FK |
| Job–Placement | 1:N | `Placement.Job_ID` FK |
| Company–Placement | 1:N | `Placement.Company_ID` FK |
| Officer–Report | 1:N | `Report.Generated_By` FK |

The two many-to-many relationships — **Student ↔ Job** and
**Application ↔ Round** — are resolved by the bridge tables `Application` and
`Interview`.

### 4.4 Table structures

#### 4.4.1 `Student`

| Column | Type | Constraint |
|---|---|---|
| Student_ID | INT UNSIGNED AI | PK |
| Name | VARCHAR(100) | NOT NULL |
| Email | VARCHAR(120) | NOT NULL, UNIQUE |
| Phone | VARCHAR(15) | NOT NULL, UNIQUE |
| Password_Hash | VARCHAR(255) | NOT NULL |
| Date_of_Birth | DATE | NOT NULL |
| Gender | ENUM | Male/Female/Other |
| Branch | VARCHAR(50) | NOT NULL |
| Batch_Year | SMALLINT UNSIGNED | CHECK 2000–2100 |
| CGPA | DECIMAL(4,2) | CHECK 0–10 |
| Address | VARCHAR(255) | NULL |
| Created_At | TIMESTAMP | DEFAULT now |

#### 4.4.2 `Company`

| Column | Type | Constraint |
|---|---|---|
| Company_ID | INT UNSIGNED AI | PK |
| Company_Name | VARCHAR(120) | NOT NULL, UNIQUE |
| Industry | VARCHAR(80) | NOT NULL |
| Location | VARCHAR(100) | NOT NULL |
| HR_Name | VARCHAR(100) | NOT NULL |
| HR_Email | VARCHAR(120) | NOT NULL, UNIQUE |
| Contact_Number | VARCHAR(15) | NOT NULL |
| Website | VARCHAR(150) | NULL |
| Password_Hash | VARCHAR(255) | NOT NULL |
| Approval_Status | ENUM | Pending/Approved/Rejected |
| Created_At | TIMESTAMP | DEFAULT now |

#### 4.4.3 `Placement_Officer`

| Column | Type | Constraint |
|---|---|---|
| Officer_ID | INT UNSIGNED AI | PK |
| Name | VARCHAR(100) | NOT NULL |
| Email | VARCHAR(120) | NOT NULL, UNIQUE |
| Contact_Number | VARCHAR(15) | NOT NULL |
| Designation | VARCHAR(80) | NOT NULL |
| Password_Hash | VARCHAR(255) | NOT NULL |
| Account_Role | ENUM | Officer/Admin |
| Is_Active | TINYINT(1) | CHECK 0/1 |
| Created_At | TIMESTAMP | DEFAULT now |

#### 4.4.4 `Job`

| Column | Type | Constraint |
|---|---|---|
| Job_ID | INT UNSIGNED AI | PK |
| Company_ID | INT UNSIGNED | FK → Company, CASCADE |
| Job_Title | VARCHAR(120) | NOT NULL |
| Job_Description | TEXT | NOT NULL |
| Eligible_Branch | VARCHAR(150) | default `All` |
| Min_CGPA | DECIMAL(4,2) | CHECK 0–10 |
| Salary_Package | DECIMAL(10,2) | CHECK ≥ 0 (LPA) |
| Job_Location | VARCHAR(100) | NOT NULL |
| Application_Deadline | DATE | indexed |
| Job_Type | ENUM | Full-Time/Internship/Internship + PPO/Part-Time |
| Created_At | TIMESTAMP | DEFAULT now |

#### 4.4.5 `Application`

| Column | Type | Constraint |
|---|---|---|
| Application_ID | INT UNSIGNED AI | PK |
| Student_ID | INT UNSIGNED | FK → Student, CASCADE |
| Job_ID | INT UNSIGNED | FK → Job, CASCADE |
| Application_Date | DATE | default current date |
| Status | ENUM | Applied … Withdrawn |
| Updated_At | TIMESTAMP | auto-update |

Unique `(Student_ID, Job_ID)`; index `(Job_ID, Status)`.

#### 4.4.6 `Recruitment_Round`

| Column | Type | Constraint |
|---|---|---|
| Round_ID | INT UNSIGNED AI | PK |
| Job_ID | INT UNSIGNED | FK → Job, CASCADE |
| Round_Name | VARCHAR(80) | NOT NULL |
| Round_Type | ENUM | Aptitude/Technical/HR/GD/Coding/Other |
| Round_Date | DATE | NOT NULL |
| Max_Marks | DECIMAL(6,2) | CHECK > 0 |

Unique `(Job_ID, Round_Name)`.

#### 4.4.7 `Interview`

| Column | Type | Constraint |
|---|---|---|
| Interview_ID | INT UNSIGNED AI | PK |
| Application_ID | INT UNSIGNED | FK → Application, CASCADE |
| Round_ID | INT UNSIGNED | FK → Round, CASCADE |
| Interview_Date | DATETIME | NOT NULL |
| Result | ENUM | Pending/Pass/Fail/On Hold |
| Interviewer_Name | VARCHAR(100) | NOT NULL |
| Marks_Obtained | DECIMAL(6,2) | NULL, CHECK ≥ 0 |
| Remarks | VARCHAR(255) | NULL |

Unique `(Application_ID, Round_ID)`.

#### 4.4.8 `Placement`

| Column | Type | Constraint |
|---|---|---|
| Placement_ID | INT UNSIGNED AI | PK |
| Student_ID | INT UNSIGNED | FK → Student, CASCADE |
| Job_ID | INT UNSIGNED | FK → Job, RESTRICT |
| Company_ID | INT UNSIGNED | FK → Company, RESTRICT |
| Placement_Date | DATE | default current date |
| Package_Offered | DECIMAL(10,2) | CHECK ≥ 0 |
| Joining_Date | DATE | NULL, CHECK ≥ Placement_Date |
| Status | ENUM | Offer Released/Accepted/Declined/Joined/Withdrawn |

Unique `(Student_ID, Job_ID)` allows multiple offers from different jobs.

#### 4.4.9 `Report`

| Column | Type | Constraint |
|---|---|---|
| Report_ID | INT UNSIGNED AI | PK |
| Report_Type | ENUM | six report types |
| Generated_Date | DATETIME | DEFAULT now |
| Generated_By | INT UNSIGNED | FK → Placement_Officer, RESTRICT |
| Description | VARCHAR(500) | NULL |

### 4.5 Normalization

**First normal form.** Each column holds one value. The only deliberate
exception is `Job.Eligible_Branch`, a comma-separated list required to keep the
schema at nine tables; it is queried with `FIND_IN_SET` rather than split in
application code.

**Second normal form.** All non-key attributes depend on the whole key. Bridge
tables use a surrogate primary key plus a composite unique key, so no partial
dependency exists.

**Third normal form.** No non-key attribute depends on another non-key
attribute. `Placement.Company_ID` is a documented, trigger-protected redundancy
for fast company reports; it is functionally determined by `Job_ID`, which is
why the triggers exist.

**Result:** the schema satisfies 3NF and, apart from those two documented
decisions, BCNF.

### 4.6 Design decisions

| Decision | Reason |
|---|---|
| Admin stored in `Placement_Officer` | Keeps exactly nine tables; `Account_Role` distinguishes dashboards |
| Surrogate keys everywhere | Stable references, simple joins |
| `Eligible_Branch` as text | Avoids a tenth table and a job-branch mapping table |
| `Company_ID` in `Placement` | Faster company reports, enforced by triggers |
| `Marks_Obtained` in `Interview` | `Max_Marks` alone cannot store a candidate's score |
| `Approval_Status` in `Company` | Placement cell must verify recruiters before jobs go live |
| `Is_Active` in `Placement_Officer` | Deactivate accounts without breaking report history |
| `ON DELETE RESTRICT` for offers/reports | Preserve financial and audit history |

---

## 5. Implementation

### 5.1 Technology choices

- **Flask** — minimal, explicit routing; ideal for showing how requests map to
  SQL.
- **mysql-connector-python** — official driver; supports prepared parameters.
- **Jinja2** — server-side rendering prevents the dashboard from becoming a
  separate JavaScript application.
- **Chart.js** — small chart library loaded from a CDN with a graceful
  offline fallback.
- **Hand-written CSS** — no framework, so the responsive rules and design
  system are visible and explainable in the viva.

### 5.2 Authentication

Registration hashes the password before insert:

```python
password_hash = generate_password_hash(password)
execute(
    """
    INSERT INTO Student
        (Name, Email, Phone, Password_Hash, Date_of_Birth,
         Gender, Branch, Batch_Year, CGPA, Address)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,
    (name, email, phone, password_hash, dob, gender,
     branch, batch_year, cgpa, address),
)
```

Login verifies the hash and the account state:

```python
student = query_one("SELECT * FROM Student WHERE Email=%s", (email,))
if not student or not check_password_hash(student["Password_Hash"], password):
    flash("Invalid email or password.", "danger")
    return render_template("auth/student_login.html")
session.clear()
session["user_id"] = student["Student_ID"]
session["role"] = "Student"
session["name"] = student["Name"]
```

### 5.3 Role-based authorisation

A single decorator protects every private route:

```python
def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("index"))
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
```

Usage:

```python
@app.route("/officer/students")
@roles_required("Officer", "Admin")
def officer_students():
    ...
```

Links are hidden in templates for convenience, but the server check is the real
control.

### 5.4 Eligibility engine

The same rule is used on the student job list, the job detail page, the apply
route and the officer eligibility page:

```python
def is_eligible(student, job):
    if student["CGPA"] < job["Min_CGPA"]:
        return False
    allowed = (job.get("Eligible_Branch") or "All").split(",")
    allowed = [b.strip().lower() for b in allowed if b.strip()]
    if "all" in allowed:
        return True
    return (student.get("Branch") or "").strip().lower() in allowed
```

In SQL the equivalent is:

```sql
WHERE s.CGPA >= j.Min_CGPA
  AND (j.Eligible_Branch = 'All'
       OR FIND_IN_SET(s.Branch, j.Eligible_Branch) > 0)
```

### 5.5 Application rules

The apply route checks, in order:

1. Session student exists.
2. Job exists and the deadline has not passed.
3. Student is eligible.
4. Student does not already have a Selected/Joined offer.
5. Student has not already applied.

Only then does it insert with status `Applied`. The unique key is the final
safeguard against duplicate submissions.

### 5.6 Transactions

`database.py` keeps multi-table changes atomic. Creating an offer:

```python
conn.start_transaction()
cursor.execute("INSERT INTO Placement (...) VALUES (...)", (...))
cursor.execute(
    "UPDATE Application SET Status='Selected' WHERE Student_ID=%s AND Job_ID=%s",
    (student_id, job_id),
)
conn.commit()
```

Deleting an offer reverses it:

```python
cursor.execute("SELECT Student_ID, Job_ID FROM Placement WHERE Placement_ID=%s FOR UPDATE", ...)
cursor.execute("DELETE FROM Placement WHERE Placement_ID=%s", ...)
cursor.execute(
    "UPDATE Application SET Status='Shortlisted' "
    "WHERE Student_ID=%s AND Job_ID=%s AND Status='Selected'",
    ...,
)
conn.commit()
```

Any exception triggers `conn.rollback()`.

### 5.7 Advanced SQL objects

- **Views** hide multi-table joins for dashboards and reports.
- **`fn_placement_percentage()`** centralises the placement-rate definition.
- **`sp_eligible_students()`** returns the eligibility list with an applied flag.
- **`sp_company_selection_summary()`** produces the recruiter scorecard.
- **Triggers** enforce cross-table rules that a single `CHECK` cannot express
  (company must own the job; no applications after the deadline; an offer
  forces the application to Selected).
- **Indexes** on `Job.Application_Deadline` and
  `Application(Job_ID, Status)` support the most common filters.

### 5.8 Reports

`build_report_data(report_type)` returns columns, rows and a summary for each
report type. The `Report` table stores only metadata (type, date, author,
description); the data is recomputed on open so reports never show stale
numbers. This demonstrates the difference between **stored** and **derived**
data, and keeps the audit trail without duplicating the database.

### 5.9 User interface

- Public pages use a marketing layout with live statistics.
- Authenticated pages use a sidebar layout with role-specific navigation.
- Shared macros render status badges, statistic cards and empty states.
- Tables scroll horizontally on small screens; forms become single-column.
- Chart scripts are loaded after Chart.js and check `typeof Chart` and the
  canvas element, so an offline CDN failure does not break the page.
- `main.js` handles the mobile sidebar, flash dismissal, table filtering,
  automatic form submission and confirmation dialogs.

---

## 6. Testing

Testing combined static validation, Flask's test client and a documented
manual/database test plan.

**Executed on the final build**

- The schema, demo data and advanced objects were loaded into MySQL 8.0.46
  without errors; all object counts and sample counts matched expectations.
- 49 templates parsed and compiled in the real Flask Jinja environment.
- 62 routes registered; every `url_for` endpoint resolved.
- Every rendered template received all variables it referenced.
- A 62-check end-to-end sweep against the live database passed: login for all
  four roles, every dashboard and list page, apply/duplicate/withdraw,
  accept-offer, job create/delete, placement create/delete with status revert,
  report generation and access-control checks.
- All four demo password hashes verified.
- SQL scripts parsed as valid MySQL statements; routine bodies reviewed
  manually.

**Database test plan**

The full table of 20 database constraint tests and 15 authentication tests is
in [`TESTING.md`](TESTING.md). Key cases include duplicate applications, CGPA
above 10, applications after the deadline, offers with the wrong company,
deleting a company that has offers (blocked) and deleting a student (cascades).

**Outcome:** no unresolved functional defects were found in the validated
paths. Known limitations are listed in the README (no CSRF tokens, CDN chart
dependency, development server only).

---

## 7. Results

With the demo dataset loaded, the system reports:

| Metric | Value |
|---|---|
| Registered students | 20 |
| Approved companies | 5 |
| Jobs | 10 |
| Applications | 43 |
| Recruitment rounds | 24 |
| Interviews | 38 |
| Offers | 10 (held by 9 students) |
| Accepted/joined offers | 6 |
| Placement rate | 30.00% |
| Highest package | 10.50 LPA |
| Average accepted package | 8.00 LPA |
| Placement-cell accounts | 3 (2 officers + 1 admin) |
| Reports | 5 |

These numbers appear consistently on the officer dashboard, admin dashboard,
public home page and reports because they all read the same tables.

---

## 8. Screenshots

Place your own screenshots in the `screenshots/` folder and insert them here.
Suggested set:

1. `01-home.png` — public home page with live stats.
2. `02-student-dashboard.png` — student dashboard with status chart.
3. `03-student-jobs.png` — job list with eligibility badges.
4. `04-recruiter-dashboard.png` — recruiter funnel.
5. `05-applicants.png` — applicant status controls.
6. `06-officer-dashboard.png` — branch chart and pending approvals.
7. `07-officer-eligibility.png` — eligible vs applied list.
8. `08-admin-dashboard.png` — package distribution and branch table.
9. `09-report.png` — printable report detail.
10. `10-er-diagram.png` — reverse-engineered ER diagram from Workbench.

---

## 9. Conclusion

The project delivers a complete placement workflow on a compact nine-table
schema. It shows that careful database design — unique keys, foreign keys,
checks, triggers and transactions — removes most of the manual reconciliation
that plagues spreadsheet-based placement cells. The Flask layer stays thin and
readable, and every dashboard number is traceable to a SQL query rather than a
hard-coded value.

From a learning perspective, the project covers the full DBMS syllabus:
conceptual and logical design, normalization, DDL and DML, joins and
subqueries, set operations, views, stored procedures, functions, triggers,
transactions, indexing, access control and application integration.

---

## 10. Future scope

1. **Resume uploads** with a `Document` table and file storage.
2. **Email/SMS notifications** for shortlist, interview and offer events.
3. **CSRF protection and rate limiting** for production deployment.
4. **PDF/Excel export** of reports instead of print-only HTML.
5. **Interview calendar** with conflict detection and interviewer accounts.
6. **Multi-year analytics** and alumni placement history.
7. **REST API and mobile client** reusing the same database.
8. **Automated tests** with pytest and a disposable test database.
9. **Role for faculty coordinators** with branch-level scope.
10. **Password reset** with one-time tokens.

---

## 11. References

1. MySQL 8.0 Reference Manual — https://dev.mysql.com/doc/refman/8.0/en/
2. Flask Documentation — https://flask.palletsprojects.com/
3. Jinja2 Template Documentation — https://jinja.palletsprojects.com/
4. mysql-connector-python Documentation — https://dev.mysql.com/doc/connector-python/en/
5. Werkzeug Security Utilities — https://werkzeug.palletsprojects.com/
6. Chart.js Documentation — https://www.chartjs.org/docs/
7. Elmasri, R. and Navathe, S. B., *Fundamentals of Database Systems*,
   Pearson.
8. Silberschatz, A., Korth, H. F. and Sudarshan, S., *Database System
   Concepts*, McGraw-Hill.
9. OWASP Top Ten — https://owasp.org/www-project-top-ten/

---

## Appendix A — Demo credentials

| Role | Email | Password |
|---|---|---|
| Student | `aarav.sharma@college.edu` | `Student@123` |
| Student (two offers) | `priya.menon@college.edu` | `Student@123` |
| Recruiter | `hr@technova.example.com` | `Recruiter@123` |
| Recruiter | `careers@databridge.example.com` | `Recruiter@123` |
| Officer | `suresh.kulkarni@college.edu` | `Officer@123` |
| Administrator | `admin@college.edu` | `Admin@123` |

## Appendix B — File inventory

| File | Purpose |
|---|---|
| `app.py` | Routes, validation, helpers, reports, error handling |
| `database.py` | Connection, queries, placement transactions |
| `database/schema.sql` | Database and nine tables |
| `database/sample_data.sql` | Demo data and PBKDF2 hashes |
| `database/advanced_objects.sql` | Views, function, procedures, triggers |
| `templates/` | 49 Jinja templates across five areas |
| `static/css/style.css` | Design system and responsive rules |
| `static/js/main.js` | Sidebar, filters, confirmations |
| `tools/hash_password.py` | Generate a password hash |
| `tools/check_db.py` | Verify connection, counts, objects |
| `requirements.txt` | Python dependencies |
| `run.bat` | Windows setup and run |
| `.env.example` | Configuration template |
| `docs/` | Report, ER diagram, viva queries, testing |
| `.vscode/` | Debug configuration and editor settings |
