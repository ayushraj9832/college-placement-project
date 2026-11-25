

USE college_placement_db;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Report;
TRUNCATE TABLE Placement;
TRUNCATE TABLE Interview;
TRUNCATE TABLE Recruitment_Round;
TRUNCATE TABLE Application;
TRUNCATE TABLE Job;
TRUNCATE TABLE Company;
TRUNCATE TABLE Placement_Officer;
TRUNCATE TABLE Student;
SET FOREIGN_KEY_CHECKS = 1;

-- Werkzeug-compatible PBKDF2 hashes (plain passwords are in the header).
SET @student_pw   = 'pbkdf2:sha256:600000$a1b2c3d4e5f60718$cc9b2d573e2fd8385b14a9817a1b8a1f55fa0677c78f253faf368b1935dab4a3';
SET @recruiter_pw = 'pbkdf2:sha256:600000$b2c3d4e5f6071829$72e9493437e6ae73dc4d5254c213d11270679e99715f1819b3ce9f58dba91826';
SET @officer_pw   = 'pbkdf2:sha256:600000$c3d4e5f60718293a$5ff7e812dc6b995239df189250b3d3abb5fbe7f8a12fd18e3d209a293e1f2c16';
SET @admin_pw     = 'pbkdf2:sha256:600000$d4e5f60718293a4b$8c5a017550ec26d199ef52654082d945b7b83cae6f1c8e5e6d3ff1a856a10ead';

START TRANSACTION;


INSERT INTO Student
  (Student_ID, Name, Email, Phone, Password_Hash, Date_of_Birth,
   Gender, Branch, Batch_Year, CGPA, Address)
VALUES
(1,  'Aarav Sharma',        'aarav.sharma@college.edu',       '9876500101', @student_pw, '2003-04-12', 'Male',   'MCA', 2027, 8.60, 'Kothrud, Pune'),
(2,  'Diya Patel',          'diya.patel@college.edu',         '9876500102', @student_pw, '2003-09-25', 'Female', 'MCA', 2027, 9.10, 'Navrangpura, Ahmedabad'),
(3,  'Rohan Mehta',         'rohan.mehta@college.edu',        '9876500103', @student_pw, '2002-12-08', 'Male',   'CSE', 2027, 7.80, 'Andheri, Mumbai'),
(4,  'Ananya Iyer',         'ananya.iyer@college.edu',        '9876500104', @student_pw, '2003-06-18', 'Female', 'IT',  2027, 8.90, 'Adyar, Chennai'),
(5,  'Kabir Singh',         'kabir.singh@college.edu',        '9876500105', @student_pw, '2003-02-14', 'Male',   'CSE', 2027, 6.90, 'Dwarka, Delhi'),
(6,  'Meera Nair',          'meera.nair@college.edu',         '9876500106', @student_pw, '2003-11-30', 'Female', 'MCA', 2027, 7.40, 'Kakkanad, Kochi'),
(7,  'Aditya Rao',          'aditya.rao@college.edu',         '9876500107', @student_pw, '2002-08-21', 'Male',   'ECE', 2027, 7.10, 'Gachibowli, Hyderabad'),
(8,  'Sanya Kapoor',        'sanya.kapoor@college.edu',       '9876500108', @student_pw, '2003-03-05', 'Female', 'IT',  2027, 8.30, 'Malviya Nagar, Jaipur'),
(9,  'Vivaan Joshi',        'vivaan.joshi@college.edu',       '9876500109', @student_pw, '2003-07-19', 'Male',   'MCA', 2027, 6.50, 'Dharampeth, Nagpur'),
(10, 'Ishita Desai',        'ishita.desai@college.edu',       '9876500110', @student_pw, '2003-01-27', 'Female', 'CSE', 2027, 9.40, 'Vesu, Surat'),
(11, 'Arjun Verma',         'arjun.verma@college.edu',        '9876500111', @student_pw, '2002-10-11', 'Male',   'IT',  2027, 7.60, 'Gomti Nagar, Lucknow'),
(12, 'Nisha Reddy',         'nisha.reddy@college.edu',        '9876500112', @student_pw, '2003-05-09', 'Female', 'ECE', 2027, 8.10, 'Whitefield, Bengaluru'),
(13, 'Karan Malhotra',      'karan.malhotra@college.edu',     '9876500113', @student_pw, '2003-12-02', 'Male',   'MCA', 2027, 7.20, 'Sector 17, Chandigarh'),
(14, 'Priya Menon',         'priya.menon@college.edu',        '9876500114', @student_pw, '2003-02-22', 'Female', 'CSE', 2027, 8.70, 'Edappally, Kochi'),
(15, 'Siddharth Kulkarni',  'siddharth.kulkarni@college.edu', '9876500115', @student_pw, '2002-09-16', 'Male',   'MCA', 2027, 6.80, 'Baner, Pune'),
(16, 'Tanvi Bhat',          'tanvi.bhat@college.edu',         '9876500116', @student_pw, '2003-04-03', 'Female', 'IT',  2027, 9.00, 'Kadri, Mangaluru'),
(17, 'Rahul Yadav',         'rahul.yadav@college.edu',        '9876500117', @student_pw, '2003-08-29', 'Male',   'ECE', 2027, 6.20, 'Sector 62, Noida'),
(18, 'Sneha Pillai',        'sneha.pillai@college.edu',       '9876500118', @student_pw, '2003-10-07', 'Female', 'MCA', 2027, 8.40, 'Kazhakkoottam, Thiruvananthapuram'),
(19, 'Devang Shah',         'devang.shah@college.edu',        '9876500119', @student_pw, '2002-06-13', 'Male',   'CSE', 2027, 7.00, 'Satellite, Ahmedabad'),
(20, 'Aisha Khan',          'aisha.khan@college.edu',         '9876500120', @student_pw, '2003-03-30', 'Female', 'IT',  2027, 8.80, 'Arera Colony, Bhopal');


INSERT INTO Company
  (Company_ID, Company_Name, Industry, Location, HR_Name, HR_Email,
   Contact_Number, Website, Password_Hash, Approval_Status)
VALUES
(1, 'TechNova Solutions',    'IT Services',        'Pune',      'Ritu Malhotra',      'hr@technova.example.com',    '02040010001', 'https://technova.example.com',   @recruiter_pw, 'Approved'),
(2, 'DataBridge Analytics',  'Data & Analytics',   'Bengaluru', 'Sandeep Rao',        'careers@databridge.example.com', '08040010002', 'https://databridge.example.com', @recruiter_pw, 'Approved'),
(3, 'CloudWorks Systems',    'Cloud Computing',    'Hyderabad', 'Neha Gupta',         'talent@cloudworks.example.com',  '04040010003', 'https://cloudworks.example.com', @recruiter_pw, 'Approved'),
(4, 'FinEdge Consulting',    'BFSI Consulting',    'Mumbai',    'Vikram Shah',        'hr@finedge.example.com',     '02240010004', 'https://finedge.example.com',    @recruiter_pw, 'Approved'),
(5, 'GreenByte Technologies','Product Engineering', 'Chennai',   'Lakshmi Narayanan',  'people@greenbyte.example.com','04440010005', 'https://greenbyte.example.com',  @recruiter_pw, 'Approved');


INSERT INTO Placement_Officer
  (Officer_ID, Name, Email, Contact_Number, Designation, Password_Hash, Account_Role)
VALUES
(1, 'Dr. Suresh Kulkarni', 'suresh.kulkarni@college.edu', '9822001001', 'Training & Placement Officer', @officer_pw, 'Officer'),
(2, 'Prof. Anita Deshmukh', 'anita.deshmukh@college.edu', '9822001002', 'Assistant Placement Officer',  @officer_pw, 'Officer'),
(3, 'Dr. Rajesh Khanna',    'admin@college.edu',          '9822001003', 'Dean - Student Affairs',       @admin_pw,   'Admin');


INSERT INTO Job
  (Job_ID, Company_ID, Job_Title, Job_Description, Eligible_Branch,
   Min_CGPA, Salary_Package, Job_Location, Application_Deadline, Job_Type)
VALUES
(1, 1, 'Software Engineer Trainee',
 'Work with senior engineers on web application development, write clean Python and JavaScript code, and complete a six-month structured training programme.',
 'MCA,CSE,IT', 7.00, 6.50, 'Pune', '2026-12-15', 'Full-Time'),
(2, 1, 'QA Engineer',
 'Design and execute manual and automated test cases for enterprise web applications. Familiarity with Selenium or Playwright is an advantage.',
 'MCA,CSE,IT', 6.50, 5.00, 'Pune', '2026-12-20', 'Full-Time'),
(3, 2, 'Data Analyst',
 'Build dashboards, write SQL queries and present business insights to client teams. Strong Excel and Python skills preferred.',
 'MCA,CSE,IT', 7.50, 8.00, 'Bengaluru', '2026-12-10', 'Full-Time'),
(4, 2, 'Data Engineering Intern',
 'Six-month internship on ETL pipelines and cloud data warehouses. High performers receive a full-time offer.',
 'MCA,CSE', 7.00, 3.60, 'Bengaluru', '2026-11-30', 'Internship'),
(5, 3, 'Cloud Support Associate',
 'Support enterprise cloud customers, troubleshoot infrastructure issues and document resolution steps. AWS or Azure certification is a plus.',
 'MCA,CSE,IT', 6.50, 5.50, 'Hyderabad', '2027-01-10', 'Full-Time'),
(6, 3, 'DevOps Engineer',
 'Automate CI/CD pipelines, manage Kubernetes clusters and improve platform reliability with the infrastructure team.',
 'MCA,CSE,IT', 7.20, 9.00, 'Hyderabad', '2027-01-15', 'Full-Time'),
(7, 4, 'Business Analyst',
 'Gather requirements from banking clients, prepare functional specifications and support UAT for digital transformation projects.',
 'All', 6.00, 7.50, 'Mumbai', '2026-10-30', 'Full-Time'),
(8, 4, 'Risk Analytics Associate',
 'Build credit-risk models, validate data quality and prepare regulatory reports for BFSI clients.',
 'MCA,CSE,IT', 8.00, 10.50, 'Mumbai', '2027-01-05', 'Full-Time'),
(9, 5, 'Full Stack Developer',
 'Develop React front ends and Flask APIs for a SaaS product. Candidates should have a strong project portfolio.',
 'MCA,CSE,IT', 7.00, 8.50, 'Chennai', '2026-12-28', 'Full-Time'),
(10, 5, 'Embedded Systems Engineer',
 'Work on firmware for IoT devices using C and RTOS. Exposure to ARM microcontrollers is expected.',
 'ECE,EEE', 6.00, 6.00, 'Chennai', '2026-11-25', 'Full-Time');


INSERT INTO Recruitment_Round
  (Round_ID, Job_ID, Round_Name, Round_Type, Round_Date, Max_Marks)
VALUES
(1,  1,  'Round 1 - Aptitude',        'Aptitude',        '2026-09-28', 100.00),
(2,  1,  'Round 2 - Technical',       'Technical',       '2026-10-02',  50.00),
(3,  1,  'Round 3 - HR',              'HR',              '2026-10-04',  25.00),
(4,  2,  'Round 1 - Aptitude',        'Aptitude',        '2026-10-01', 100.00),
(5,  2,  'Round 2 - Technical',       'Technical',       '2026-10-04',  50.00),
(6,  3,  'Round 1 - Aptitude',        'Aptitude',        '2026-09-30', 100.00),
(7,  3,  'Round 2 - Case Study',      'Technical',       '2026-10-03',  50.00),
(8,  4,  'Coding Assessment',         'Coding',          '2026-11-20', 100.00),
(9,  5,  'Round 1 - Aptitude',        'Aptitude',        '2026-10-18', 100.00),
(10, 5,  'Round 2 - Technical',       'Technical',       '2026-10-22',  50.00),
(11, 6,  'Round 1 - Coding',          'Coding',          '2026-10-10', 100.00),
(12, 6,  'Round 2 - System Design',   'Technical',       '2026-10-14',  50.00),
(13, 6,  'Round 3 - HR',              'HR',              '2026-10-16',  25.00),
(14, 7,  'Round 1 - Aptitude',        'Aptitude',        '2026-10-10', 100.00),
(15, 7,  'Round 2 - HR',              'HR',              '2026-10-14',  25.00),
(16, 8,  'Round 1 - Aptitude',        'Aptitude',        '2026-10-12', 100.00),
(17, 8,  'Round 2 - Analytics Case',  'Technical',       '2026-10-16',  50.00),
(18, 8,  'Round 3 - HR',              'HR',              '2026-10-18',  25.00),
(19, 9,  'Round 1 - Coding',          'Coding',          '2026-10-15', 100.00),
(20, 9,  'Round 2 - Technical',       'Technical',       '2026-10-20',  50.00),
(21, 9,  'Round 3 - HR',              'HR',              '2026-10-24',  25.00),
(22, 10, 'Round 1 - Aptitude',        'Aptitude',        '2026-10-20', 100.00),
(23, 10, 'Round 2 - Technical',       'Technical',       '2026-10-25',  50.00),
(24, 3,  'Round 3 - HR Discussion',   'HR',              '2026-11-20',  25.00);


INSERT INTO Application
  (Application_ID, Student_ID, Job_ID, Application_Date, Status)
VALUES
(1,  1,  1,  '2026-09-20', 'Selected'),
(2,  2,  3,  '2026-09-22', 'Selected'),
(3,  4,  6,  '2026-09-25', 'Selected'),
(4,  10, 8,  '2026-09-27', 'Selected'),
(5,  16, 9,  '2026-10-01', 'Selected'),
(6,  18, 1,  '2026-10-03', 'Selected'),
(7,  3,  5,  '2026-10-05', 'Selected'),
(8,  14, 2,  '2026-10-06', 'Selected'),
(9,  14, 9,  '2026-10-07', 'Selected'),
(10, 12, 10, '2026-10-08', 'Selected'),
(11, 1,  3,  '2026-09-21', 'Rejected'),
(12, 2,  1,  '2026-09-23', 'Shortlisted'),
(13, 3,  9,  '2026-09-28', 'Under Review'),
(14, 4,  3,  '2026-09-29', 'Interview Scheduled'),
(15, 5,  2,  '2026-09-30', 'Shortlisted'),
(16, 6,  1,  '2026-10-02', 'Under Review'),
(17, 7,  10, '2026-10-04', 'Interview Scheduled'),
(18, 8,  9,  '2026-10-05', 'Shortlisted'),
(19, 9,  5,  '2026-10-06', 'Applied'),
(20, 11, 6,  '2026-10-07', 'Applied'),
(21, 17, 10, '2026-10-11', 'Rejected'),
(22, 19, 9,  '2026-10-12', 'Shortlisted'),
(23, 20, 3,  '2026-10-13', 'Applied'),
(24, 1,  6,  '2026-10-14', 'Rejected'),
(25, 2,  9,  '2026-10-15', 'Shortlisted'),
(26, 6,  5,  '2026-10-16', 'Interview Scheduled'),
(27, 8,  3,  '2026-10-17', 'Rejected'),
(28, 10, 1,  '2026-10-18', 'Withdrawn'),
(29, 12, 7,  '2026-10-19', 'Applied'),
(30, 16, 3,  '2026-10-20', 'Under Review'),
(31, 18, 9,  '2026-10-21', 'Interview Scheduled'),
(32, 5,  5,  '2026-10-22', 'Applied'),
(33, 9,  2,  '2026-10-23', 'Applied'),
(34, 11, 9,  '2026-10-24', 'Applied'),
(35, 19, 2,  '2026-10-27', 'Shortlisted'),
(36, 20, 9,  '2026-10-28', 'Applied'),
(37, 5,  7,  '2026-10-29', 'Under Review'),
(38, 17, 7,  '2026-10-30', 'Applied'),
(39, 6,  9,  '2026-10-31', 'Applied'),
(40, 3,  7,  '2026-10-30', 'Applied'),
(41, 7,  7,  '2026-10-30', 'Applied'),
(42, 11, 7,  '2026-10-29', 'Applied'),
(43, 19, 1,  '2026-10-30', 'Applied');


INSERT INTO Interview
  (Interview_ID, Application_ID, Round_ID, Interview_Date, Result,
   Interviewer_Name, Marks_Obtained, Remarks)
VALUES
(1,  1,  1,  '2026-09-28 10:00', 'Pass', 'Nikhil Menon',      82.00, 'Strong logical reasoning'),
(2,  1,  2,  '2026-10-02 11:00', 'Pass', 'Shreya Kulkarni',   41.00, 'Good Python fundamentals'),
(3,  1,  3,  '2026-10-04 15:00', 'Pass', 'Ritu Malhotra',     22.00, 'Excellent communication'),
(4,  2,  6,  '2026-09-30 10:00', 'Pass', 'Amit Sinha',        88.00, 'Top scorer in aptitude'),
(5,  2,  7,  '2026-10-03 14:00', 'Pass', 'Sandeep Rao',       45.00, 'Clear business thinking'),
(6,  3,  11, '2026-10-10 09:30', 'Pass', 'Neha Gupta',        91.00, 'Clean modular code'),
(7,  3,  12, '2026-10-14 11:00', 'Pass', 'Arvind Nair',       44.00, 'Strong system design basics'),
(8,  3,  13, '2026-10-16 16:00', 'Pass', 'Neha Gupta',        21.00, 'Culture fit confirmed'),
(9,  4,  16, '2026-10-12 10:00', 'Pass', 'Vikram Shah',       86.00, 'Good statistics knowledge'),
(10, 4,  17, '2026-10-16 14:00', 'Pass', 'Meghna Joshi',      46.00, 'Strong case presentation'),
(11, 4,  18, '2026-10-18 12:00', 'Pass', 'Vikram Shah',       23.00, 'Confident and articulate'),
(12, 5,  19, '2026-10-15 09:00', 'Pass', 'Lakshmi Narayanan', 90.00, 'Excellent coding round'),
(13, 5,  20, '2026-10-20 11:30', 'Pass', 'Karthik Raman',     43.00, 'Good API design'),
(14, 5,  21, '2026-10-24 15:30', 'Pass', 'Lakshmi Narayanan', 20.00, 'Ready to join in June'),
(15, 6,  1,  '2026-09-28 11:30', 'Pass', 'Nikhil Menon',      79.00, 'Solid aptitude score'),
(16, 6,  2,  '2026-10-02 12:00', 'Pass', 'Shreya Kulkarni',   38.00, 'Good debugging skills'),
(17, 6,  3,  '2026-10-04 16:30', 'Pass', 'Ritu Malhotra',     20.00, 'Positive attitude'),
(18, 7,  9,  '2026-10-18 10:00', 'Pass', 'Neha Gupta',        75.00, 'Good troubleshooting approach'),
(19, 7,  10, '2026-10-22 11:00', 'Pass', 'Arvind Nair',       36.00, 'Understands networking basics'),
(20, 8,  4,  '2026-10-01 10:00', 'Pass', 'Ritu Malhotra',     84.00, 'Detail oriented'),
(21, 8,  5,  '2026-10-04 13:00', 'Pass', 'Shreya Kulkarni',   39.00, 'Good test design'),
(22, 9,  19, '2026-10-15 11:00', 'Pass', 'Lakshmi Narayanan', 88.00, 'Strong React portfolio'),
(23, 9,  20, '2026-10-20 14:00', 'Pass', 'Karthik Raman',     41.00, 'Good Flask API knowledge'),
(24, 9,  21, '2026-10-24 17:00', 'Pass', 'Lakshmi Narayanan', 19.00, 'Offer discussed'),
(25, 10, 22, '2026-10-20 10:00', 'Pass', 'Lakshmi Narayanan', 80.00, 'Good embedded basics'),
(26, 10, 23, '2026-10-25 11:00', 'Pass', 'Karthik Raman',     37.00, 'Knows RTOS concepts'),
(27, 12, 1,  '2026-09-28 12:00', 'Pass', 'Nikhil Menon',      85.00, 'Shortlisted for technical'),
(28, 12, 2,  '2026-11-16 10:00', 'Pending', 'Shreya Kulkarni', NULL, 'Rescheduled at student request'),
(29, 14, 6,  '2026-09-30 12:00', 'Pass', 'Amit Sinha',        81.00, 'Moved to case study'),
(30, 14, 24, '2026-11-20 15:00', 'Pending', 'Sandeep Rao',      NULL, 'Final HR discussion'),
(31, 15, 4,  '2026-10-01 11:00', 'Pass', 'Ritu Malhotra',     78.00, 'Shortlisted for technical'),
(32, 17, 22, '2026-10-20 12:00', 'Pass', 'Lakshmi Narayanan', 77.00, 'Good fundamentals'),
(33, 17, 23, '2026-11-18 10:00', 'Pending', 'Karthik Raman',    NULL, 'Technical interview rescheduled'),
(34, 26, 9,  '2026-10-18 13:00', 'Pass', 'Neha Gupta',        72.00, 'Shortlisted for technical'),
(35, 26, 10, '2026-11-20 11:00', 'Pending', 'Arvind Nair',      NULL, 'Technical round scheduled'),
(36, 27, 6,  '2026-09-30 14:00', 'Fail', 'Amit Sinha',        48.00, 'Did not meet minimum cutoff'),
(37, 31, 19, '2026-10-15 14:00', 'Pass', 'Lakshmi Narayanan', 83.00, 'Strong coding score'),
(38, 31, 20, '2026-11-22 10:00', 'Pending', 'Karthik Raman',    NULL, 'Technical round scheduled');


INSERT INTO Placement
  (Placement_ID, Student_ID, Job_ID, Company_ID, Placement_Date,
   Package_Offered, Joining_Date, Status)
VALUES
(1,  1,  1,  1, '2026-10-05',  6.50, '2027-06-15', 'Offer Accepted'),
(2,  2,  3,  2, '2026-10-18',  8.00, '2027-07-01', 'Offer Accepted'),
(3,  4,  6,  3, '2026-10-25',  9.00, '2027-06-20', 'Offer Accepted'),
(4,  10, 8,  4, '2026-10-28', 10.50, '2027-07-05', 'Offer Accepted'),
(5,  16, 9,  5, '2026-11-02',  8.50, '2027-06-25', 'Offer Released'),
(6,  18, 1,  1, '2026-11-05',  6.50, '2027-06-15', 'Offer Released'),
(7,  3,  5,  3, '2026-11-06',  5.50, '2027-06-30', 'Offer Accepted'),
(8,  14, 2,  1, '2026-11-08',  5.00, '2027-06-15', 'Offer Declined'),
(9,  14, 9,  5, '2026-11-09',  8.50, '2027-06-25', 'Offer Accepted'),
(10, 12, 10, 5, '2026-11-10',  6.00, '2027-07-10', 'Offer Released');


INSERT INTO Report
  (Report_ID, Report_Type, Generated_Date, Generated_By, Description)
VALUES
(1, 'Placement Summary',   '2026-11-01 10:00', 1, 'Campus placement summary for the 2026-27 season.'),
(2, 'Branch-wise Report',  '2026-11-02 11:30', 1, 'Branch-wise placement percentage and average package.'),
(3, 'Company-wise Report', '2026-11-03 09:45', 3, 'Company participation and selection statistics for the Dean.'),
(4, 'Unplaced Students',   '2026-11-04 16:00', 2, 'List of students still looking for a placement, for follow-up.'),
(5, 'Recruitment Summary', '2026-11-05 12:15', 1, 'Application funnel and interview activity for the season.');

COMMIT;

-- Quick verification
SELECT 'Students' AS Table_Name, COUNT(*) AS Rows_Loaded FROM Student
UNION ALL SELECT 'Companies', COUNT(*) FROM Company
UNION ALL SELECT 'Jobs', COUNT(*) FROM Job
UNION ALL SELECT 'Applications', COUNT(*) FROM Application
UNION ALL SELECT 'Rounds', COUNT(*) FROM Recruitment_Round
UNION ALL SELECT 'Interviews', COUNT(*) FROM Interview
UNION ALL SELECT 'Placements', COUNT(*) FROM Placement
UNION ALL SELECT 'Officers', COUNT(*) FROM Placement_Officer
UNION ALL SELECT 'Reports', COUNT(*) FROM Report;
