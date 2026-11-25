# Testing Documentation

This document records how the system was validated, the manual test cases for
each role, the database constraint tests, and the checks to repeat after any
change.

---

## 1. Test environment

| Item | Value |
|---|---|
| Operating system | Windows 11 |
| Python | 3.11 |
| Flask | 3.1.x |
| Jinja2 | 3.1.x |
| MySQL Server | 8.0 (service `MySQL80`) |
| Browser | Chrome / Edge (latest) |
| Editor | VS Code |

---

## 2. Validation already performed

These checks were run against the final source tree.

| Check | Tool / method | Result |
|---|---|---|
| All templates parse as valid Jinja | Jinja2 `Environment.parse` | **49 / 49 pass** |
| All templates compile in the app's Jinja env | `app.jinja_env.get_template()` | **49 / 49 pass** |
| Every `url_for('endpoint')` resolves | Compare against `app.url_map` | **0 unknown endpoints** |
| Every `render_template('file')` target exists | Filesystem check | **0 missing** |
| Every route passes the variables its template uses | Jinja `meta.find_undeclared_variables` | **0 missing** |
| `app.py` syntax | `compile()` + pyflakes | **0 errors** |
| Registered routes | `app.url_map` | **62 routes** |
| 403 page for wrong role | Flask test client | **403 Access denied** |
| 404 page for unknown URL | Flask test client | **404 rendered** |
| Logout clears session | Flask test client | **302 to home** |
| Guest redirected from protected page | Flask test client | **302 to login/home** |
| Demo password hashes | `check_password_hash` | **4 / 4 match** |
| `schema.sql` syntax | sqlglot (MySQL dialect) | **22 statements parse** |
| `sample_data.sql` syntax | sqlglot (MySQL dialect) | **28 statements parse** |
| `advanced_objects.sql` views | sqlglot | **5 views parse** |
| Procedure/trigger bodies | Manual review (sqlglot lacks routine support) | **syntax reviewed** |

> Database-level tests below require the schema and sample data to be loaded.
> See `README.md` for the three-script order.

### 2.1 Live end-to-end run

The complete stack was also exercised against a real MySQL 8.0.46 instance:

| Check | Result |
|---|---|
| `schema.sql` executed | 9 tables created |
| `sample_data.sql` executed | 20 / 5 / 10 / 43 / 24 / 38 / 10 / 3 / 5 rows |
| `advanced_objects.sql` executed | 5 views, 1 function, 2 procedures, 4 triggers |
| `fn_placement_percentage()` | `30.00` |
| `sp_eligible_students(1)` | 14 rows, applied flag correct |
| Flask test-client route sweep | **62 checks, 0 failures** |
| Student apply → duplicate block → withdraw | Pass |
| Student accept offer → re-answer block | Pass |
| Recruiter create job → invalid branch block → delete | Pass |
| Officer create placement → application Selected | Pass |
| Officer delete placement → application Shortlisted | Pass |
| Officer generate/open report | Pass |
| Admin create officer account | Pass |
| Role and guest access checks | 403 / 302 as expected |
| Demo data restored after mutation tests | Counts unchanged |

---

## 3. Authentication and access control

| ID | Test | Steps | Expected result | Status |
|---|---|---|---|---|
| AUTH-01 | Student login success | `/student/login` → `aarav.sharma@college.edu` / `Student@123` | Redirect to `/student/dashboard`, name in sidebar | Pass (hash verified) |
| AUTH-02 | Student login wrong password | Same email, `wrongpass` | Stays on login, red flash "Invalid email or password" | Pass (code review) |
| AUTH-03 | Recruiter login success | `hr@technova.example.com` / `Recruiter@123` | Recruiter dashboard | Pass (hash verified) |
| AUTH-04 | Officer login success | `suresh.kulkarni@college.edu` / `Officer@123` | Officer dashboard | Pass (hash verified) |
| AUTH-05 | Admin login success | `admin@college.edu` / `Admin@123` | Admin dashboard | Pass (hash verified) |
| AUTH-06 | Admin cannot use officer login | `admin@college.edu` on `/officer/login` | Rejected because `Account_Role='Admin'` | Pass (route filter) |
| AUTH-07 | Officer cannot use admin login | `suresh.kulkarni@college.edu` on `/admin/login` | Rejected (role filter) | Pass (route filter) |
| AUTH-08 | Inactive officer blocked | Set `Is_Active=0`, then login | "account is deactivated" message | Pass (code review) |
| AUTH-09 | Pending recruiter blocked | Register a company, try login before approval | Login blocked with pending-approval message | Pass (code review) |
| AUTH-10 | Rejected recruiter blocked | Set `Approval_Status='Rejected'`, login | Login blocked | Pass (code review) |
| AUTH-11 | Student cannot open officer URL | Student session → `/officer/dashboard` | 403 Access denied page | Pass (test client) |
| AUTH-12 | Guest redirected | No session → `/recruiter/dashboard` | 302 to `/` | Pass (test client) |
| AUTH-13 | Logout | Click Logout | Session cleared, redirect to home | Pass (test client) |
| AUTH-14 | Duplicate student email | Register existing email | "email already registered" | Pass (code review) |
| AUTH-15 | Short password | Register with 5 characters | Rejected by `minlength` and server check | Pass (code review) |

---

## 4. Student module

| ID | Test | Steps | Expected result |
|---|---|---|---|
| STU-01 | Dashboard loads | Login as Aarav | Stats, status chart, profile and offers render |
| STU-02 | Browse open jobs | Open `/student/jobs` | Only jobs with deadline ≥ today |
| STU-03 | Search jobs | Type "Data" in search | Only matching title/company/location |
| STU-04 | Branch filter | Select `MCA` | Jobs allowing MCA appear |
| STU-05 | Eligible-only filter | Tick "eligible only" | Only jobs matching CGPA + branch |
| STU-06 | Ineligible job hidden apply | Open a job requiring CGPA 9.4 as Aarav (8.6) | Apply button disabled / blocked |
| STU-07 | Apply success | Apply to an eligible open job | Row appears in applications, flash success |
| STU-08 | Duplicate apply blocked | Apply to the same job again | "already applied" warning |
| STU-09 | Closed job apply blocked | Craft POST to closed job | Rejected server-side |
| STU-10 | Withdraw application | Withdraw an active application | Status becomes `Withdrawn` |
| STU-11 | Cannot withdraw Selected | Try to withdraw an application whose status is Selected | Blocked |
| STU-12 | Offers page | Login as Priya Menon | Two offers, one accepted and one declined |
| STU-13 | Accept offer | Change status to Offer Accepted | Badge updates, placement stats update |
| STU-14 | Profile update | Change phone/address/CGPA | Saved, sidebar name unchanged, new CGPA used by eligibility |
| STU-15 | Email is read-only | Inspect profile form | Email field disabled/readonly |
| STU-16 | Student cannot see other student's data | Craft `/student/applications` as another user | Only own rows returned (session-based) |

---

## 5. Recruiter module

| ID | Test | Steps | Expected result |
|---|---|---|---|
| REC-01 | Dashboard | Login as TechNova recruiter | Open jobs, application funnel, recent offers |
| REC-02 | Pending company cannot post | Use a newly registered company | Redirect with warning until approved |
| REC-03 | Create job | Fill all fields, allowed branches `MCA,CSE` | Job appears in list |
| REC-04 | Invalid branch rejected | Enter `MCA,MBA` | Warning listing valid branches |
| REC-05 | CGPA bounds | Enter 11 | "between 0 and 10" warning |
| REC-06 | Negative salary | Enter -5 | Rejected |
| REC-07 | Past deadline | Choose yesterday | Rejected |
| REC-08 | Edit own job | Change title/package | Saved |
| REC-09 | Edit other company's job | Craft `/recruiter/jobs/3/edit` as TechNova | 404 (ownership filter) |
| REC-10 | Delete own job | Delete job with no placements | Redirect, job gone, applications cascade |
| REC-11 | Applicants list | Open applicants for Job 1 | Students with CGPA/branch/status |
| REC-12 | Status update | Set an applicant to Shortlisted | Badge changes, student sees it |
| REC-13 | Invalid status | POST `status=Hired` | Rejected |
| REC-14 | Add round | Add "Round 4 - Manager" | Appears in round list |
| REC-15 | Duplicate round name | Add same name twice | Friendly error |
| REC-16 | Schedule interview | Choose applicant, round, date, interviewer | Interview row created, application becomes `Interview Scheduled` |
| REC-17 | Interview date in past | Choose yesterday | Rejected |
| REC-18 | Marks above max | Enter 150 for a 100-mark round | Rejected |
| REC-19 | Record result | Set Pass/Fail and marks | Interview list updates |
| REC-20 | Release offer | Use offer form for a shortlisted applicant | Placement created, application becomes Selected |
| REC-21 | Duplicate offer | Offer the same student the same job again | Friendly "already has an offer" message |
| REC-22 | Offer for another company's applicant | Craft URL | 404 |
| REC-23 | Update placement status | Mark Offer Accepted | Student and officer see the change |
| REC-24 | Profile update | Change HR phone | Saved and shown on public company page |

---

## 6. Officer module

| ID | Test | Steps | Expected result |
|---|---|---|---|
| OFF-01 | Dashboard | Login as officer | Stats, branch chart, status chart, pending approvals |
| OFF-02 | Student search | Search "Nair" | Meera Nair only |
| OFF-03 | Branch filter | Select ECE | Three ECE students |
| OFF-04 | Student detail | Open a student | Applications, interviews, placements, profile |
| OFF-05 | Edit CGPA | Change CGPA and save | Detail page reflects it, eligibility changes |
| OFF-06 | Delete student | Delete a student with applications | Cascades to applications/interviews/placements after confirm |
| OFF-07 | Company approval | Approve a pending company | Status Approved, recruiter can log in |
| OFF-08 | Company rejection | Reject a company | Status Rejected, recruiter blocked |
| OFF-09 | Company detail | Open TechNova | Jobs, placements, HR details |
| OFF-10 | Eligibility page | Open Job 1 eligibility | 14 students, applied flag correct |
| OFF-11 | All applications | Open officer applications | 43 rows, filters by status/company work |
| OFF-12 | Add round for a job | Select a job, add round | Round appears and is unique per job |
| OFF-13 | Delete round | Delete a round with interviews | Interviews cascade after confirmation |
| OFF-14 | Interviews filter | Upcoming / past / all | Correct date filtering |
| OFF-15 | Create placement | Choose student + job + package | Offer created, application Selected |
| OFF-16 | Delete placement | Delete an offer | Offer gone, application reverts to Shortlisted |
| OFF-17 | Generate report | Choose "Branch-wise Report" | Report row saved, detail table correct |
| OFF-18 | Report detail | Open saved report | Columns, summary cards, print button |
| OFF-19 | Invalid report type | POST `report_type=Hack` | Rejected |

---

## 7. Administrator module

| ID | Test | Expected result |
|---|---|---|
| ADM-01 | Admin dashboard | College-wide stats, package bands chart, branch table |
| ADM-02 | Create officer account | New row in `Placement_Officer`, password hashed |
| ADM-03 | Create duplicate email | Friendly uniqueness error |
| ADM-04 | Toggle account | Active → Inactive; inactive account cannot log in |
| ADM-05 | Cannot deactivate self | "Your account" label, no toggle button |
| ADM-06 | Reports access | Admin can open `/officer/reports` |
| ADM-07 | Admin cannot access student data endpoints | 403 |

---

## 8. Database constraint tests

Run in MySQL Workbench after loading the sample data.

| ID | Statement | Expected |
|---|---|---|
| DB-01 | `INSERT INTO Student (...) VALUES (... CGPA 11 ...)` | Error 3819, `chk_student_cgpa` |
| DB-02 | `INSERT INTO Student (...) VALUES (... Batch_Year 1990 ...)` | Error 3819, `chk_student_batch` |
| DB-03 | Duplicate student email | Error 1062 on `uq_student_email` |
| DB-04 | Duplicate application `(1,1)` | Error 1062 on `uq_application_student_job` |
| DB-05 | Duplicate round name in the same job | Error 1062 on `uq_round_job_name` |
| DB-06 | Second interview for the same application + round | Error 1062 on `uq_interview_app_round` |
| DB-07 | Duplicate placement `(Student_ID, Job_ID)` | Error 1062 on `uq_placement_student_job` |
| DB-08 | Placement with wrong `Company_ID` | Error 45000 from `trg_placement_company_check` |
| DB-09 | Application after the deadline | Error 45000 from `trg_application_deadline_check` |
| DB-10 | Negative package | Error 3819, `chk_placement_package` |
| DB-11 | Joining date before placement date | Error 3819, `chk_placement_joining` |
| DB-12 | Negative marks | Error 3819, `chk_interview_marks` |
| DB-13 | Delete company with offers | Error 1451 (RESTRICT) |
| DB-14 | Delete a student with applications | Cascades to applications, interviews, placements |
| DB-15 | Delete a job with placements | Error 1451 (RESTRICT) |
| DB-16 | Delete an officer who generated reports | Error 1451 (RESTRICT) |
| DB-17 | Insert placement | Trigger sets the matching application to Selected |
| DB-18 | `CALL sp_eligible_students(1)` | 14 eligible rows with `Already_Applied` flag |
| DB-19 | `SELECT fn_placement_percentage()` | `30.00` |
| DB-20 | `SELECT * FROM vw_unplaced_students` | 14 rows |

---

## 9. UI and responsive checks

| Width | Pages checked | Expected |
|---|---|---|
| ≥ 1200 px | All dashboards and public pages | Full sidebar, multi-column grids |
| 992 px | Dashboards | Cards reflow, tables scroll horizontally |
| 768 px | Public site, logins | Hamburger nav, single-column forms |
| 420 px | Student dashboard, jobs, applications | No horizontal page scroll, readable buttons |
| Print | Officer report detail | Sidebar hidden, table readable |
| Keyboard | Login, forms, nav | Visible focus rings, labels associated |
| No internet | Any dashboard | Charts hidden with "no data" fallback, no JS errors |

---

## 10. Security checks

| ID | Test | Expected |
|---|---|---|
| SEC-01 | SQL injection in login email (`' OR 1=1 --`) | Login fails; parameterised query treats it as text |
| SEC-02 | SQL injection in search box | Search returns no rows, no SQL error |
| SEC-03 | Role escalation by URL | 403 on every other role's dashboard |
| SEC-04 | IDOR on recruiter job edit | 404 for another company's job |
| SEC-05 | IDOR on officer student detail | Allowed for officer (by design), denied for student/recruiter |
| SEC-06 | Password column contents | Starts with `pbkdf2:` / `scrypt:`, never plain text |
| SEC-07 | Session cookie | `HttpOnly` default, signed with `SECRET_KEY` |
| SEC-08 | Mutating GET | No GET route changes data |
| SEC-09 | Error page leakage | 500 page hides stack trace in non-debug mode |
| SEC-10 | Deactivated officer session | Existing session rejected on next request |

---

## 11. Performance sanity checks

| ID | Check | Expected |
|---|---|---|
| PERF-01 | Student dashboard queries | 6 small indexed queries, < 100 ms locally |
| PERF-02 | Officer applications with 43 rows | Single join query, < 100 ms |
| PERF-03 | `vw_branch_placement_stats` | Grouped scan of 20 students, instant |
| PERF-04 | Job list uses `idx_job_deadline` | `EXPLAIN` shows the index for deadline filters |
| PERF-05 | Application funnel uses `idx_application_job_status` | `EXPLAIN` uses the composite index |

Check with:

```sql
EXPLAIN SELECT * FROM Job WHERE Application_Deadline >= CURDATE();
EXPLAIN SELECT Status, COUNT(*) FROM Application
WHERE Job_ID = 1 GROUP BY Status;
```

---

## 12. How to repeat the automated checks

Create a virtual environment (once), then run:

```powershell
# 1. Compile check
python -m py_compile app.py database.py tools\check_db.py tools\hash_password.py

# 2. Template and endpoint validation
python validate_project.py      # see the script in the project notes

# 3. Live database verification
.\.venv\Scripts\python.exe tools\check_db.py
```

Expected final lines:

```
[OK]   MySQL 8.0.x as root@localhost on college_placement_db
...
Views found (5): vw_branch_placement_stats, vw_company_selection_stats, ...
Procedures/functions (3):
  FUNCTION   fn_placement_percentage
  PROCEDURE  sp_company_selection_summary
  PROCEDURE  sp_eligible_students
Triggers (4): trg_application_deadline_check, ...
```

---

## 13. Regression checklist after edits

1. Public pages load with no session.
2. All four logins succeed with demo credentials.
3. Each dashboard shows non-zero, live numbers.
4. Apply → shortlist → interview → offer → accept works end to end.
5. Deleting the offer reverts the application to Shortlisted.
6. Company approval unlocks recruiter job posting.
7. Officer reports open and print.
8. No new console errors in the browser.
9. `python -m py_compile` passes.
10. `tools/check_db.py` still reports 9 tables, 5 views, 3 routines,
    4 triggers.

---

## 14. Known limitations accepted for this submission

- No CSRF tokens (documented in README).
- No automated unit-test suite; validation is static + manual as described.
- Charts require the Chart.js CDN.
- MySQL Workbench on some systems blocks safe updates without a key; all
  provided statements include a `WHERE` clause.
