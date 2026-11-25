# Viva SQL Query Bank

Forty-plus queries and demonstrations for the practical viva, grouped from
simple to advanced. Every query uses the actual table and column names in
`database/schema.sql` and runs against the demo data from
`database/sample_data.sql`.

> Run `USE college_placement_db;` first in MySQL Workbench.
> Expected values below assume the demo data has just been loaded
> (20 students, 5 companies, 10 jobs, 43 applications, 24 rounds,
> 38 interviews, 10 offers, 3 officers, 5 reports).

---

## A. Basic retrieval

### Q1. List all students in MCA, best CGPA first

```sql
SELECT Student_ID, Name, Branch, CGPA
FROM Student
WHERE Branch = 'MCA'
ORDER BY CGPA DESC;
```

**Teaches:** `WHERE`, `ORDER BY`. Returns the 7 MCA students, starting with
Diya Patel (9.10).

### Q2. Students with CGPA between 8 and 9.5

```sql
SELECT Name, Branch, CGPA
FROM Student
WHERE CGPA BETWEEN 8.00 AND 9.50
ORDER BY CGPA DESC;
```

**Teaches:** `BETWEEN` is inclusive on both ends.

### Q3. Students whose name starts with "A" or ends with "a"

```sql
SELECT Name, Email
FROM Student
WHERE Name LIKE 'A%' OR Name LIKE '%a';
```

**Teaches:** `LIKE` wildcards.

### Q4. Five highest packages among all offers

```sql
SELECT Placement_ID, Student_ID, Package_Offered, Status
FROM Placement
ORDER BY Package_Offered DESC
LIMIT 5;
```

**Teaches:** `ORDER BY ... LIMIT`. The top offer is 10.50 LPA.

### Q5. Jobs closing in the next 60 days

```sql
SELECT Job_ID, Job_Title, Application_Deadline,
       DATEDIFF(Application_Deadline, CURDATE()) AS Days_Left
FROM Job
WHERE Application_Deadline BETWEEN CURDATE()
      AND DATE_ADD(CURDATE(), INTERVAL 60 DAY)
ORDER BY Application_Deadline;
```

**Teaches:** date arithmetic with `DATEDIFF` and `DATE_ADD`.
On 12 Nov 2026 this returns jobs with deadlines up to 11 Jan 2027.

### Q6. Distinct branches that have at least one student

```sql
SELECT DISTINCT Branch
FROM Student
ORDER BY Branch;
```

**Teaches:** `DISTINCT`.

---

## B. Joins

### Q7. Every job with its company name

```sql
SELECT j.Job_ID, j.Job_Title, c.Company_Name, j.Salary_Package, j.Job_Location
FROM Job j
JOIN Company c ON c.Company_ID = j.Company_ID
ORDER BY c.Company_Name, j.Job_Title;
```

**Teaches:** inner join on a foreign key.

### Q8. Applications with student, job and company in one row

```sql
SELECT a.Application_ID,
       s.Name AS Student,
       s.Branch,
       j.Job_Title,
       c.Company_Name,
       a.Status,
       a.Application_Date
FROM Application a
JOIN Student s ON s.Student_ID = a.Student_ID
JOIN Job j     ON j.Job_ID = a.Job_ID
JOIN Company c ON c.Company_ID = j.Company_ID
ORDER BY a.Application_Date DESC;
```

**Teaches:** a four-table join. Returns all 43 applications.

### Q9. Every company, even those with no jobs (LEFT JOIN)

```sql
SELECT c.Company_Name, COUNT(j.Job_ID) AS Total_Jobs
FROM Company c
LEFT JOIN Job j ON j.Company_ID = c.Company_ID
GROUP BY c.Company_ID, c.Company_Name
ORDER BY Total_Jobs DESC;
```

**Teaches:** `LEFT JOIN` keeps unmatched companies. In the demo data all five
companies have jobs, but the query stays correct after deleting a job.

### Q10. Students and their offers, including students without offers

```sql
SELECT s.Name, s.Branch, p.Package_Offered, p.Status
FROM Student s
LEFT JOIN Placement p ON p.Student_ID = s.Student_ID
ORDER BY s.Name;
```

**Teaches:** `LEFT JOIN` with `NULL` handling. 20 rows; 14 have `NULL` package
(10 offers held by 9 distinct students).

### Q11. Interviews with student, round and company

```sql
SELECT i.Interview_ID,
       s.Name AS Student,
       c.Company_Name,
       r.Round_Name,
       i.Interview_Date,
       i.Result,
       i.Marks_Obtained
FROM Interview i
JOIN Application a       ON a.Application_ID = i.Application_ID
JOIN Student s           ON s.Student_ID = a.Student_ID
JOIN Recruitment_Round r ON r.Round_ID = i.Round_ID
JOIN Job j               ON j.Job_ID = r.Job_ID
JOIN Company c           ON c.Company_ID = j.Company_ID
ORDER BY i.Interview_Date;
```

**Teaches:** chaining five joins through bridge tables. Returns 38 interviews.

### Q12. Jobs that have never received an application

```sql
SELECT j.Job_ID, j.Job_Title, c.Company_Name
FROM Job j
JOIN Company c ON c.Company_ID = j.Company_ID
LEFT JOIN Application a ON a.Job_ID = j.Job_ID
WHERE a.Application_ID IS NULL;
```

**Teaches:** the `LEFT JOIN ... IS NULL` anti-join pattern. Returns
"Data Engineering Intern" (Job 4).

---

## C. Aggregation and grouping

### Q13. Applications per job, only jobs with two or more

```sql
SELECT j.Job_Title, COUNT(a.Application_ID) AS Applications
FROM Job j
JOIN Application a ON a.Job_ID = j.Job_ID
GROUP BY j.Job_ID, j.Job_Title
HAVING COUNT(a.Application_ID) >= 2
ORDER BY Applications DESC;
```

**Teaches:** `GROUP BY` + `HAVING` (filter after aggregation).

### Q14. Applications per branch

```sql
SELECT s.Branch, COUNT(a.Application_ID) AS Applications
FROM Student s
LEFT JOIN Application a ON a.Student_ID = s.Student_ID
GROUP BY s.Branch
ORDER BY Applications DESC;
```

**Expected (demo):** MCA 13, CSE 13, IT 11, ECE 6, and three branches with 0.
Total 43.

### Q15. Average and highest package per company

```sql
SELECT c.Company_Name,
       COUNT(p.Placement_ID)            AS Offers,
       ROUND(AVG(p.Package_Offered), 2) AS Avg_Package,
       MAX(p.Package_Offered)           AS Highest_Package
FROM Company c
JOIN Placement p ON p.Company_ID = c.Company_ID
GROUP BY c.Company_ID, c.Company_Name
ORDER BY Avg_Package DESC;
```

**Expected (demo):** FinEdge 10.50 average; GreenByte 7.67; CloudWorks 7.25;
DataBridge 8.00; TechNova 6.00.

### Q16. The single highest package and who received it

```sql
SELECT s.Name, s.Branch, c.Company_Name, p.Package_Offered
FROM Placement p
JOIN Student s ON s.Student_ID = p.Student_ID
JOIN Company c ON c.Company_ID = p.Company_ID
WHERE p.Package_Offered = (SELECT MAX(Package_Offered) FROM Placement);
```

**Teaches:** scalar subquery in `WHERE`. Returns Ishita Desai, 10.50 LPA.

### Q17. Second-highest package

```sql
SELECT MAX(Package_Offered) AS Second_Highest
FROM Placement
WHERE Package_Offered < (SELECT MAX(Package_Offered) FROM Placement);
```

**Teaches:** nested aggregate logic. Returns 9.00.

### Q18. Status funnel — one row per status

```sql
SELECT Status,
       COUNT(*) AS Total,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Application), 1) AS Percent
FROM Application
GROUP BY Status
ORDER BY Total DESC;
```

**Teaches:** aggregate plus scalar subquery; percentage of total.

### Q19. Applications per company with a shortlist rate

```sql
SELECT c.Company_Name,
       COUNT(a.Application_ID) AS Applications,
       SUM(a.Status = 'Shortlisted') AS Shortlisted,
       ROUND(SUM(a.Status = 'Shortlisted') * 100.0 /
             COUNT(a.Application_ID), 1) AS Shortlist_Rate
FROM Company c
JOIN Job j ON j.Company_ID = c.Company_ID
JOIN Application a ON a.Job_ID = j.Job_ID
GROUP BY c.Company_ID, c.Company_Name
ORDER BY Shortlist_Rate DESC;
```

**Teaches:** boolean expressions inside `SUM` (conditional aggregation).

### Q20. Companies ranked by confirmed selections

```sql
SELECT c.Company_Name,
       COUNT(p.Placement_ID) AS Confirmed_Offers
FROM Company c
JOIN Placement p ON p.Company_ID = c.Company_ID
WHERE p.Status IN ('Offer Accepted', 'Joined')
GROUP BY c.Company_ID, c.Company_Name
ORDER BY Confirmed_Offers DESC;
```

**Expected (demo):** TechNova 1, DataBridge 1, CloudWorks 2, FinEdge 1,
GreenByte 1 — six confirmed offers in total.

### Q21. Interview result counts and pass rate

```sql
SELECT Result,
       COUNT(*) AS Total,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Interview), 2) AS Percent
FROM Interview
GROUP BY Result
ORDER BY Total DESC;
```

**Expected (demo):** 32 Pass, 5 Pending, 1 Fail. Pass rate 84.21%.

### Q22. Average marks per round type

```sql
SELECT Round_Type,
       COUNT(*)                       AS Interviews,
       ROUND(AVG(Marks_Obtained), 2)  AS Avg_Marks,
       ROUND(AVG(Marks_Obtained * 100.0 / Max_Marks), 2) AS Avg_Percent
FROM (
    SELECT r.Round_Type, r.Max_Marks, i.Marks_Obtained
    FROM Recruitment_Round r
    JOIN Interview i ON i.Round_ID = r.Round_ID
    WHERE i.Marks_Obtained IS NOT NULL
) AS round_marks
GROUP BY Round_Type
ORDER BY Avg_Percent DESC;
```

**Teaches:** joining a measurement to its maximum and normalising it.

---

## D. Subqueries

### Q23. Students scoring above their own branch average

```sql
SELECT s.Name, s.Branch, s.CGPA
FROM Student s
WHERE s.CGPA > (
    SELECT AVG(s2.CGPA)
    FROM Student s2
    WHERE s2.Branch = s.Branch
)
ORDER BY s.Branch, s.CGPA DESC;
```

**Teaches:** correlated subquery. Returns 9 students.

### Q24. Students who have never applied to any job

```sql
SELECT s.Student_ID, s.Name, s.Branch
FROM Student s
WHERE NOT EXISTS (
    SELECT 1 FROM Application a WHERE a.Student_ID = s.Student_ID
);
```

**Expected (demo):** Karan Malhotra and Siddharth Kulkarni.

**Teaches:** `NOT EXISTS`; safer than `NOT IN` when `NULL`s are possible.

### Q25. Students who applied to at least one job from every company

```sql
SELECT s.Name
FROM Student s
WHERE NOT EXISTS (
    SELECT 1 FROM Company c
    WHERE NOT EXISTS (
        SELECT 1 FROM Application a
        JOIN Job j ON j.Job_ID = a.Job_ID
        WHERE a.Student_ID = s.Student_ID
          AND j.Company_ID = c.Company_ID
    )
);
```

**Teaches:** double `NOT EXISTS` (relational division). Demo result: no student
has applied to all five companies.

### Q26. Jobs whose package is above the overall average

```sql
SELECT Job_Title, Salary_Package
FROM Job
WHERE Salary_Package > (SELECT AVG(Salary_Package) FROM Job)
ORDER BY Salary_Package DESC;
```

**Teaches:** scalar subquery compared to a column.

### Q27. Students with more than one offer

```sql
SELECT s.Name, COUNT(*) AS Offers
FROM Placement p
JOIN Student s ON s.Student_ID = p.Student_ID
GROUP BY s.Student_ID, s.Name
HAVING COUNT(*) > 1;
```

**Expected (demo):** Priya Menon with 2 offers.

### Q28. Latest application date per student

```sql
SELECT s.Name, a.Application_Date, j.Job_Title
FROM Application a
JOIN Student s ON s.Student_ID = a.Student_ID
JOIN Job j ON j.Job_ID = a.Job_ID
WHERE a.Application_Date = (
    SELECT MAX(a2.Application_Date)
    FROM Application a2
    WHERE a2.Student_ID = a.Student_ID
)
ORDER BY a.Application_Date DESC;
```

**Teaches:** correlated subquery returning one row per student (ties included).

### Q29. Derived table: average number of applications per student

```sql
SELECT ROUND(AVG(Applications), 2) AS Avg_Applications
FROM (
    SELECT Student_ID, COUNT(*) AS Applications
    FROM Application
    GROUP BY Student_ID
) AS per_student;
```

**Teaches:** subquery in `FROM`. 43 applications over 18 applicants = 2.39.

---

## E. Set operations

### Q30. One combined list of students and companies (UNION)

```sql
SELECT Name AS Display_Name, 'Student' AS Kind FROM Student
UNION
SELECT Company_Name, 'Company' FROM Company
ORDER BY Kind, Display_Name;
```

**Teaches:** `UNION` removes duplicates and sorts the combined result.
Use `UNION ALL` when duplicates must be kept.

### Q31. Funnel snapshot with UNION ALL

```sql
SELECT 'Students'      AS Metric, COUNT(*) AS Total FROM Student
UNION ALL SELECT 'Companies',      COUNT(*) FROM Company
UNION ALL SELECT 'Jobs',           COUNT(*) FROM Job
UNION ALL SELECT 'Applications',   COUNT(*) FROM Application
UNION ALL SELECT 'Rounds',         COUNT(*) FROM Recruitment_Round
UNION ALL SELECT 'Interviews',     COUNT(*) FROM Interview
UNION ALL SELECT 'Placements',     COUNT(*) FROM Placement
UNION ALL SELECT 'Officers',       COUNT(*) FROM Placement_Officer
UNION ALL SELECT 'Reports',        COUNT(*) FROM Report;
```

**Teaches:** `UNION ALL` with a literal label column. This is the same
verification query at the end of `sample_data.sql`.

---

## F. Eligibility with `FIND_IN_SET`

### Q32. Students eligible for Job 1

```sql
SELECT s.Student_ID, s.Name, s.Branch, s.CGPA
FROM Student s
JOIN Job j ON j.Job_ID = 1
WHERE s.CGPA >= j.Min_CGPA
  AND (j.Eligible_Branch = 'All'
       OR FIND_IN_SET(s.Branch, j.Eligible_Branch) > 0)
ORDER BY s.CGPA DESC;
```

**Expected (demo):** 14 eligible students (Job 1 allows MCA, CSE, IT at
CGPA ≥ 7.00).

**Teaches:** `FIND_IN_SET` for a comma-separated list without a tenth table.

### Q33. Eligible students who have not applied to Job 1

```sql
SELECT s.Student_ID, s.Name, s.Branch, s.CGPA
FROM Student s
JOIN Job j ON j.Job_ID = 1
WHERE s.CGPA >= j.Min_CGPA
  AND (j.Eligible_Branch = 'All' OR FIND_IN_SET(s.Branch, j.Eligible_Branch) > 0)
  AND NOT EXISTS (
      SELECT 1 FROM Application a
      WHERE a.Student_ID = s.Student_ID AND a.Job_ID = 1
  )
ORDER BY s.CGPA DESC;
```

**Teaches:** eligibility + anti-join. This is the "eligible but not applied"
follow-up list the placement cell uses.

### Q34. How many eligible students each job has

```sql
SELECT j.Job_ID, j.Job_Title,
       COUNT(s.Student_ID) AS Eligible_Students
FROM Job j
LEFT JOIN Student s
       ON s.CGPA >= j.Min_CGPA
      AND (j.Eligible_Branch = 'All'
           OR FIND_IN_SET(s.Branch, j.Eligible_Branch) > 0)
GROUP BY j.Job_ID, j.Job_Title
ORDER BY Eligible_Students DESC;
```

**Teaches:** a non-equi join (inequality + function) inside `LEFT JOIN`.

---

## G. Views

### Q35. Job board with application counts

```sql
SELECT Job_ID, Job_Title, Company_Name, Salary_Package,
       Application_Count, Round_Count, Application_Deadline
FROM vw_job_details
ORDER BY Application_Deadline;
```

### Q36. Unplaced students

```sql
SELECT Student_ID, Name, Branch, CGPA, Email
FROM vw_unplaced_students
ORDER BY CGPA DESC;
```

**Expected (demo):** 14 students (20 minus 6 with accepted/joined offers).

### Q37. Branch performance view

```sql
SELECT * FROM vw_branch_placement_stats
ORDER BY Placement_Percentage DESC;
```

### Q38. Company selection statistics view

```sql
SELECT * FROM vw_company_selection_stats
ORDER BY Total_Selections DESC, Total_Applications DESC;
```

**Teaches:** views encapsulate complex joins and can be queried like tables.

---

## H. Stored function and procedures

### Q39. College placement percentage

```sql
SELECT fn_placement_percentage() AS Placement_Percentage;
```

**Expected (demo):** `30.00` (6 placed of 20 students).

The function counts only offers with status `Offer Accepted` or `Joined`, which
matches `global_stats()` in `app.py`.

### Q40. Eligible students for a job via procedure

```sql
CALL sp_eligible_students(1);
```

Returns the same 14 students as Q32 plus an `Applied` flag.

### Q41. Company selection summary via procedure

```sql
CALL sp_company_selection_summary();
```

Returns one row per company with jobs, applications, selections and average
package.

---

## I. Triggers

### Q42. Reject an offer whose company does not own the job

```sql
-- Job 5 belongs to Company 3, not Company 1.
INSERT INTO Placement
    (Student_ID, Job_ID, Company_ID, Placement_Date,
     Package_Offered, Joining_Date, Status)
VALUES (5, 5, 1, CURDATE(), 5.50, NULL, 'Offer Released');
```

**Expected error:** `SQLSTATE '45000'` with message
`Placement.Company_ID does not match the job company`.
The trigger `trg_placement_company_check` blocks the row.

### Q43. Reject an application after the deadline

```sql
-- Job 7 closed on 2026-10-30; today is later.
INSERT INTO Application (Student_ID, Job_ID, Application_Date, Status)
VALUES (1, 7, CURDATE(), 'Applied');
```

**Expected error:** `The application deadline for this job has passed`
(`trg_application_deadline_check`).

### Q44. Show that a trigger marks the application Selected

```sql
START TRANSACTION;

INSERT INTO Placement
    (Student_ID, Job_ID, Company_ID, Placement_Date,
     Package_Offered, Joining_Date, Status)
VALUES (5, 5, 3, CURDATE(), 5.50, NULL, 'Offer Released');

SELECT Application_ID, Student_ID, Job_ID, Status
FROM Application
WHERE Student_ID = 5 AND Job_ID = 5;
-- Status is now 'Selected' although only Placement was inserted.

ROLLBACK;
```

**Teaches:** `trg_placement_select_application` keeps the two tables consistent.

---

## J. Transactions

### Q45. All-or-nothing offer creation (the same logic as `create_placement`)

```sql
START TRANSACTION;

INSERT INTO Placement
    (Student_ID, Job_ID, Company_ID, Placement_Date,
     Package_Offered, Joining_Date, Status)
VALUES (5, 5, 3, CURDATE(), 5.50, '2027-06-30', 'Offer Released');

UPDATE Application
SET Status = 'Selected'
WHERE Student_ID = 5 AND Job_ID = 5;

-- Inspect before committing
SELECT * FROM Placement WHERE Student_ID = 5 AND Job_ID = 5;

COMMIT;     -- or ROLLBACK; to discard both changes
```

### Q46. Demonstrate rollback

```sql
START TRANSACTION;

DELETE FROM Student WHERE Student_ID = 14;   -- cascades to applications,
                                             -- interviews and placements
SELECT COUNT(*) AS Placements_Now FROM Placement;

ROLLBACK;
SELECT COUNT(*) AS Placements_Restored FROM Placement;  -- 10 again
```

**Teaches:** InnoDB transactions and `ON DELETE CASCADE`.

> Keep `START TRANSACTION ... ROLLBACK` around destructive demonstrations in a
> viva so the demo data stays intact.

---

## K. Window functions (MySQL 8)

### Q47. Rank students by CGPA inside each branch

```sql
SELECT Name, Branch, CGPA,
       RANK() OVER (PARTITION BY Branch ORDER BY CGPA DESC) AS Branch_Rank
FROM Student
ORDER BY Branch, Branch_Rank;
```

**Teaches:** `PARTITION BY` + `ORDER BY` inside an analytic function.

### Q48. Dense rank companies by number of offers

```sql
SELECT c.Company_Name,
       COUNT(p.Placement_ID) AS Offers,
       DENSE_RANK() OVER (ORDER BY COUNT(p.Placement_ID) DESC) AS Rank_No
FROM Company c
LEFT JOIN Placement p ON p.Company_ID = c.Company_ID
GROUP BY c.Company_ID, c.Company_Name
ORDER BY Rank_No;
```

**Teaches:** window function over an aggregate; `LEFT JOIN` keeps companies
with zero offers.

### Q49. Running total of applications by date

```sql
SELECT Application_Date,
       COUNT(*) AS Applied_Today,
       SUM(COUNT(*)) OVER (ORDER BY Application_Date) AS Running_Total
FROM Application
GROUP BY Application_Date
ORDER BY Application_Date;
```

**Teaches:** cumulative sum with a window frame (default `RANGE` frame).

### Q50. Each student's latest application using ROW_NUMBER

```sql
SELECT Student_ID, Name, Job_Title, Application_Date, Status
FROM (
    SELECT s.Student_ID, s.Name, j.Job_Title, a.Application_Date, a.Status,
           ROW_NUMBER() OVER (PARTITION BY s.Student_ID
                              ORDER BY a.Application_Date DESC, a.Application_ID DESC) AS rn
    FROM Application a
    JOIN Student s ON s.Student_ID = a.Student_ID
    JOIN Job j ON j.Job_ID = a.Job_ID
) AS ranked
WHERE rn = 1
ORDER BY Application_Date DESC;
```

**Teaches:** the top-N-per-group pattern.

---

## L. Data modification and constraint demonstrations

### Q51. Safe update of a student's CGPA

```sql
UPDATE Student
SET CGPA = 8.75
WHERE Student_ID = 1;

SELECT Student_ID, Name, CGPA FROM Student WHERE Student_ID = 1;
```

### Q52. CHECK constraint rejects an impossible CGPA

```sql
UPDATE Student SET CGPA = 12.00 WHERE Student_ID = 1;
```

**Expected error:** `Check constraint 'chk_student_cgpa' is violated.`
(MySQL error 3819). Restore with `UPDATE Student SET CGPA = 8.60 WHERE ...`.

### Q53. UNIQUE constraint rejects a duplicate application

```sql
INSERT INTO Application (Student_ID, Job_ID, Application_Date, Status)
VALUES (1, 1, CURDATE(), 'Applied');
```

**Expected error:** `Duplicate entry '1-1' for key 'uq_application_student_job'`
(error 1062). Aarav already applied to Job 1.

### Q54. FK RESTRICT protects offers

```sql
DELETE FROM Company WHERE Company_ID = 1;
```

**Expected error:** `Cannot delete or update a parent row: a foreign key
constraint fails` (error 1451), because placements and jobs reference the
company. This is why companies are rejected/deactivated instead of deleted.

### Q55. Cascading delete inside a transaction

```sql
START TRANSACTION;
SELECT COUNT(*) AS Apps_Before FROM Application WHERE Student_ID = 14;
DELETE FROM Student WHERE Student_ID = 14;
SELECT COUNT(*) AS Apps_After  FROM Application WHERE Student_ID = 14;  -- 0
SELECT COUNT(*) AS Interviews_After
FROM Interview i
JOIN Application a ON a.Application_ID = i.Application_ID
WHERE a.Student_ID = 14;                                                -- 0
ROLLBACK;
```

**Teaches:** `ON DELETE CASCADE` versus `RESTRICT`.

### Q56. Insert a new job as a recruiter would

```sql
INSERT INTO Job
    (Company_ID, Job_Title, Job_Description, Eligible_Branch,
     Min_CGPA, Salary_Package, Job_Location, Application_Deadline, Job_Type)
VALUES
    (1, 'Junior Python Developer',
     'Maintain internal Flask tools and write integration tests.',
     'MCA,CSE,IT', 7.00, 6.00, 'Pune', '2027-01-31', 'Full-Time');
```

**Teaches:** `INSERT` with enum and decimal values. The Flask form performs the
same insert with parameter placeholders.

---

## M. Reporting queries

### Q57. Complete placement report

```sql
SELECT s.Student_ID,
       s.Name            AS Student,
       s.Branch,
       s.CGPA,
       c.Company_Name,
       j.Job_Title,
       p.Package_Offered AS Package_LPA,
       p.Placement_Date,
       p.Joining_Date,
       p.Status
FROM Placement p
JOIN Student s ON s.Student_ID = p.Student_ID
JOIN Job j     ON j.Job_ID = p.Job_ID
JOIN Company c ON c.Company_ID = p.Company_ID
ORDER BY p.Package_Offered DESC;
```

**Teaches:** the core report behind the "Placement Summary" report type.
Returns 10 offer rows.

### Q58. Branch report with percentage and average package

```sql
SELECT s.Branch,
       COUNT(DISTINCT s.Student_ID) AS Students,
       COUNT(DISTINCT CASE WHEN p.Status IN ('Offer Accepted','Joined')
                           THEN p.Student_ID END) AS Placed,
       ROUND(COUNT(DISTINCT CASE WHEN p.Status IN ('Offer Accepted','Joined')
                                 THEN p.Student_ID END) * 100.0
             / COUNT(DISTINCT s.Student_ID), 2) AS Placement_Percent,
       ROUND(AVG(CASE WHEN p.Status IN ('Offer Accepted','Joined')
                      THEN p.Package_Offered END), 2) AS Avg_Package
FROM Student s
LEFT JOIN Placement p ON p.Student_ID = s.Student_ID
GROUP BY s.Branch
ORDER BY Placement_Percent DESC;
```

**Teaches:** conditional `COUNT(DISTINCT ...)` and `AVG(CASE ...)` — the same
math as `vw_branch_placement_stats`.

### Q59. Unplaced students who are still eligible for open jobs

```sql
SELECT s.Student_ID, s.Name, s.Branch, s.CGPA,
       COUNT(j.Job_ID) AS Open_Eligible_Jobs
FROM Student s
JOIN Job j
  ON j.Application_Deadline >= CURDATE()
 AND s.CGPA >= j.Min_CGPA
 AND (j.Eligible_Branch = 'All'
      OR FIND_IN_SET(s.Branch, j.Eligible_Branch) > 0)
WHERE NOT EXISTS (
    SELECT 1 FROM Placement p
    WHERE p.Student_ID = s.Student_ID
      AND p.Status IN ('Offer Accepted', 'Joined')
)
GROUP BY s.Student_ID, s.Name, s.Branch, s.CGPA
ORDER BY Open_Eligible_Jobs DESC, s.CGPA DESC;
```

**Teaches:** combines eligibility, open-job filtering and `NOT EXISTS` — a
realistic placement-cell follow-up report.

### Q60. Interview performance above the round average

```sql
SELECT s.Name, r.Round_Name, i.Marks_Obtained,
       ROUND((SELECT AVG(i2.Marks_Obtained)
              FROM Interview i2
              WHERE i2.Round_ID = i.Round_ID
                AND i2.Marks_Obtained IS NOT NULL), 2) AS Round_Average
FROM Interview i
JOIN Application a       ON a.Application_ID = i.Application_ID
JOIN Student s           ON s.Student_ID = a.Student_ID
JOIN Recruitment_Round r ON r.Round_ID = i.Round_ID
WHERE i.Marks_Obtained > (
    SELECT AVG(i2.Marks_Obtained)
    FROM Interview i2
    WHERE i2.Round_ID = i.Round_ID
      AND i2.Marks_Obtained IS NOT NULL
)
ORDER BY r.Round_Name, i.Marks_Obtained DESC;
```

**Teaches:** two correlated subqueries in one statement.

---

## Quick answer sheet for common viva questions

| Question | One-line answer |
|---|---|
| Why 9 tables? | The synopsis fixes the count; administrator lives in `Placement_Officer` via `Account_Role`. |
| Why is `Application` needed? | It resolves the many-to-many Student ↔ Job relationship and stores status/date. |
| Why is `Interview` needed? | It resolves Application ↔ Recruitment_Round and stores marks/result. |
| Where is the primary key of a bridge table? | `Application_ID` / `Interview_ID` surrogate keys, with a composite `UNIQUE` on the two parents. |
| How do you prevent two applications to the same job? | `UNIQUE (Student_ID, Job_ID)`. |
| How can one student hold two offers? | `Placement` is unique per `(Student_ID, Job_ID)`, not per student. |
| How is eligibility calculated? | `CGPA >= Min_CGPA` **and** (`Eligible_Branch = 'All'` or `FIND_IN_SET(Branch, Eligible_Branch)`). |
| Why `FIND_IN_SET`? | It queries a comma-separated list without adding a tenth table. |
| Which normal form? | 1NF, 2NF, 3NF; BCNF with two documented, trigger-protected denormalisations. |
| Which engine and why? | InnoDB — transactions, foreign keys, row-level locking. |
| Where are transactions used? | `create_placement()` and `delete_placement()` in `database.py`. |
| How are passwords stored? | PBKDF2-SHA256 hashes via Werkzeug; never plain text. |
| How is SQL injection prevented? | Every query uses `%s` parameters; no string concatenation. |
| How is role access enforced? | `@roles_required` compares the signed session role on the server. |
| Difference between `WHERE` and `HAVING`? | `WHERE` filters rows before grouping; `HAVING` filters groups after aggregation. |
| Difference between `NOT IN` and `NOT EXISTS`? | `NOT EXISTS` is NULL-safe and usually faster on large correlated sets. |
| What does `ON DELETE RESTRICT` protect? | Offers and audit reports from disappearing when a parent is deleted. |
| Why does `Placement` store `Company_ID`? | Fast company reports; triggers keep it consistent with `Job.Company_ID`. |
