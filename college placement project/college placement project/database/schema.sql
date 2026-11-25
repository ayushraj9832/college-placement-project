

CREATE DATABASE IF NOT EXISTS college_placement_db
  CHARACTER SET utf8mb4;

USE college_placement_db;

SET NAMES utf8mb4;

-- Drop in reverse dependency order (children before parents).
DROP TABLE IF EXISTS Report;
DROP TABLE IF EXISTS Placement;
DROP TABLE IF EXISTS Interview;
DROP TABLE IF EXISTS Recruitment_Round;
DROP TABLE IF EXISTS Application;
DROP TABLE IF EXISTS Job;
DROP TABLE IF EXISTS Company;
DROP TABLE IF EXISTS Placement_Officer;
DROP TABLE IF EXISTS Student;



CREATE TABLE Student (
  Student_ID    INT UNSIGNED AUTO_INCREMENT,
  Name          VARCHAR(100) NOT NULL,
  Email         VARCHAR(120) NOT NULL,
  Phone         VARCHAR(15)  NOT NULL,
  Password_Hash VARCHAR(255) NOT NULL,
  Date_of_Birth DATE         NOT NULL,
  Gender        ENUM('Male','Female','Other') NOT NULL,
  Branch        VARCHAR(50)  NOT NULL,
  Batch_Year    SMALLINT UNSIGNED NOT NULL,
  CGPA          DECIMAL(4,2) NOT NULL DEFAULT 0.00,
  Address       VARCHAR(255) NULL,
  Created_At    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (Student_ID),
  UNIQUE KEY uq_student_email (Email),
  UNIQUE KEY uq_student_phone (Phone),
  CONSTRAINT chk_student_cgpa  CHECK (CGPA >= 0 AND CGPA <= 10),
  CONSTRAINT chk_student_batch CHECK (Batch_Year BETWEEN 2000 AND 2100)
) ENGINE = InnoDB
  COMMENT = 'Student master table and student login account';



CREATE TABLE Company (
  Company_ID      INT UNSIGNED AUTO_INCREMENT,
  Company_Name    VARCHAR(120) NOT NULL,
  Industry        VARCHAR(80)  NOT NULL,
  Location        VARCHAR(100) NOT NULL,
  HR_Name         VARCHAR(100) NOT NULL,
  HR_Email        VARCHAR(120) NOT NULL,
  Contact_Number  VARCHAR(15)  NOT NULL,
  Website         VARCHAR(150) NULL,
  Password_Hash   VARCHAR(255) NOT NULL,
  Approval_Status ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
  Created_At      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (Company_ID),
  UNIQUE KEY uq_company_name (Company_Name),
  UNIQUE KEY uq_company_hr_email (HR_Email)
) ENGINE = InnoDB
  COMMENT = 'Company master table and recruiter login account';



CREATE TABLE Placement_Officer (
  Officer_ID     INT UNSIGNED AUTO_INCREMENT,
  Name           VARCHAR(100) NOT NULL,
  Email          VARCHAR(120) NOT NULL,
  Contact_Number VARCHAR(15)  NOT NULL,
  Designation    VARCHAR(80)  NOT NULL,
  Password_Hash  VARCHAR(255) NOT NULL,
  Account_Role   ENUM('Officer','Admin') NOT NULL DEFAULT 'Officer',
  Is_Active      TINYINT(1)   NOT NULL DEFAULT 1,
  Created_At     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (Officer_ID),
  UNIQUE KEY uq_officer_email (Email),
  CONSTRAINT chk_officer_active CHECK (Is_Active IN (0,1))
) ENGINE = InnoDB
  COMMENT = 'Placement officer and administrator accounts';



CREATE TABLE Job (
  Job_ID               INT UNSIGNED AUTO_INCREMENT,
  Company_ID           INT UNSIGNED NOT NULL,
  Job_Title            VARCHAR(120) NOT NULL,
  Job_Description      TEXT         NOT NULL,
  Eligible_Branch      VARCHAR(150) NOT NULL DEFAULT 'All',
  Min_CGPA             DECIMAL(4,2) NOT NULL DEFAULT 0.00,
  Salary_Package       DECIMAL(10,2) NOT NULL,
  Job_Location         VARCHAR(100) NOT NULL,
  Application_Deadline DATE         NOT NULL,
  Job_Type             ENUM('Full-Time','Internship','Internship + PPO','Part-Time')
                       NOT NULL DEFAULT 'Full-Time',
  Created_At           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (Job_ID),
  KEY idx_job_deadline (Application_Deadline),
  CONSTRAINT fk_job_company FOREIGN KEY (Company_ID)
    REFERENCES Company (Company_ID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_job_min_cgpa CHECK (Min_CGPA >= 0 AND Min_CGPA <= 10),
  CONSTRAINT chk_job_salary   CHECK (Salary_Package >= 0)
) ENGINE = InnoDB
  COMMENT = 'Job openings posted by companies';


CREATE TABLE Application (
  Application_ID   INT UNSIGNED AUTO_INCREMENT,
  Student_ID       INT UNSIGNED NOT NULL,
  Job_ID           INT UNSIGNED NOT NULL,
  Application_Date DATE         NOT NULL DEFAULT (CURRENT_DATE),
  Status           ENUM('Applied','Under Review','Shortlisted',
                        'Interview Scheduled','Selected','Rejected','Withdrawn')
                   NOT NULL DEFAULT 'Applied',
  Updated_At       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                   ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (Application_ID),
  UNIQUE KEY uq_application_student_job (Student_ID, Job_ID),
  KEY idx_application_job_status (Job_ID, Status),
  CONSTRAINT fk_application_student FOREIGN KEY (Student_ID)
    REFERENCES Student (Student_ID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_application_job FOREIGN KEY (Job_ID)
    REFERENCES Job (Job_ID)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB
  COMMENT = 'Student applications to jobs (many-to-many bridge table)';



CREATE TABLE Recruitment_Round (
  Round_ID   INT UNSIGNED AUTO_INCREMENT,
  Job_ID     INT UNSIGNED NOT NULL,
  Round_Name VARCHAR(80)  NOT NULL,
  Round_Type ENUM('Aptitude','Technical','HR','Group Discussion','Coding','Other')
             NOT NULL,
  Round_Date DATE         NOT NULL,
  Max_Marks  DECIMAL(6,2) NOT NULL DEFAULT 100.00,
  PRIMARY KEY (Round_ID),
  UNIQUE KEY uq_round_job_name (Job_ID, Round_Name),
  CONSTRAINT fk_round_job FOREIGN KEY (Job_ID)
    REFERENCES Job (Job_ID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_round_max_marks CHECK (Max_Marks > 0)
) ENGINE = InnoDB
  COMMENT = 'Selection rounds defined for each job';



CREATE TABLE Interview (
  Interview_ID     INT UNSIGNED AUTO_INCREMENT,
  Application_ID   INT UNSIGNED NOT NULL,
  Round_ID         INT UNSIGNED NOT NULL,
  Interview_Date   DATETIME     NOT NULL,
  Result           ENUM('Pending','Pass','Fail','On Hold')
                   NOT NULL DEFAULT 'Pending',
  Interviewer_Name VARCHAR(100) NOT NULL,
  Marks_Obtained   DECIMAL(6,2) NULL,
  Remarks          VARCHAR(255) NULL,
  PRIMARY KEY (Interview_ID),
  UNIQUE KEY uq_interview_app_round (Application_ID, Round_ID),
  CONSTRAINT fk_interview_application FOREIGN KEY (Application_ID)
    REFERENCES Application (Application_ID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_interview_round FOREIGN KEY (Round_ID)
    REFERENCES Recruitment_Round (Round_ID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_interview_marks CHECK (Marks_Obtained IS NULL OR Marks_Obtained >= 0)
) ENGINE = InnoDB
  COMMENT = 'Interview schedule and result per application per round';



CREATE TABLE Placement (
  Placement_ID    INT UNSIGNED AUTO_INCREMENT,
  Student_ID      INT UNSIGNED NOT NULL,
  Job_ID          INT UNSIGNED NOT NULL,
  Company_ID      INT UNSIGNED NOT NULL,
  Placement_Date  DATE         NOT NULL DEFAULT (CURRENT_DATE),
  Package_Offered DECIMAL(10,2) NOT NULL,
  Joining_Date    DATE         NULL,
  Status          ENUM('Offer Released','Offer Accepted','Offer Declined',
                       'Joined','Withdrawn')
                  NOT NULL DEFAULT 'Offer Released',
  PRIMARY KEY (Placement_ID),
  UNIQUE KEY uq_placement_student_job (Student_ID, Job_ID),
  CONSTRAINT fk_placement_student FOREIGN KEY (Student_ID)
    REFERENCES Student (Student_ID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_placement_job FOREIGN KEY (Job_ID)
    REFERENCES Job (Job_ID)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_placement_company FOREIGN KEY (Company_ID)
    REFERENCES Company (Company_ID)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_placement_package CHECK (Package_Offered >= 0),
  CONSTRAINT chk_placement_joining CHECK
    (Joining_Date IS NULL OR Joining_Date >= Placement_Date)
) ENGINE = InnoDB
  COMMENT = 'Final placement / offer records';



CREATE TABLE Report (
  Report_ID      INT UNSIGNED AUTO_INCREMENT,
  Report_Type    ENUM('Placement Summary','Branch-wise Report',
                      'Company-wise Report','Unplaced Students',
                      'Recruitment Summary','Other') NOT NULL,
  Generated_Date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  Generated_By   INT UNSIGNED NOT NULL,
  Description    VARCHAR(500) NULL,
  PRIMARY KEY (Report_ID),
  CONSTRAINT fk_report_officer FOREIGN KEY (Generated_By)
    REFERENCES Placement_Officer (Officer_ID)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB
  COMMENT = 'Placement reports generated by officers/administrators';

s
SHOW TABLES;
