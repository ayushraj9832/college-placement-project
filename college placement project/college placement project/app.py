import os
from datetime import date, datetime
from functools import wraps

from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from mysql.connector import Error as MySQLError
from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from database import create_placement, delete_placement, execute, query_all, query_one

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this-in-env")


BRANCHES = ["MCA", "CSE", "IT", "ECE", "EEE", "Mechanical", "Civil"]
JOB_TYPES = ["Full-Time", "Internship", "Internship + PPO", "Part-Time"]
APP_STATUSES = [
    "Applied", "Under Review", "Shortlisted", "Interview Scheduled",
    "Selected", "Rejected", "Withdrawn",
]
MANUAL_APP_STATUSES = [
    "Applied", "Under Review", "Shortlisted", "Interview Scheduled",
    "Rejected", "Withdrawn",
]
ROUND_TYPES = ["Aptitude", "Technical", "HR", "Group Discussion", "Coding", "Other"]
INTERVIEW_RESULTS = ["Pending", "Pass", "Fail", "On Hold"]
PLACEMENT_STATUSES = [
    "Offer Released", "Offer Accepted", "Offer Declined", "Joined", "Withdrawn",
]
REPORT_TYPES = [
    "Placement Summary", "Branch-wise Report", "Company-wise Report",
    "Unplaced Students", "Recruitment Summary", "Other",
]

ROLE_HOME = {
    "Student": "student_dashboard",
    "Recruiter": "recruiter_dashboard",
    "Officer": "officer_dashboard",
    "Admin": "admin_dashboard",
}
ROLE_LOGIN = {
    "Student": "student_login",
    "Recruiter": "recruiter_login",
    "Officer": "officer_login",
    "Admin": "admin_login",
}


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session or "role" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("index"))
            if session["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def is_eligible(student, job):
    cgpa = to_float(student.get("CGPA"))
    min_cgpa = to_float(job.get("Min_CGPA"))
    if cgpa < min_cgpa:
        return False

    allowed = (job.get("Eligible_Branch") or "All").split(",")
    allowed = [b.strip().lower() for b in allowed if b.strip()]
    if "all" in allowed:
        return True
    return (student.get("Branch") or "").strip().lower() in allowed


def normalize_branches(raw):
    parts = [p.strip().upper() for p in (raw or "").split(",") if p.strip()]
    if not parts or "ALL" in parts:
        return "All"
    return ",".join(dict.fromkeys(parts))


def invalid_branches(value):
    known = {b.upper() for b in BRANCHES}
    tokens = [p.strip() for p in (value or "").split(",") if p.strip()]
    return [t for t in tokens if t.upper() != "ALL" and t.upper() not in known]


def current_company():
    company = query_one(
        "SELECT * FROM Company WHERE Company_ID = %s", (session["user_id"],)
    )
    if not company:
        session.clear()
        abort(403)
    return company


def global_stats():
    students = query_one("SELECT COUNT(*) AS total FROM Student")["total"]
    companies = query_one(
        "SELECT COUNT(*) AS total FROM Company WHERE Approval_Status='Approved'"
    )["total"]
    jobs = query_one("SELECT COUNT(*) AS total FROM Job")["total"]
    applications = query_one("SELECT COUNT(*) AS total FROM Application")["total"]
    placed = query_one(
        """
        SELECT COUNT(DISTINCT Student_ID) AS total
        FROM Placement
        WHERE Status IN ('Offer Accepted','Joined')
        """
    )["total"]
    highest = query_one(
        """
        SELECT COALESCE(MAX(Package_Offered),0) AS value
        FROM Placement WHERE Status IN ('Offer Accepted','Joined')
        """
    )["value"]
    average = query_one(
        """
        SELECT COALESCE(ROUND(AVG(Package_Offered),2),0) AS value
        FROM Placement WHERE Status IN ('Offer Accepted','Joined')
        """
    )["value"]
    return {
        "students": students,
        "companies": companies,
        "jobs": jobs,
        "applications": applications,
        "placed": placed,
        "unplaced": max(students - placed, 0),
        "placement_rate": round(placed * 100 / students, 1) if students else 0,
        "highest": highest,
        "average": average,
    }


def branch_stats():
    return query_all(
        """
        SELECT s.Branch,
               COUNT(DISTINCT s.Student_ID) AS Total_Students,
               COUNT(DISTINCT CASE WHEN p.Status IN ('Offer Accepted','Joined')
                                   THEN p.Student_ID END) AS Placed_Students,
               COALESCE(ROUND(AVG(CASE WHEN p.Status IN ('Offer Accepted','Joined')
                                       THEN p.Package_Offered END), 2), 0) AS Avg_Package
        FROM Student s
        LEFT JOIN Placement p ON p.Student_ID = s.Student_ID
        GROUP BY s.Branch
        ORDER BY s.Branch
        """
    )


def company_stats():
    return query_all(
        """
        SELECT c.Company_ID, c.Company_Name,
               (SELECT COUNT(*) FROM Job j WHERE j.Company_ID = c.Company_ID) AS Jobs,
               (SELECT COUNT(*) FROM Application a
                 JOIN Job j ON j.Job_ID = a.Job_ID
                WHERE j.Company_ID = c.Company_ID) AS Applications,
               (SELECT COUNT(*) FROM Placement p
                WHERE p.Company_ID = c.Company_ID
                  AND p.Status IN ('Offer Accepted','Joined')) AS Selections,
               (SELECT COALESCE(ROUND(AVG(p.Package_Offered),2),0)
                  FROM Placement p
                 WHERE p.Company_ID = c.Company_ID
                   AND p.Status IN ('Offer Accepted','Joined')) AS Avg_Package
        FROM Company c
        ORDER BY Selections DESC, c.Company_Name
        """
    )


def status_chart(company_id=None):
    if company_id is None:
        rows = query_all(
            "SELECT Status, COUNT(*) AS Total FROM Application GROUP BY Status"
        )
    else:
        rows = query_all(
            """
            SELECT a.Status, COUNT(*) AS Total
            FROM Application a
            JOIN Job j ON j.Job_ID = a.Job_ID
            WHERE j.Company_ID = %s
            GROUP BY a.Status
            """,
            (company_id,),
        )
    return [r["Status"] for r in rows], [int(r["Total"]) for r in rows]


def build_report_data(report_type):
    summary, columns, rows = [], [], []

    if report_type == "Placement Summary":
        st = global_stats()
        summary = [
            {"label": "Total students", "value": st["students"]},
            {"label": "Placed students", "value": st["placed"]},
            {"label": "Placement percentage", "value": f"{st['placement_rate']}%"},
            {"label": "Average package", "value": f"{float(st['average']):.2f} LPA"},
            {"label": "Highest package", "value": f"{float(st['highest']):.2f} LPA"},
            {"label": "Participating companies", "value": st["companies"]},
        ]
        columns = ["Company", "Selections", "Average package (LPA)"]
        for row in company_stats():
            rows.append([row["Company_Name"], row["Selections"], row["Avg_Package"]])

    elif report_type == "Branch-wise Report":
        columns = ["Branch", "Students", "Placed", "Placement %", "Avg package (LPA)"]
        for row in branch_stats():
            total = int(row["Total_Students"] or 0)
            placed = int(row["Placed_Students"] or 0)
            pct = round(placed * 100 / total, 1) if total else 0
            rows.append([row["Branch"], total, placed, f"{pct}%", row["Avg_Package"]])

    elif report_type == "Company-wise Report":
        columns = ["Company", "Jobs", "Applications", "Selections", "Avg package (LPA)"]
        for row in company_stats():
            rows.append([
                row["Company_Name"], row["Jobs"], row["Applications"],
                row["Selections"], row["Avg_Package"],
            ])

    elif report_type == "Unplaced Students":
        columns = ["Student", "Branch", "CGPA", "Email", "Phone"]
        for row in query_all(
            """
            SELECT s.Name, s.Branch, s.CGPA, s.Email, s.Phone
            FROM Student s
            WHERE NOT EXISTS (
                SELECT 1 FROM Placement p
                WHERE p.Student_ID = s.Student_ID
                  AND p.Status IN ('Offer Accepted','Joined')
            )
            ORDER BY s.Branch, s.Name
            """
        ):
            rows.append([row["Name"], row["Branch"], row["CGPA"], row["Email"], row["Phone"]])

    elif report_type == "Recruitment Summary":
        columns = ["Application status", "Total"]
        for row in query_all(
            "SELECT Status, COUNT(*) AS Total FROM Application GROUP BY Status ORDER BY Total DESC"
        ):
            rows.append([row["Status"], row["Total"]])
        summary = [
            {"label": "Applications", "value": query_one("SELECT COUNT(*) AS c FROM Application")["c"]},
            {"label": "Recruitment rounds", "value": query_one("SELECT COUNT(*) AS c FROM Recruitment_Round")["c"]},
            {"label": "Interviews", "value": query_one("SELECT COUNT(*) AS c FROM Interview")["c"]},
            {"label": "Companies", "value": query_one("SELECT COUNT(*) AS c FROM Company")["c"]},
        ]

    return summary, columns, rows


@app.template_filter("money")
def money_filter(value):
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


@app.template_filter("dmy")
def dmy_filter(value):
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y, %I:%M %p")
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    return str(value)


@app.context_processor
def inject_globals():
    return {
        "today": date.today(),
        "current_role": session.get("role"),
        "current_name": session.get("name"),
        "BRANCHES": BRANCHES,
        "JOB_TYPES": JOB_TYPES,
        "APP_STATUSES": APP_STATUSES,
        "MANUAL_APP_STATUSES": MANUAL_APP_STATUSES,
        "ROUND_TYPES": ROUND_TYPES,
        "INTERVIEW_RESULTS": INTERVIEW_RESULTS,
        "PLACEMENT_STATUSES": PLACEMENT_STATUSES,
        "REPORT_TYPES": REPORT_TYPES,
    }


@app.route("/")
def index():
    st = global_stats()
    jobs = query_all(
        """
        SELECT j.*, c.Company_Name, c.Industry,
               (SELECT COUNT(*) FROM Application a WHERE a.Job_ID = j.Job_ID) AS Application_Count
        FROM Job j
        JOIN Company c ON c.Company_ID = j.Company_ID
        WHERE c.Approval_Status = 'Approved' AND j.Application_Deadline >= CURDATE()
        ORDER BY j.Job_ID DESC
        LIMIT 6
        """
    )
    companies = query_all(
        """
        SELECT c.*,
               (SELECT COUNT(*) FROM Job j WHERE j.Company_ID = c.Company_ID) AS Open_Jobs
        FROM Company c
        WHERE c.Approval_Status = 'Approved'
        ORDER BY c.Company_Name
        LIMIT 8
        """
    )
    return render_template("index.html", stats=st, jobs=jobs, companies=companies)


@app.route("/about")
def about():
    return render_template("about.html", stats=global_stats())


@app.route("/companies")
def public_companies():
    q = request.args.get("q", "").strip()
    sql = """
        SELECT c.*,
               (SELECT COUNT(*) FROM Job j WHERE j.Company_ID = c.Company_ID) AS Open_Jobs,
               (SELECT COUNT(*) FROM Placement p
                 WHERE p.Company_ID = c.Company_ID
                   AND p.Status IN ('Offer Accepted','Joined')) AS Selections
        FROM Company c
        WHERE c.Approval_Status = 'Approved'
    """
    params = []
    if q:
        sql += " AND (c.Company_Name LIKE %s OR c.Industry LIKE %s OR c.Location LIKE %s)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY c.Company_Name"
    return render_template("companies.html", companies=query_all(sql, params), q=q)


@app.route("/jobs")
def public_jobs():
    q = request.args.get("q", "").strip()
    branch = request.args.get("branch", "").strip()
    job_type = request.args.get("job_type", "").strip()

    sql = """
        SELECT j.*, c.Company_Name, c.Industry,
               (SELECT COUNT(*) FROM Application a WHERE a.Job_ID = j.Job_ID) AS Application_Count
        FROM Job j
        JOIN Company c ON c.Company_ID = j.Company_ID
        WHERE c.Approval_Status = 'Approved' AND j.Application_Deadline >= CURDATE()
    """
    params = []
    if q:
        sql += " AND (j.Job_Title LIKE %s OR c.Company_Name LIKE %s OR j.Job_Location LIKE %s)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if branch:
        sql += " AND (j.Eligible_Branch = 'All' OR FIND_IN_SET(%s, j.Eligible_Branch))"
        params.append(branch)
    if job_type:
        sql += " AND j.Job_Type = %s"
        params.append(job_type)
    sql += " ORDER BY j.Application_Deadline ASC"
    return render_template(
        "jobs.html", jobs=query_all(sql, params), q=q, branch=branch, job_type=job_type
    )


@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        student = query_one("SELECT * FROM Student WHERE Email = %s", (email,))
        if student and check_password_hash(student["Password_Hash"], password):
            session.clear()
            session.update(user_id=student["Student_ID"], role="Student",
                           name=student["Name"], email=student["Email"])
            flash(f"Welcome back, {student['Name']}!", "success")
            return redirect(url_for("student_dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/student_login.html")


@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        email = f.get("email", "").strip().lower()
        phone = f.get("phone", "").strip()
        password = f.get("password", "")
        confirm = f.get("confirm_password", "")
        dob = parse_date(f.get("date_of_birth"))
        gender = f.get("gender", "")
        branch = f.get("branch", "")
        batch = to_int(f.get("batch_year"))
        cgpa = to_float(f.get("cgpa"), -1)

        if not all([name, email, phone, password, dob, gender, branch]):
            flash("Please fill in all required fields.", "warning")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
        elif password != confirm:
            flash("Passwords do not match.", "warning")
        elif gender not in ("Male", "Female", "Other"):
            flash("Please choose a valid gender.", "warning")
        elif not (2000 <= batch <= 2100):
            flash("Please enter a valid batch year.", "warning")
        elif not (0 <= cgpa <= 10):
            flash("CGPA must be between 0 and 10.", "warning")
        else:
            try:
                execute(
                    """
                    INSERT INTO Student
                        (Name, Email, Phone, Password_Hash, Date_of_Birth,
                         Gender, Branch, Batch_Year, CGPA, Address)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (name, email, phone, generate_password_hash(password), dob,
                     gender, branch, batch, cgpa, f.get("address", "").strip()),
                )
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("student_login"))
            except IntegrityError:
                flash("That email or phone number is already registered.", "danger")
            except MySQLError:
                app.logger.exception("Student registration failed")
                flash("Could not create the account. Please try again.", "danger")
    return render_template("auth/student_register.html")


@app.route("/recruiter/login", methods=["GET", "POST"])
def recruiter_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        company = query_one("SELECT * FROM Company WHERE HR_Email = %s", (email,))
        if company and check_password_hash(company["Password_Hash"], password):
            if company["Approval_Status"] != "Approved":
                flash(
                    f"Your company account is {company['Approval_Status'].lower()}. "
                    "Please contact the placement cell.",
                    "warning",
                )
            else:
                session.clear()
                session.update(user_id=company["Company_ID"], role="Recruiter",
                               name=company["Company_Name"], email=company["HR_Email"])
                flash(f"Welcome, {company['Company_Name']}!", "success")
                return redirect(url_for("recruiter_dashboard"))
        else:
            flash("Invalid company email or password.", "danger")
    return render_template("auth/recruiter_login.html")


@app.route("/recruiter/register", methods=["GET", "POST"])
def recruiter_register():
    if request.method == "POST":
        f = request.form
        company_name = f.get("company_name", "").strip()
        industry = f.get("industry", "").strip()
        location = f.get("location", "").strip()
        hr_name = f.get("hr_name", "").strip()
        hr_email = f.get("hr_email", "").strip().lower()
        contact = f.get("contact_number", "").strip()
        website = f.get("website", "").strip()
        password = f.get("password", "")
        confirm = f.get("confirm_password", "")

        if not all([company_name, industry, location, hr_name, hr_email, contact, password]):
            flash("Please fill in all required fields.", "warning")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
        elif password != confirm:
            flash("Passwords do not match.", "warning")
        else:
            try:
                execute(
                    """
                    INSERT INTO Company
                        (Company_Name, Industry, Location, HR_Name, HR_Email,
                         Contact_Number, Website, Password_Hash, Approval_Status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Pending')
                    """,
                    (company_name, industry, location, hr_name, hr_email,
                     contact, website, generate_password_hash(password)),
                )
                flash(
                    "Company registered. The placement cell will review and approve "
                    "your account before you can post jobs.",
                    "success",
                )
                return redirect(url_for("recruiter_login"))
            except IntegrityError:
                flash("That company name or HR email is already registered.", "danger")
            except MySQLError:
                app.logger.exception("Company registration failed")
                flash("Could not create the company account. Please try again.", "danger")
    return render_template("auth/recruiter_register.html")


@app.route("/officer/login", methods=["GET", "POST"])
def officer_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        officer = query_one(
            "SELECT * FROM Placement_Officer WHERE Email=%s AND Account_Role='Officer'",
            (email,),
        )
        if officer and officer["Is_Active"] and check_password_hash(officer["Password_Hash"], password):
            session.clear()
            session.update(user_id=officer["Officer_ID"], role="Officer",
                           name=officer["Name"], email=officer["Email"])
            flash(f"Welcome, {officer['Name']}.", "success")
            return redirect(url_for("officer_dashboard"))
        flash("Invalid officer credentials or inactive account.", "danger")
    return render_template("auth/officer_login.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        admin = query_one(
            "SELECT * FROM Placement_Officer WHERE Email=%s AND Account_Role='Admin'",
            (email,),
        )
        if admin and admin["Is_Active"] and check_password_hash(admin["Password_Hash"], password):
            session.clear()
            session.update(user_id=admin["Officer_ID"], role="Admin",
                           name=admin["Name"], email=admin["Email"])
            flash("Administrator login successful.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid administrator credentials or inactive account.", "danger")
    return render_template("auth/admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/student/dashboard")
@roles_required("Student")
def student_dashboard():
    sid = session["user_id"]
    student = query_one("SELECT * FROM Student WHERE Student_ID = %s", (sid,))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    stats = {
        "applications": query_one(
            "SELECT COUNT(*) AS c FROM Application WHERE Student_ID=%s", (sid,)
        )["c"],
        "shortlisted": query_one(
            """SELECT COUNT(*) AS c FROM Application WHERE Student_ID=%s
               AND Status IN ('Shortlisted','Interview Scheduled')""", (sid,)
        )["c"],
        "interviews": query_one(
            """SELECT COUNT(*) AS c FROM Interview i
               JOIN Application a ON a.Application_ID=i.Application_ID
               WHERE a.Student_ID=%s AND i.Interview_Date >= NOW()""", (sid,)
        )["c"],
        "offers": query_one(
            """SELECT COUNT(*) AS c FROM Placement WHERE Student_ID=%s
               AND Status IN ('Offer Released','Offer Accepted','Joined')""", (sid,)
        )["c"],
    }
    applications = query_all(
        """
        SELECT a.*, j.Job_Title, j.Salary_Package, c.Company_Name
        FROM Application a
        JOIN Job j ON j.Job_ID = a.Job_ID
        JOIN Company c ON c.Company_ID = j.Company_ID
        WHERE a.Student_ID = %s
        ORDER BY a.Application_Date DESC, a.Application_ID DESC
        LIMIT 5
        """, (sid,),
    )
    interviews = query_all(
        """
        SELECT i.*, r.Round_Name, r.Round_Type, j.Job_Title, c.Company_Name
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID = i.Round_ID
        JOIN Application a ON a.Application_ID = i.Application_ID
        JOIN Job j ON j.Job_ID = a.Job_ID
        JOIN Company c ON c.Company_ID = j.Company_ID
        WHERE a.Student_ID = %s AND i.Interview_Date >= NOW()
        ORDER BY i.Interview_Date ASC
        LIMIT 5
        """, (sid,),
    )
    placement = query_one(
        """
        SELECT p.*, j.Job_Title, c.Company_Name
        FROM Placement p
        JOIN Job j ON j.Job_ID = p.Job_ID
        JOIN Company c ON c.Company_ID = p.Company_ID
        WHERE p.Student_ID = %s
        ORDER BY p.Package_Offered DESC
        LIMIT 1
        """, (sid,),
    )
    status_rows = query_all(
        "SELECT Status, COUNT(*) AS Total FROM Application WHERE Student_ID=%s GROUP BY Status",
        (sid,),
    )
    status_labels = [r["Status"] for r in status_rows]
    status_values = [int(r["Total"]) for r in status_rows]
    return render_template(
        "student/dashboard.html", student=student, stats=stats,
        applications=applications, interviews=interviews, placement=placement,
        status_labels=status_labels, status_values=status_values,
    )


@app.route("/student/profile", methods=["GET", "POST"])
@roles_required("Student")
def student_profile():
    sid = session["user_id"]
    student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (sid,))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        phone = f.get("phone", "").strip()
        dob = parse_date(f.get("date_of_birth"))
        gender = f.get("gender", "")
        branch = f.get("branch", "")
        batch = to_int(f.get("batch_year"))
        cgpa = to_float(f.get("cgpa"), -1)

        if not all([name, phone, dob, gender, branch]):
            flash("Please fill in all required fields.", "warning")
        elif not (2000 <= batch <= 2100):
            flash("Please enter a valid batch year.", "warning")
        elif not (0 <= cgpa <= 10):
            flash("CGPA must be between 0 and 10.", "warning")
        else:
            try:
                execute(
                    """
                    UPDATE Student
                    SET Name=%s, Phone=%s, Date_of_Birth=%s, Gender=%s,
                        Branch=%s, Batch_Year=%s, CGPA=%s, Address=%s
                    WHERE Student_ID=%s
                    """,
                    (name, phone, dob, gender, branch, batch, cgpa,
                     f.get("address", "").strip(), sid),
                )
                session["name"] = name
                flash("Profile updated successfully.", "success")
                return redirect(url_for("student_profile"))
            except IntegrityError:
                flash("That phone number is already used by another student.", "danger")
            except MySQLError:
                app.logger.exception("Profile update failed")
                flash("Could not update the profile.", "danger")
        student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (sid,))
    return render_template("student/profile.html", student=student)


@app.route("/student/companies")
@roles_required("Student")
def student_companies():
    companies = query_all(
        """
        SELECT c.*,
               (SELECT COUNT(*) FROM Job j WHERE j.Company_ID=c.Company_ID) AS Open_Jobs,
               (SELECT COUNT(*) FROM Placement p WHERE p.Company_ID=c.Company_ID
                 AND p.Status IN ('Offer Accepted','Joined')) AS Selections
        FROM Company c
        WHERE c.Approval_Status='Approved'
        ORDER BY c.Company_Name
        """
    )
    return render_template("student/companies.html", companies=companies)


@app.route("/student/jobs")
@roles_required("Student")
def student_jobs():
    sid = session["user_id"]
    student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (sid,))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    q = request.args.get("q", "").strip()
    branch = request.args.get("branch", "").strip()
    eligible_only = request.args.get("eligible") == "1"

    sql = """
        SELECT j.*, c.Company_Name, c.Industry, c.Location AS Company_Location,
               (SELECT COUNT(*) FROM Application a WHERE a.Job_ID=j.Job_ID) AS Application_Count,
               EXISTS(SELECT 1 FROM Application a
                      WHERE a.Job_ID=j.Job_ID AND a.Student_ID=%s) AS Has_Applied
        FROM Job j
        JOIN Company c ON c.Company_ID = j.Company_ID
        WHERE c.Approval_Status='Approved'
          AND j.Application_Deadline >= CURDATE()
    """
    params = [sid]
    if q:
        sql += " AND (j.Job_Title LIKE %s OR c.Company_Name LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    if branch:
        sql += " AND (j.Eligible_Branch='All' OR FIND_IN_SET(%s, j.Eligible_Branch))"
        params.append(branch)
    sql += " ORDER BY j.Application_Deadline ASC"
    jobs = query_all(sql, params)
    for job in jobs:
        job["Eligible"] = is_eligible(student, job)
    if eligible_only:
        jobs = [j for j in jobs if j["Eligible"]]

    return render_template(
        "student/jobs.html", student=student, jobs=jobs,
        q=q, branch=branch, eligible_only=eligible_only,
    )


@app.route("/student/jobs/<int:job_id>")
@roles_required("Student")
def student_job_detail(job_id):
    sid = session["user_id"]
    student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (sid,))
    job = query_one(
        """
        SELECT j.*, c.Company_Name, c.Industry, c.Location AS Company_Location,
               c.Website, c.Approval_Status,
               (SELECT COUNT(*) FROM Application a WHERE a.Job_ID=j.Job_ID) AS Application_Count
        FROM Job j JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE j.Job_ID=%s
        """, (job_id,),
    )
    if not job or job["Approval_Status"] != "Approved":
        abort(404)
    application = query_one(
        "SELECT * FROM Application WHERE Student_ID=%s AND Job_ID=%s", (sid, job_id)
    )
    rounds = query_all(
        "SELECT * FROM Recruitment_Round WHERE Job_ID=%s ORDER BY Round_Date, Round_ID",
        (job_id,),
    )
    interviews = []
    if application:
        interviews = query_all(
            """
            SELECT i.*, r.Round_Name, r.Round_Type
            FROM Interview i JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
            WHERE i.Application_ID=%s ORDER BY i.Interview_Date
            """, (application["Application_ID"],),
        )
    return render_template(
        "student/job_detail.html", student=student, job=job,
        eligible=is_eligible(student, job), application=application,
        rounds=rounds, interviews=interviews,
        is_open=job["Application_Deadline"] >= date.today(),
    )


@app.route("/student/apply/<int:job_id>", methods=["POST"])
@roles_required("Student")
def student_apply(job_id):
    sid = session["user_id"]
    student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (sid,))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))
    job = query_one(
        """
        SELECT j.*, c.Approval_Status
        FROM Job j JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE j.Job_ID=%s
        """, (job_id,),
    )
    if not job or job["Approval_Status"] != "Approved":
        abort(404)
    existing = query_one(
        "SELECT Application_ID, Status FROM Application WHERE Student_ID=%s AND Job_ID=%s",
        (sid, job_id),
    )
    if job["Application_Deadline"] < date.today():
        flash("The application deadline for this job has passed.", "warning")
    elif not is_eligible(student, job):
        flash("You do not meet the eligibility criteria for this job.", "warning")
    elif existing and existing["Status"] == "Withdrawn":
        flash("You withdrew this application, so it cannot be submitted again.", "info")
    elif existing:
        flash("You have already applied for this job.", "info")
    elif query_one(
        """SELECT Placement_ID FROM Placement
           WHERE Student_ID=%s AND Status IN ('Offer Accepted','Joined') LIMIT 1""",
        (sid,),
    ):
        flash("You have already accepted a placement offer, so new applications are closed.", "info")
    else:
        try:
            execute(
                "INSERT INTO Application (Student_ID, Job_ID, Status) VALUES (%s,%s,'Applied')",
                (sid, job_id),
            )
            flash("Application submitted successfully.", "success")
        except IntegrityError:
            flash("You have already applied for this job.", "warning")
        except MySQLError:
            app.logger.exception("Application insert failed")
            flash("Could not submit the application.", "danger")
    return redirect(url_for("student_job_detail", job_id=job_id))


@app.route("/student/applications")
@roles_required("Student")
def student_applications():
    applications = query_all(
        """
        SELECT a.*, j.Job_Title, j.Salary_Package, j.Job_Location,
               c.Company_Name,
               (SELECT COUNT(*) FROM Interview i
                 WHERE i.Application_ID=a.Application_ID) AS Interview_Count,
               (SELECT i.Result FROM Interview i
                 WHERE i.Application_ID=a.Application_ID
                 ORDER BY i.Interview_Date DESC LIMIT 1) AS Last_Result,
               p.Status AS Placement_Status, p.Package_Offered
        FROM Application a
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        LEFT JOIN Placement p ON p.Student_ID=a.Student_ID AND p.Job_ID=a.Job_ID
        WHERE a.Student_ID=%s
        ORDER BY a.Application_Date DESC, a.Application_ID DESC
        """, (session["user_id"],),
    )
    return render_template("student/applications.html", applications=applications)


@app.route("/student/applications/<int:application_id>/withdraw", methods=["POST"])
@roles_required("Student")
def student_application_withdraw(application_id):
    application = query_one(
        "SELECT * FROM Application WHERE Application_ID=%s AND Student_ID=%s",
        (application_id, session["user_id"]),
    )
    if not application:
        abort(404)

    if application["Status"] in ("Selected", "Withdrawn", "Rejected"):
        flash("This application can no longer be withdrawn.", "warning")
        return redirect(url_for("student_applications"))

    try:
        execute(
            "UPDATE Application SET Status='Withdrawn' WHERE Application_ID=%s",
            (application_id,),
        )
    except MySQLError:
        flash("Could not withdraw the application. Please try again.", "danger")
    else:
        flash("Application withdrawn.", "info")
    return redirect(url_for("student_applications"))


@app.route("/student/interviews")
@roles_required("Student")
def student_interviews():
    rows = query_all(
        """
        SELECT i.*, r.Round_Name, r.Round_Type, r.Max_Marks,
               j.Job_Title, c.Company_Name
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        JOIN Application a ON a.Application_ID=i.Application_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE a.Student_ID=%s
        ORDER BY i.Interview_Date DESC
        """, (session["user_id"],),
    )
    now = datetime.now()
    upcoming = [r for r in rows if r["Interview_Date"] >= now]
    past = [r for r in rows if r["Interview_Date"] < now]
    return render_template("student/interviews.html", upcoming=upcoming, past=past)


@app.route("/student/placements")
@roles_required("Student")
def student_placements():
    placements = query_all(
        """
        SELECT p.*, j.Job_Title, j.Job_Type, c.Company_Name, c.Location AS Company_Location
        FROM Placement p
        JOIN Job j ON j.Job_ID=p.Job_ID
        JOIN Company c ON c.Company_ID=p.Company_ID
        WHERE p.Student_ID=%s
        ORDER BY p.Placement_Date DESC
        """, (session["user_id"],),
    )
    return render_template("student/placements.html", placements=placements)


@app.route("/student/placements/<int:placement_id>/status", methods=["POST"])
@roles_required("Student")
def student_placement_status(placement_id):
    status = request.form.get("status", "")
    if status not in ("Offer Accepted", "Offer Declined"):
        flash("Choose either Accept or Decline for an offer.", "warning")
        return redirect(url_for("student_placements"))

    placement = query_one(
        "SELECT * FROM Placement WHERE Placement_ID=%s AND Student_ID=%s",
        (placement_id, session["user_id"]),
    )
    if not placement:
        abort(404)
    if placement["Status"] != "Offer Released":
        flash("This offer has already been answered.", "warning")
        return redirect(url_for("student_placements"))

    try:
        execute(
            "UPDATE Placement SET Status=%s WHERE Placement_ID=%s",
            (status, placement_id),
        )
    except MySQLError:
        flash("Could not update the offer. Please try again.", "danger")
    else:
        if status == "Offer Accepted":
            flash("Offer accepted. The placement cell will contact you about joining.", "success")
        else:
            flash("Offer declined. Your other applications are unaffected.", "info")
    return redirect(url_for("student_placements"))


@app.route("/recruiter/dashboard")
@roles_required("Recruiter")
def recruiter_dashboard():
    cid = session["user_id"]
    company = current_company()
    stats = {
        "jobs": query_one("SELECT COUNT(*) AS c FROM Job WHERE Company_ID=%s", (cid,))["c"],
        "applications": query_one(
            """SELECT COUNT(*) AS c FROM Application a
               JOIN Job j ON j.Job_ID=a.Job_ID WHERE j.Company_ID=%s""", (cid,)
        )["c"],
        "shortlisted": query_one(
            """SELECT COUNT(*) AS c FROM Application a
               JOIN Job j ON j.Job_ID=a.Job_ID
               WHERE j.Company_ID=%s AND a.Status IN ('Shortlisted','Interview Scheduled')""",
            (cid,),
        )["c"],
        "selected": query_one(
            """SELECT COUNT(*) AS c FROM Application a
               JOIN Job j ON j.Job_ID=a.Job_ID
               WHERE j.Company_ID=%s AND a.Status='Selected'""", (cid,)
        )["c"],
    }
    applications = query_all(
        """
        SELECT a.*, s.Name AS Student_Name, s.Branch, s.CGPA, j.Job_Title
        FROM Application a
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        WHERE j.Company_ID=%s
        ORDER BY a.Application_Date DESC, a.Application_ID DESC
        LIMIT 6
        """, (cid,),
    )
    interviews = query_all(
        """
        SELECT i.*, r.Round_Name, s.Name AS Student_Name, j.Job_Title
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        JOIN Application a ON a.Application_ID=i.Application_ID
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        WHERE j.Company_ID=%s AND i.Interview_Date >= NOW()
        ORDER BY i.Interview_Date ASC LIMIT 5
        """, (cid,),
    )
    jobs = query_all(
        """SELECT j.*, (SELECT COUNT(*) FROM Application a WHERE a.Job_ID=j.Job_ID) AS Application_Count
           FROM Job j WHERE j.Company_ID=%s ORDER BY j.Job_ID DESC LIMIT 4""", (cid,)
    )
    labels, values = status_chart(cid)
    return render_template(
        "recruiter/dashboard.html", company=company, stats=stats,
        applications=applications, interviews=interviews, jobs=jobs,
        status_labels=labels, status_values=values,
    )


@app.route("/recruiter/profile", methods=["GET", "POST"])
@roles_required("Recruiter")
def recruiter_profile():
    cid = session["user_id"]
    company = current_company()
    if request.method == "POST":
        f = request.form
        name = f.get("company_name", "").strip()
        industry = f.get("industry", "").strip()
        location = f.get("location", "").strip()
        hr_name = f.get("hr_name", "").strip()
        hr_email = f.get("hr_email", "").strip().lower()
        contact = f.get("contact_number", "").strip()
        website = f.get("website", "").strip()
        if not all([name, industry, location, hr_name, hr_email, contact]):
            flash("Please fill in all required fields.", "warning")
        else:
            try:
                execute(
                    """
                    UPDATE Company
                    SET Company_Name=%s, Industry=%s, Location=%s, HR_Name=%s,
                        HR_Email=%s, Contact_Number=%s, Website=%s
                    WHERE Company_ID=%s
                    """,
                    (name, industry, location, hr_name, hr_email, contact, website, cid),
                )
                session["name"] = name
                session["email"] = hr_email
                flash("Company profile updated.", "success")
                return redirect(url_for("recruiter_profile"))
            except IntegrityError:
                flash("That company name or HR email is already in use.", "danger")
            except MySQLError:
                app.logger.exception("Company profile update failed")
                flash("Could not update the company profile.", "danger")
        company = current_company()
    return render_template("recruiter/profile.html", company=company)


@app.route("/recruiter/jobs")
@roles_required("Recruiter")
def recruiter_jobs():
    jobs = query_all(
        """
        SELECT j.*,
               (SELECT COUNT(*) FROM Application a WHERE a.Job_ID=j.Job_ID) AS Application_Count,
               (SELECT COUNT(*) FROM Application a WHERE a.Job_ID=j.Job_ID
                 AND a.Status='Selected') AS Selected_Count,
               (SELECT COUNT(*) FROM Recruitment_Round r WHERE r.Job_ID=j.Job_ID) AS Round_Count
        FROM Job j
        WHERE j.Company_ID=%s
        ORDER BY j.Job_ID DESC
        """, (session["user_id"],),
    )
    return render_template("recruiter/jobs.html", jobs=jobs, company=current_company())


def _job_form_values(form):
    return {
        "title": form.get("job_title", "").strip(),
        "description": form.get("job_description", "").strip(),
        "eligible": normalize_branches(form.get("eligible_branch", "All")),
        "min_cgpa": to_float(form.get("min_cgpa"), -1),
        "salary": to_float(form.get("salary_package"), -1),
        "location": form.get("job_location", "").strip(),
        "deadline": parse_date(form.get("application_deadline")),
        "job_type": form.get("job_type", "Full-Time"),
    }


@app.route("/recruiter/jobs/new", methods=["GET", "POST"])
@roles_required("Recruiter")
def recruiter_job_new():
    company = current_company()
    if company["Approval_Status"] != "Approved":
        flash("Your company must be approved before posting jobs.", "warning")
        return redirect(url_for("recruiter_dashboard"))

    if request.method == "POST":
        v = _job_form_values(request.form)
        if not all([v["title"], v["description"], v["location"], v["deadline"]]):
            flash("Please fill in all required fields.", "warning")
        elif invalid_branches(v["eligible"]):
            flash(
                "Unknown branch in the eligibility list. Use All or a comma-separated "
                "subset of: " + ", ".join(BRANCHES) + ".",
                "warning",
            )
        elif v["deadline"] < date.today():
            flash("The application deadline cannot be in the past.", "warning")
        elif not (0 <= v["min_cgpa"] <= 10):
            flash("Minimum CGPA must be between 0 and 10.", "warning")
        elif v["salary"] < 0:
            flash("Salary package cannot be negative.", "warning")
        elif v["job_type"] not in JOB_TYPES:
            flash("Please choose a valid job type.", "warning")
        else:
            try:
                execute(
                    """
                    INSERT INTO Job
                        (Company_ID, Job_Title, Job_Description, Eligible_Branch,
                         Min_CGPA, Salary_Package, Job_Location,
                         Application_Deadline, Job_Type)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (session["user_id"], v["title"], v["description"], v["eligible"],
                     v["min_cgpa"], v["salary"], v["location"], v["deadline"], v["job_type"]),
                )
                flash("Job opening published.", "success")
                return redirect(url_for("recruiter_jobs"))
            except MySQLError:
                app.logger.exception("Job insert failed")
                flash("Could not publish the job opening.", "danger")
    return render_template("recruiter/job_form.html", job=None, mode="new")


@app.route("/recruiter/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@roles_required("Recruiter")
def recruiter_job_edit(job_id):
    cid = session["user_id"]
    job = query_one("SELECT * FROM Job WHERE Job_ID=%s AND Company_ID=%s", (job_id, cid))
    if not job:
        abort(404)

    if request.method == "POST":
        v = _job_form_values(request.form)
        if not all([v["title"], v["description"], v["location"], v["deadline"]]):
            flash("Please fill in all required fields.", "warning")
        elif invalid_branches(v["eligible"]):
            flash(
                "Unknown branch in the eligibility list. Use All or a comma-separated "
                "subset of: " + ", ".join(BRANCHES) + ".",
                "warning",
            )
        elif not (0 <= v["min_cgpa"] <= 10):
            flash("Minimum CGPA must be between 0 and 10.", "warning")
        elif v["salary"] < 0:
            flash("Salary package cannot be negative.", "warning")
        elif v["job_type"] not in JOB_TYPES:
            flash("Please choose a valid job type.", "warning")
        else:
            try:
                execute(
                    """
                    UPDATE Job
                    SET Job_Title=%s, Job_Description=%s, Eligible_Branch=%s,
                        Min_CGPA=%s, Salary_Package=%s, Job_Location=%s,
                        Application_Deadline=%s, Job_Type=%s
                    WHERE Job_ID=%s AND Company_ID=%s
                    """,
                    (v["title"], v["description"], v["eligible"], v["min_cgpa"],
                     v["salary"], v["location"], v["deadline"], v["job_type"],
                     job_id, cid),
                )
                flash("Job opening updated.", "success")
                return redirect(url_for("recruiter_jobs"))
            except MySQLError:
                app.logger.exception("Job update failed")
                flash("Could not update the job opening.", "danger")
    return render_template("recruiter/job_form.html", job=job, mode="edit")


@app.route("/recruiter/jobs/<int:job_id>/delete", methods=["POST"])
@roles_required("Recruiter")
def recruiter_job_delete(job_id):
    try:
        _, rowcount = execute(
            "DELETE FROM Job WHERE Job_ID=%s AND Company_ID=%s",
            (job_id, session["user_id"]),
        )
        flash("Job opening deleted." if rowcount else "Job not found.", "success" if rowcount else "warning")
    except IntegrityError:
        flash("This job has placement records and cannot be deleted. Close it by editing the deadline instead.", "danger")
    except MySQLError:
        app.logger.exception("Job delete failed")
        flash("Could not delete the job opening.", "danger")
    return redirect(url_for("recruiter_jobs"))


@app.route("/recruiter/jobs/<int:job_id>/applicants")
@roles_required("Recruiter")
def recruiter_applicants(job_id):
    cid = session["user_id"]
    job = query_one("SELECT * FROM Job WHERE Job_ID=%s AND Company_ID=%s", (job_id, cid))
    if not job:
        abort(404)

    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()
    sql = """
        SELECT a.*, s.Student_ID, s.Name AS Student_Name, s.Email, s.Phone,
               s.Branch, s.Batch_Year, s.CGPA,
               (SELECT COUNT(*) FROM Interview i
                 WHERE i.Application_ID=a.Application_ID) AS Interview_Count,
               (SELECT p.Status FROM Placement p
                 WHERE p.Student_ID=a.Student_ID AND p.Job_ID=a.Job_ID
                 LIMIT 1) AS Offer_Status
        FROM Application a
        JOIN Student s ON s.Student_ID=a.Student_ID
        WHERE a.Job_ID=%s
    """
    params = [job_id]
    if status:
        sql += " AND a.Status=%s"
        params.append(status)
    if q:
        sql += " AND (s.Name LIKE %s OR s.Email LIKE %s OR s.Branch LIKE %s)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY s.CGPA DESC, a.Application_Date"
    applicants = query_all(sql, params)
    return render_template(
        "recruiter/applicants.html", job=job, applicants=applicants,
        status=status, q=q,
    )


@app.route("/recruiter/applications/<int:application_id>/status", methods=["POST"])
@roles_required("Recruiter")
def recruiter_application_status(application_id):
    status = request.form.get("status", "")
    if status not in MANUAL_APP_STATUSES:
        flash("Invalid application status.", "warning")
        return redirect(request.referrer or url_for("recruiter_jobs"))

    application = query_one(
        """
        SELECT a.Application_ID, a.Student_ID, a.Job_ID
        FROM Application a
        JOIN Job j ON j.Job_ID=a.Job_ID
        WHERE a.Application_ID=%s AND j.Company_ID=%s
        """,
        (application_id, session["user_id"]),
    )
    if not application:
        flash("Application not found.", "warning")
        return redirect(request.referrer or url_for("recruiter_jobs"))

    if query_one(
        "SELECT Placement_ID FROM Placement WHERE Student_ID=%s AND Job_ID=%s",
        (application["Student_ID"], application["Job_ID"]),
    ):
        flash(
            "This application already has an offer. Update the offer from the Placements page instead.",
            "warning",
        )
        return redirect(request.referrer or url_for("recruiter_jobs"))

    try:
        execute(
            "UPDATE Application SET Status=%s WHERE Application_ID=%s",
            (status, application_id),
        )
        flash("Application status updated.", "success")
    except MySQLError:
        app.logger.exception("Status update failed")
        flash("Could not update the application status.", "danger")
    return redirect(request.referrer or url_for("recruiter_jobs"))


@app.route("/recruiter/jobs/<int:job_id>/rounds", methods=["GET", "POST"])
@roles_required("Recruiter")
def recruiter_rounds(job_id):
    cid = session["user_id"]
    job = query_one("SELECT * FROM Job WHERE Job_ID=%s AND Company_ID=%s", (job_id, cid))
    if not job:
        abort(404)

    if request.method == "POST":
        name = request.form.get("round_name", "").strip()
        rtype = request.form.get("round_type", "")
        rdate = parse_date(request.form.get("round_date"))
        max_marks = to_float(request.form.get("max_marks"), 0)
        if not name or not rdate or rtype not in ROUND_TYPES:
            flash("Please complete the round details.", "warning")
        elif max_marks <= 0:
            flash("Maximum marks must be greater than zero.", "warning")
        else:
            try:
                execute(
                    """
                    INSERT INTO Recruitment_Round
                        (Job_ID, Round_Name, Round_Type, Round_Date, Max_Marks)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (job_id, name, rtype, rdate, max_marks),
                )
                flash("Recruitment round added.", "success")
                return redirect(url_for("recruiter_rounds", job_id=job_id))
            except IntegrityError:
                flash("A round with that name already exists for this job.", "danger")
            except MySQLError:
                app.logger.exception("Round insert failed")
                flash("Could not add the round.", "danger")

    rounds = query_all(
        """
        SELECT r.*, (SELECT COUNT(*) FROM Interview i WHERE i.Round_ID=r.Round_ID) AS Interview_Count
        FROM Recruitment_Round r WHERE r.Job_ID=%s ORDER BY r.Round_Date, r.Round_ID
        """, (job_id,),
    )
    return render_template("recruiter/rounds.html", job=job, rounds=rounds)


@app.route("/recruiter/rounds/<int:round_id>/delete", methods=["POST"])
@roles_required("Recruiter")
def recruiter_round_delete(round_id):
    try:
        _, rowcount = execute(
            """
            DELETE r FROM Recruitment_Round r
            JOIN Job j ON j.Job_ID=r.Job_ID
            WHERE r.Round_ID=%s AND j.Company_ID=%s
            """, (round_id, session["user_id"]),
        )
        flash("Round deleted." if rowcount else "Round not found.", "success" if rowcount else "warning")
    except MySQLError:
        app.logger.exception("Round delete failed")
        flash("Could not delete the round.", "danger")
    return redirect(request.referrer or url_for("recruiter_jobs"))


@app.route("/recruiter/applications/<int:application_id>/interview", methods=["GET", "POST"])
@roles_required("Recruiter")
def recruiter_interview_new(application_id):
    cid = session["user_id"]
    application = query_one(
        """
        SELECT a.*, s.Name AS Student_Name, s.Branch, s.CGPA,
               j.Job_ID, j.Job_Title, c.Company_Name
        FROM Application a
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE a.Application_ID=%s AND j.Company_ID=%s
        """, (application_id, cid),
    )
    if not application:
        abort(404)

    rounds = query_all(
        """
        SELECT r.* FROM Recruitment_Round r
        WHERE r.Job_ID=%s AND NOT EXISTS (
            SELECT 1 FROM Interview i
            WHERE i.Round_ID=r.Round_ID AND i.Application_ID=%s
        )
        ORDER BY r.Round_Date, r.Round_ID
        """, (application["Job_ID"], application_id),
    )
    existing = query_all(
        """
        SELECT i.*, r.Round_Name FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        WHERE i.Application_ID=%s ORDER BY i.Interview_Date
        """, (application_id,),
    )

    if request.method == "POST":
        round_id = to_int(request.form.get("round_id"))
        when = parse_datetime(request.form.get("interview_date"))
        interviewer = request.form.get("interviewer_name", "").strip()
        result = request.form.get("result", "Pending")
        marks_raw = request.form.get("marks_obtained", "").strip()
        marks = to_float(marks_raw, -1) if marks_raw else None
        remarks = request.form.get("remarks", "").strip()

        round_row = query_one(
            "SELECT * FROM Recruitment_Round WHERE Round_ID=%s AND Job_ID=%s",
            (round_id, application["Job_ID"]),
        )
        if not round_row:
            flash("Please choose a valid round for this job.", "warning")
        elif not when or not interviewer:
            flash("Interview date and interviewer name are required.", "warning")
        elif result not in INTERVIEW_RESULTS:
            flash("Invalid interview result.", "warning")
        elif marks is not None and (marks < 0 or marks > float(round_row["Max_Marks"])):
            flash(f"Marks must be between 0 and {round_row['Max_Marks']}.", "warning")
        else:
            try:
                execute(
                    """
                    INSERT INTO Interview
                        (Application_ID, Round_ID, Interview_Date, Result,
                         Interviewer_Name, Marks_Obtained, Remarks)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (application_id, round_id, when, result,
                          interviewer, marks, remarks),
                )
                execute(
                    """
                    UPDATE Application SET Status='Interview Scheduled'
                    WHERE Application_ID=%s
                      AND Status IN ('Applied','Under Review','Shortlisted')
                    """, (application_id,),
                )
                flash("Interview scheduled.", "success")
                return redirect(url_for("recruiter_applicants", job_id=application["Job_ID"]))
            except IntegrityError:
                flash("An interview for this application and round already exists.", "danger")
            except MySQLError:
                app.logger.exception("Interview insert failed")
                flash("Could not schedule the interview.", "danger")

    return render_template(
        "recruiter/interview_form.html", application=application,
        rounds=rounds, existing=existing,
    )


@app.route("/recruiter/interviews")
@roles_required("Recruiter")
def recruiter_interviews():
    when = request.args.get("when", "all")
    sql = """
        SELECT i.*, r.Round_Name, r.Round_Type, r.Max_Marks,
               s.Name AS Student_Name, s.Branch, j.Job_Title, j.Job_ID
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        JOIN Application a ON a.Application_ID=i.Application_ID
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        WHERE j.Company_ID=%s
    """
    params = [session["user_id"]]
    if when == "upcoming":
        sql += " AND i.Interview_Date >= NOW()"
    elif when == "past":
        sql += " AND i.Interview_Date < NOW()"
    sql += " ORDER BY i.Interview_Date DESC"
    return render_template(
        "recruiter/interviews.html", interviews=query_all(sql, params), when=when
    )


@app.route("/recruiter/interviews/<int:interview_id>/result", methods=["POST"])
@roles_required("Recruiter")
def recruiter_interview_result(interview_id):
    result = request.form.get("result", "")
    marks_raw = request.form.get("marks_obtained", "").strip()
    marks = to_float(marks_raw, -1) if marks_raw else None
    row = query_one(
        """
        SELECT i.*, r.Max_Marks, j.Company_ID
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        JOIN Application a ON a.Application_ID=i.Application_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        WHERE i.Interview_ID=%s
        """, (interview_id,),
    )
    if not row or row["Company_ID"] != session["user_id"]:
        abort(403)
    if result not in INTERVIEW_RESULTS:
        flash("Invalid interview result.", "warning")
    elif marks is not None and (marks < 0 or marks > float(row["Max_Marks"])):
        flash(f"Marks must be between 0 and {row['Max_Marks']}.", "warning")
    else:
        execute(
            "UPDATE Interview SET Result=%s, Marks_Obtained=%s WHERE Interview_ID=%s",
            (result, marks, interview_id),
        )
        flash("Interview result saved.", "success")
    return redirect(request.referrer or url_for("recruiter_interviews"))


@app.route("/recruiter/applications/<int:application_id>/offer", methods=["GET", "POST"])
@roles_required("Recruiter")
def recruiter_offer_new(application_id):
    cid = session["user_id"]
    application = query_one(
        """
        SELECT a.*, s.Name AS Student_Name, s.Branch, s.CGPA,
               j.Job_ID, j.Job_Title, j.Salary_Package, j.Company_ID,
               c.Company_Name
        FROM Application a
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE a.Application_ID=%s AND j.Company_ID=%s
        """, (application_id, cid),
    )
    if not application:
        abort(404)
    existing = query_one(
        "SELECT * FROM Placement WHERE Student_ID=%s AND Job_ID=%s",
        (application["Student_ID"], application["Job_ID"]),
    )

    if request.method == "POST":
        if existing:
            flash("An offer for this student and job already exists.", "warning")
            return redirect(url_for("recruiter_applicants", job_id=application["Job_ID"]))
        package = to_float(request.form.get("package_offered"), -1)
        joining = parse_date(request.form.get("joining_date"))
        status = request.form.get("status", "Offer Released")
        if package < 0:
            flash("Package must be zero or greater.", "warning")
        elif joining and joining < date.today():
            flash("Joining date cannot be in the past.", "warning")
        elif status not in PLACEMENT_STATUSES:
            flash("Invalid offer status.", "warning")
        else:
            try:
                create_placement(
                    application["Student_ID"], application["Job_ID"],
                    application["Company_ID"], package, joining, status,
                )
                flash("Offer recorded and the candidate marked as Selected.", "success")
                return redirect(url_for("recruiter_placements"))
            except IntegrityError:
                flash("An offer for this student and job already exists.", "danger")
            except MySQLError:
                app.logger.exception("Placement insert failed")
                flash("Could not record the offer.", "danger")

    return render_template("recruiter/offer_form.html", application=application, existing=existing)


@app.route("/recruiter/placements")
@roles_required("Recruiter")
def recruiter_placements():
    placements = query_all(
        """
        SELECT p.*, s.Name AS Student_Name, s.Branch, s.CGPA, j.Job_Title
        FROM Placement p
        JOIN Student s ON s.Student_ID=p.Student_ID
        JOIN Job j ON j.Job_ID=p.Job_ID
        WHERE p.Company_ID=%s
        ORDER BY p.Placement_Date DESC
        """, (session["user_id"],),
    )
    return render_template("recruiter/placements.html", placements=placements)


@app.route("/recruiter/placements/<int:placement_id>/status", methods=["POST"])
@roles_required("Recruiter")
def recruiter_placement_status(placement_id):
    status = request.form.get("status", "")
    if status not in PLACEMENT_STATUSES:
        flash("Invalid offer status.", "warning")
    else:
        _, rowcount = execute(
            "UPDATE Placement SET Status=%s WHERE Placement_ID=%s AND Company_ID=%s",
            (status, placement_id, session["user_id"]),
        )
        flash("Offer status updated." if rowcount else "Offer not found.", "success" if rowcount else "warning")
    return redirect(request.referrer or url_for("recruiter_placements"))


@app.route("/officer/dashboard")
@roles_required("Officer", "Admin")
def officer_dashboard():
    st = global_stats()
    branches = branch_stats()
    companies = company_stats()[:6]
    labels, values = status_chart()
    pending = query_all(
        "SELECT * FROM Company WHERE Approval_Status='Pending' ORDER BY Created_At DESC"
    )
    recent = query_all(
        """
        SELECT p.*, s.Name AS Student_Name, s.Branch, c.Company_Name, j.Job_Title
        FROM Placement p
        JOIN Student s ON s.Student_ID=p.Student_ID
        JOIN Company c ON c.Company_ID=p.Company_ID
        JOIN Job j ON j.Job_ID=p.Job_ID
        ORDER BY p.Placement_Date DESC, p.Placement_ID DESC LIMIT 6
        """
    )
    return render_template(
        "officer/dashboard.html", stats=st, branches=branches,
        companies=companies, status_labels=labels, status_values=values,
        pending=pending, recent=recent,
        branch_labels=[b["Branch"] for b in branches],
        branch_values=[int(b["Placed_Students"]) for b in branches],
    )


@app.route("/officer/students")
@roles_required("Officer", "Admin")
def officer_students():
    q = request.args.get("q", "").strip()
    branch = request.args.get("branch", "").strip()
    sql = """
        SELECT s.*,
               (SELECT COUNT(*) FROM Application a WHERE a.Student_ID=s.Student_ID) AS Applications,
               (SELECT MAX(p.Package_Offered) FROM Placement p WHERE p.Student_ID=s.Student_ID) AS Highest_Package,
               (SELECT p.Status FROM Placement p WHERE p.Student_ID=s.Student_ID
                 ORDER BY p.Package_Offered DESC LIMIT 1) AS Placement_Status
        FROM Student s WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (s.Name LIKE %s OR s.Email LIKE %s OR s.Branch LIKE %s)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if branch:
        sql += " AND s.Branch=%s"
        params.append(branch)
    sql += " ORDER BY s.Name"
    branches = query_all("SELECT DISTINCT Branch FROM Student ORDER BY Branch")
    return render_template(
        "officer/students.html", students=query_all(sql, params),
        branches=branches, q=q, branch=branch,
    )


@app.route("/officer/students/<int:student_id>")
@roles_required("Officer", "Admin")
def officer_student_detail(student_id):
    student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (student_id,))
    if not student:
        abort(404)
    applications = query_all(
        """
        SELECT a.*, j.Job_Title, c.Company_Name
        FROM Application a
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE a.Student_ID=%s ORDER BY a.Application_Date DESC
        """, (student_id,),
    )
    interviews = query_all(
        """
        SELECT i.*, r.Round_Name, j.Job_Title, c.Company_Name
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        JOIN Application a ON a.Application_ID=i.Application_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE a.Student_ID=%s ORDER BY i.Interview_Date DESC
        """, (student_id,),
    )
    placements = query_all(
        """
        SELECT p.*, j.Job_Title, c.Company_Name
        FROM Placement p
        JOIN Job j ON j.Job_ID=p.Job_ID
        JOIN Company c ON c.Company_ID=p.Company_ID
        WHERE p.Student_ID=%s ORDER BY p.Placement_Date DESC
        """, (student_id,),
    )
    return render_template(
        "officer/student_detail.html", student=student,
        applications=applications, interviews=interviews, placements=placements,
    )


@app.route("/officer/students/<int:student_id>/edit", methods=["GET", "POST"])
@roles_required("Officer", "Admin")
def officer_student_edit(student_id):
    student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (student_id,))
    if not student:
        abort(404)
    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        phone = f.get("phone", "").strip()
        dob = parse_date(f.get("date_of_birth"))
        gender = f.get("gender", "")
        branch = f.get("branch", "")
        batch = to_int(f.get("batch_year"))
        cgpa = to_float(f.get("cgpa"), -1)
        if not all([name, phone, dob, gender, branch]):
            flash("Please fill in all required fields.", "warning")
        elif not (0 <= cgpa <= 10):
            flash("CGPA must be between 0 and 10.", "warning")
        elif not (2000 <= batch <= 2100):
            flash("Invalid batch year.", "warning")
        else:
            try:
                execute(
                    """
                    UPDATE Student
                    SET Name=%s, Phone=%s, Date_of_Birth=%s, Gender=%s,
                        Branch=%s, Batch_Year=%s, CGPA=%s, Address=%s
                    WHERE Student_ID=%s
                    """, (name, phone, dob, gender, branch, batch, cgpa,
                          f.get("address", "").strip(), student_id),
                )
                flash("Student record updated.", "success")
                return redirect(url_for("officer_student_detail", student_id=student_id))
            except IntegrityError:
                flash("That phone number is already in use.", "danger")
            except MySQLError:
                app.logger.exception("Student update failed")
                flash("Could not update the student.", "danger")
        student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (student_id,))
    return render_template("officer/student_form.html", student=student)


@app.route("/officer/students/<int:student_id>/delete", methods=["POST"])
@roles_required("Officer", "Admin")
def officer_student_delete(student_id):
    try:
        _, rowcount = execute("DELETE FROM Student WHERE Student_ID=%s", (student_id,))
        flash("Student deleted with all related records." if rowcount else "Student not found.",
              "success" if rowcount else "warning")
    except MySQLError:
        app.logger.exception("Student delete failed")
        flash("Could not delete the student.", "danger")
    return redirect(url_for("officer_students"))


@app.route("/officer/companies")
@roles_required("Officer", "Admin")
def officer_companies():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    sql = """
        SELECT c.*,
               (SELECT COUNT(*) FROM Job j WHERE j.Company_ID=c.Company_ID) AS Jobs,
               (SELECT COUNT(*) FROM Application a JOIN Job j ON j.Job_ID=a.Job_ID
                 WHERE j.Company_ID=c.Company_ID) AS Applications,
               (SELECT COUNT(*) FROM Placement p WHERE p.Company_ID=c.Company_ID
                 AND p.Status IN ('Offer Accepted','Joined')) AS Selections
        FROM Company c WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (c.Company_Name LIKE %s OR c.Industry LIKE %s OR c.Location LIKE %s)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if status:
        sql += " AND c.Approval_Status=%s"
        params.append(status)
    sql += " ORDER BY c.Company_Name"
    return render_template(
        "officer/companies.html", companies=query_all(sql, params),
        q=q, status=status,
    )


@app.route("/officer/companies/<int:company_id>")
@roles_required("Officer", "Admin")
def officer_company_detail(company_id):
    company = query_one("SELECT * FROM Company WHERE Company_ID=%s", (company_id,))
    if not company:
        abort(404)
    jobs = query_all(
        """
        SELECT j.*, (SELECT COUNT(*) FROM Application a WHERE a.Job_ID=j.Job_ID) AS Application_Count
        FROM Job j WHERE j.Company_ID=%s ORDER BY j.Job_ID DESC
        """, (company_id,),
    )
    placements = query_all(
        """
        SELECT p.*, s.Name AS Student_Name, s.Branch, j.Job_Title
        FROM Placement p
        JOIN Student s ON s.Student_ID=p.Student_ID
        JOIN Job j ON j.Job_ID=p.Job_ID
        WHERE p.Company_ID=%s ORDER BY p.Placement_Date DESC
        """, (company_id,),
    )
    return render_template(
        "officer/company_detail.html", company=company, jobs=jobs, placements=placements
    )


@app.route("/officer/companies/<int:company_id>/status/<status>", methods=["POST"])
@roles_required("Officer", "Admin")
def officer_company_status(company_id, status):
    if status not in ("Approved", "Rejected", "Pending"):
        abort(400)
    execute("UPDATE Company SET Approval_Status=%s WHERE Company_ID=%s", (status, company_id))
    flash(f"Company marked as {status.lower()}.", "success")
    return redirect(request.referrer or url_for("officer_companies"))


@app.route("/officer/applications")
@roles_required("Officer", "Admin")
def officer_applications():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    company_id = to_int(request.args.get("company_id"), 0)
    sql = """
        SELECT a.*, s.Name AS Student_Name, s.Branch, s.CGPA,
               j.Job_Title, j.Job_ID, c.Company_Name, c.Company_ID,
               p.Status AS Placement_Status
        FROM Application a
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        LEFT JOIN Placement p ON p.Student_ID=a.Student_ID AND p.Job_ID=a.Job_ID
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (s.Name LIKE %s OR c.Company_Name LIKE %s OR j.Job_Title LIKE %s)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if status:
        sql += " AND a.Status=%s"
        params.append(status)
    if company_id:
        sql += " AND c.Company_ID=%s"
        params.append(company_id)
    sql += " ORDER BY a.Application_Date DESC, a.Application_ID DESC"
    companies = query_all("SELECT Company_ID, Company_Name FROM Company ORDER BY Company_Name")
    return render_template(
        "officer/applications.html", applications=query_all(sql, params),
        companies=companies, q=q, status=status, company_id=company_id,
    )


@app.route("/officer/rounds", methods=["GET", "POST"])
@roles_required("Officer", "Admin")
def officer_rounds():
    if request.method == "POST":
        job_id = to_int(request.form.get("job_id"))
        name = request.form.get("round_name", "").strip()
        rtype = request.form.get("round_type", "")
        rdate = parse_date(request.form.get("round_date"))
        max_marks = to_float(request.form.get("max_marks"), 0)
        job = query_one("SELECT Job_ID FROM Job WHERE Job_ID=%s", (job_id,))
        if not job or not name or not rdate or rtype not in ROUND_TYPES:
            flash("Please complete the round details.", "warning")
        elif max_marks <= 0:
            flash("Maximum marks must be greater than zero.", "warning")
        else:
            try:
                execute(
                    """INSERT INTO Recruitment_Round
                       (Job_ID, Round_Name, Round_Type, Round_Date, Max_Marks)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (job_id, name, rtype, rdate, max_marks),
                )
                flash("Recruitment round added.", "success")
                return redirect(url_for("officer_rounds"))
            except IntegrityError:
                flash("That round name already exists for this job.", "danger")
            except MySQLError:
                flash("Could not add the round.", "danger")
    rounds = query_all(
        """
        SELECT r.*, j.Job_Title, c.Company_Name,
               (SELECT COUNT(*) FROM Interview i WHERE i.Round_ID=r.Round_ID) AS Interview_Count
        FROM Recruitment_Round r
        JOIN Job j ON j.Job_ID=r.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        ORDER BY j.Job_Title, r.Round_Date
        """
    )
    jobs = query_all(
        """SELECT j.Job_ID, j.Job_Title, c.Company_Name
           FROM Job j JOIN Company c ON c.Company_ID=j.Company_ID
           ORDER BY c.Company_Name, j.Job_Title"""
    )
    return render_template("officer/rounds.html", rounds=rounds, jobs=jobs)


@app.route("/officer/rounds/<int:round_id>/delete", methods=["POST"])
@roles_required("Officer", "Admin")
def officer_round_delete(round_id):
    execute("DELETE FROM Recruitment_Round WHERE Round_ID=%s", (round_id,))
    flash("Round deleted.", "success")
    return redirect(url_for("officer_rounds"))


@app.route("/officer/interviews")
@roles_required("Officer", "Admin")
def officer_interviews():
    when = request.args.get("when", "all")
    sql = """
        SELECT i.*, r.Round_Name, s.Name AS Student_Name, s.Branch,
               j.Job_Title, c.Company_Name
        FROM Interview i
        JOIN Recruitment_Round r ON r.Round_ID=i.Round_ID
        JOIN Application a ON a.Application_ID=i.Application_ID
        JOIN Student s ON s.Student_ID=a.Student_ID
        JOIN Job j ON j.Job_ID=a.Job_ID
        JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE 1=1
    """
    params = []
    if when == "upcoming":
        sql += " AND i.Interview_Date >= NOW()"
    elif when == "past":
        sql += " AND i.Interview_Date < NOW()"
    sql += " ORDER BY i.Interview_Date DESC"
    return render_template(
        "officer/interviews.html", interviews=query_all(sql, params), when=when
    )


@app.route("/officer/placements", methods=["GET", "POST"])
@roles_required("Officer", "Admin")
def officer_placements():
    if request.method == "POST":
        student_id = to_int(request.form.get("student_id"))
        job_id = to_int(request.form.get("job_id"))
        package = to_float(request.form.get("package_offered"), -1)
        joining = parse_date(request.form.get("joining_date"))
        status = request.form.get("status", "Offer Released")
        job = query_one("SELECT * FROM Job WHERE Job_ID=%s", (job_id,))
        student = query_one("SELECT * FROM Student WHERE Student_ID=%s", (student_id,))
        if not job or not student:
            flash("Please choose a valid student and job.", "warning")
        elif package < 0:
            flash("Package cannot be negative.", "warning")
        elif joining and joining < date.today():
            flash("Joining date cannot be in the past.", "warning")
        elif status not in PLACEMENT_STATUSES:
            flash("Invalid offer status.", "warning")
        else:
            try:
                create_placement(student_id, job_id, job["Company_ID"], package, joining, status)
                flash("Placement record created.", "success")
                return redirect(url_for("officer_placements"))
            except IntegrityError:
                flash("This student already has an offer for this job.", "danger")
            except MySQLError:
                flash("Could not create the placement record.", "danger")

    placements = query_all(
        """
        SELECT p.*, s.Name AS Student_Name, s.Branch, s.CGPA,
               c.Company_Name, j.Job_Title
        FROM Placement p
        JOIN Student s ON s.Student_ID=p.Student_ID
        JOIN Company c ON c.Company_ID=p.Company_ID
        JOIN Job j ON j.Job_ID=p.Job_ID
        ORDER BY p.Placement_Date DESC, p.Placement_ID DESC
        """
    )
    students = query_all("SELECT Student_ID, Name, Branch, CGPA FROM Student ORDER BY Name")
    jobs = query_all(
        """SELECT j.Job_ID, j.Job_Title, j.Salary_Package, c.Company_Name
           FROM Job j JOIN Company c ON c.Company_ID=j.Company_ID
           ORDER BY c.Company_Name, j.Job_Title"""
    )
    return render_template(
        "officer/placements.html", placements=placements, students=students, jobs=jobs
    )


@app.route("/officer/placements/<int:placement_id>/delete", methods=["POST"])
@roles_required("Officer", "Admin")
def officer_placement_delete(placement_id):
    try:
        deleted = delete_placement(placement_id)
    except MySQLError:
        flash("Could not delete the placement record.", "danger")
        return redirect(url_for("officer_placements"))
    if deleted:
        flash("Placement record deleted and the application moved back to Shortlisted.", "success")
    else:
        flash("That placement record no longer exists.", "warning")
    return redirect(url_for("officer_placements"))


@app.route("/officer/reports")
@roles_required("Officer", "Admin")
def officer_reports():
    reports = query_all(
        """
        SELECT r.*, o.Name AS Officer_Name
        FROM Report r
        JOIN Placement_Officer o ON o.Officer_ID=r.Generated_By
        ORDER BY r.Generated_Date DESC, r.Report_ID DESC
        """
    )
    return render_template("officer/reports.html", reports=reports)


@app.route("/officer/reports/generate", methods=["POST"])
@roles_required("Officer", "Admin")
def officer_report_generate():
    rtype = request.form.get("report_type", "")
    description = request.form.get("description", "").strip()
    if rtype not in REPORT_TYPES:
        flash("Please choose a valid report type.", "warning")
        return redirect(url_for("officer_reports"))
    _, report_id = execute(
        "INSERT INTO Report (Report_Type, Generated_By, Description) VALUES (%s,%s,%s)",
        (rtype, session["user_id"], description),
    )
    flash("Report generated and saved.", "success")
    return redirect(url_for("officer_report_detail", report_id=report_id))


@app.route("/officer/reports/<int:report_id>")
@roles_required("Officer", "Admin")
def officer_report_detail(report_id):
    report = query_one(
        """
        SELECT r.*, o.Name AS Officer_Name, o.Designation
        FROM Report r
        JOIN Placement_Officer o ON o.Officer_ID=r.Generated_By
        WHERE r.Report_ID=%s
        """, (report_id,),
    )
    if not report:
        abort(404)
    summary, columns, rows = build_report_data(report["Report_Type"])
    return render_template(
        "officer/report_detail.html", report=report,
        summary=summary, columns=columns, rows=rows,
    )


@app.route("/officer/jobs/<int:job_id>/eligible")
@roles_required("Officer", "Admin")
def officer_eligibility(job_id):
    job = query_one(
        """
        SELECT j.*, c.Company_Name
        FROM Job j JOIN Company c ON c.Company_ID=j.Company_ID
        WHERE j.Job_ID=%s
        """, (job_id,),
    )
    if not job:
        abort(404)
    students = query_all(
        """
        SELECT s.*, EXISTS(SELECT 1 FROM Application a
                           WHERE a.Student_ID=s.Student_ID AND a.Job_ID=%s) AS Has_Applied
        FROM Student s ORDER BY s.CGPA DESC
        """, (job_id,),
    )
    eligible = [s for s in students if is_eligible(s, job)]
    return render_template(
        "officer/eligibility.html", job=job, students=eligible,
        applied_count=len([s for s in eligible if s["Has_Applied"]]),
    )


@app.route("/admin/dashboard")
@roles_required("Admin")
def admin_dashboard():
    st = global_stats()
    branches = branch_stats()
    companies = company_stats()
    labels, values = status_chart()
    packages = query_all(
        """
        SELECT CASE
                 WHEN Package_Offered < 5 THEN 'Below 5 LPA'
                 WHEN Package_Offered < 8 THEN '5 - 8 LPA'
                 WHEN Package_Offered < 12 THEN '8 - 12 LPA'
                 ELSE '12+ LPA'
               END AS Bucket,
               COUNT(*) AS Total,
               MIN(Package_Offered) AS Sort_Key
        FROM Placement
        WHERE Status IN ('Offer Accepted','Joined')
        GROUP BY Bucket
        ORDER BY Sort_Key
        """
    )
    recent = query_all(
        """
        SELECT p.*, s.Name AS Student_Name, s.Branch, c.Company_Name, j.Job_Title
        FROM Placement p
        JOIN Student s ON s.Student_ID=p.Student_ID
        JOIN Company c ON c.Company_ID=p.Company_ID
        JOIN Job j ON j.Job_ID=p.Job_ID
        ORDER BY p.Placement_Date DESC, p.Placement_ID DESC LIMIT 8
        """
    )
    pending = query_all(
        "SELECT * FROM Company WHERE Approval_Status='Pending' ORDER BY Created_At DESC"
    )
    officers = query_all(
        "SELECT * FROM Placement_Officer ORDER BY Account_Role, Name"
    )
    return render_template(
        "admin/dashboard.html", stats=st, branches=branches, companies=companies,
        status_labels=labels, status_values=values,
        package_labels=[p["Bucket"] for p in packages],
        package_values=[int(p["Total"]) for p in packages],
        recent=recent, pending=pending, officers=officers,
        branch_labels=[b["Branch"] for b in branches],
        branch_values=[int(b["Placed_Students"]) for b in branches],
    )


@app.route("/admin/officers")
@roles_required("Admin")
def admin_officers():
    officers = query_all("SELECT * FROM Placement_Officer ORDER BY Account_Role, Name")
    return render_template("admin/officers.html", officers=officers)


@app.route("/admin/officers/add", methods=["POST"])
@roles_required("Admin")
def admin_officer_add():
    f = request.form
    name = f.get("name", "").strip()
    email = f.get("email", "").strip().lower()
    contact = f.get("contact_number", "").strip()
    designation = f.get("designation", "").strip()
    role = f.get("account_role", "Officer")
    password = f.get("password", "")
    if not all([name, email, contact, designation, password]):
        flash("Please fill in all required fields.", "warning")
    elif role not in ("Officer", "Admin"):
        flash("Invalid account role.", "warning")
    elif len(password) < 6:
        flash("Password must be at least 6 characters.", "warning")
    else:
        try:
            execute(
                """
                INSERT INTO Placement_Officer
                    (Name, Email, Contact_Number, Designation, Password_Hash, Account_Role)
                VALUES (%s,%s,%s,%s,%s,%s)
                """, (name, email, contact, designation,
                      generate_password_hash(password), role),
            )
            flash("Placement cell account created.", "success")
        except IntegrityError:
            flash("That email is already registered.", "danger")
        except MySQLError:
            flash("Could not create the account.", "danger")
    return redirect(url_for("admin_officers"))


@app.route("/admin/officers/<int:officer_id>/toggle", methods=["POST"])
@roles_required("Admin")
def admin_officer_toggle(officer_id):
    if officer_id == session["user_id"]:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin_officers"))
    execute(
        "UPDATE Placement_Officer SET Is_Active = 1 - Is_Active WHERE Officer_ID=%s",
        (officer_id,),
    )
    flash("Account status changed.", "success")
    return redirect(url_for("admin_officers"))


@app.route("/admin/reports")
@roles_required("Admin")
def admin_reports():
    return redirect(url_for("officer_reports"))


@app.errorhandler(403)
def error_403(_e):
    return render_template(
        "error.html", code=403, title="Access denied",
        message="Your account does not have permission to open this page.",
    ), 403


@app.errorhandler(404)
def error_404(_e):
    return render_template(
        "error.html", code=404, title="Page not found",
        message="The page or record you requested does not exist.",
    ), 404


@app.errorhandler(MySQLError)
def error_mysql(exc):
    app.logger.exception("Database error: %s", exc)
    return render_template(
        "error.html", code=500, title="Database error",
        message="The database could not complete this request. Check that MySQL is running and that your .env settings are correct.",
    ), 500


@app.errorhandler(500)
def error_500(_e):
    return render_template(
        "error.html", code=500, title="Something went wrong",
        message="An unexpected error occurred. Please go back and try again.",
    ), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
