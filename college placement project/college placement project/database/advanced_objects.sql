

USE college_placement_db;


DROP VIEW IF EXISTS vw_job_details;
CREATE VIEW vw_job_details AS
SELECT j.Job_ID, j.Job_Title, j.Job_Location, j.Salary_Package,
       j.Min_CGPA, j.Eligible_Branch, j.Application_Deadline, j.Job_Type,
       c.Company_ID, c.Company_Name, c.Industry,
       (SELECT COUNT(*) FROM Application a WHERE a.Job_ID = j.Job_ID) AS Application_Count,
       (SELECT COUNT(*) FROM Recruitment_Round r WHERE r.Job_ID = j.Job_ID) AS Round_Count
FROM Job j
JOIN Company c ON c.Company_ID = j.Company_ID;

DROP VIEW IF EXISTS vw_student_applications;
CREATE VIEW vw_student_applications AS
SELECT a.Application_ID, a.Application_Date, a.Status,
       s.Student_ID, s.Name AS Student_Name, s.Branch, s.CGPA, s.Batch_Year,
       j.Job_ID, j.Job_Title, j.Salary_Package,
       c.Company_ID, c.Company_Name
FROM Application a
JOIN Student s ON s.Student_ID = a.Student_ID
JOIN Job j ON j.Job_ID = a.Job_ID
JOIN Company c ON c.Company_ID = j.Company_ID;

DROP VIEW IF EXISTS vw_branch_placement_stats;
CREATE VIEW vw_branch_placement_stats AS
SELECT s.Branch,
       COUNT(DISTINCT s.Student_ID) AS Total_Students,
       COUNT(DISTINCT CASE WHEN p.Status IN ('Offer Accepted','Joined')
                           THEN p.Student_ID END) AS Placed_Students,
       ROUND(COUNT(DISTINCT CASE WHEN p.Status IN ('Offer Accepted','Joined')
                                 THEN p.Student_ID END) * 100.0
             / NULLIF(COUNT(DISTINCT s.Student_ID), 0), 2) AS Placement_Percentage,
       COALESCE(ROUND(AVG(CASE WHEN p.Status IN ('Offer Accepted','Joined')
                               THEN p.Package_Offered END), 2), 0) AS Avg_Package
FROM Student s
LEFT JOIN Placement p ON p.Student_ID = s.Student_ID
GROUP BY s.Branch;

DROP VIEW IF EXISTS vw_company_selection_stats;
CREATE VIEW vw_company_selection_stats AS
SELECT c.Company_ID, c.Company_Name, c.Industry, c.Location,
       (SELECT COUNT(*) FROM Job j WHERE j.Company_ID = c.Company_ID) AS Total_Jobs,
       (SELECT COUNT(*) FROM Application a
         JOIN Job j ON j.Job_ID = a.Job_ID
        WHERE j.Company_ID = c.Company_ID) AS Total_Applications,
       (SELECT COUNT(*) FROM Placement p
        WHERE p.Company_ID = c.Company_ID
          AND p.Status IN ('Offer Accepted','Joined')) AS Total_Selections,
       (SELECT COALESCE(ROUND(AVG(p.Package_Offered), 2), 0)
          FROM Placement p
         WHERE p.Company_ID = c.Company_ID
           AND p.Status IN ('Offer Accepted','Joined')) AS Avg_Package
FROM Company c;

DROP VIEW IF EXISTS vw_unplaced_students;
CREATE VIEW vw_unplaced_students AS
SELECT s.Student_ID, s.Name, s.Email, s.Phone, s.Branch, s.Batch_Year, s.CGPA
FROM Student s
WHERE NOT EXISTS (
    SELECT 1 FROM Placement p
    WHERE p.Student_ID = s.Student_ID
      AND p.Status IN ('Offer Accepted','Joined')
);


DROP FUNCTION IF EXISTS fn_placement_percentage;
DELIMITER $$
CREATE FUNCTION fn_placement_percentage()
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_total  INT DEFAULT 0;
    DECLARE v_placed INT DEFAULT 0;

    SELECT COUNT(*) INTO v_total FROM Student;
    SELECT COUNT(DISTINCT Student_ID) INTO v_placed
    FROM Placement
    WHERE Status IN ('Offer Accepted','Joined');

    IF v_total = 0 THEN
        RETURN 0.00;
    END IF;
    RETURN ROUND(v_placed * 100.0 / v_total, 2);
END$$
DELIMITER ;


DROP PROCEDURE IF EXISTS sp_eligible_students;
DELIMITER $$
CREATE PROCEDURE sp_eligible_students(IN p_job_id INT)
BEGIN
    SELECT s.Student_ID, s.Name, s.Branch, s.Batch_Year, s.CGPA, s.Email,
           EXISTS(SELECT 1 FROM Application a
                  WHERE a.Student_ID = s.Student_ID
                    AND a.Job_ID = p_job_id) AS Already_Applied
    FROM Student s
    JOIN Job j ON j.Job_ID = p_job_id
    WHERE s.CGPA >= j.Min_CGPA
      AND (j.Eligible_Branch = 'All'
           OR FIND_IN_SET(s.Branch, j.Eligible_Branch) > 0)
    ORDER BY s.CGPA DESC;
END$$
DELIMITER ;


DROP PROCEDURE IF EXISTS sp_company_selection_summary;
DELIMITER $$
CREATE PROCEDURE sp_company_selection_summary()
BEGIN
    SELECT c.Company_Name,
           COUNT(DISTINCT j.Job_ID) AS Jobs,
           COUNT(DISTINCT a.Application_ID) AS Applications,
           COUNT(DISTINCT CASE WHEN p.Status IN ('Offer Accepted','Joined')
                               THEN p.Placement_ID END) AS Selections,
           COALESCE(ROUND(AVG(CASE WHEN p.Status IN ('Offer Accepted','Joined')
                                   THEN p.Package_Offered END), 2), 0) AS Avg_Package
    FROM Company c
    LEFT JOIN Job j ON j.Company_ID = c.Company_ID
    LEFT JOIN Application a ON a.Job_ID = j.Job_ID
    LEFT JOIN Placement p ON p.Student_ID = a.Student_ID AND p.Job_ID = a.Job_ID
    GROUP BY c.Company_ID, c.Company_Name
    ORDER BY Selections DESC, c.Company_Name;
END$$
DELIMITER ;


DROP TRIGGER IF EXISTS trg_placement_company_check;
DELIMITER $$
CREATE TRIGGER trg_placement_company_check
BEFORE INSERT ON Placement
FOR EACH ROW
BEGIN
    DECLARE v_company INT UNSIGNED;
    SELECT Company_ID INTO v_company FROM Job WHERE Job_ID = NEW.Job_ID;
    IF v_company <> NEW.Company_ID THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Placement.Company_ID does not match the job company';
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_placement_company_check_update;
DELIMITER $$
CREATE TRIGGER trg_placement_company_check_update
BEFORE UPDATE ON Placement
FOR EACH ROW
BEGIN
    DECLARE v_company INT UNSIGNED;
    SELECT Company_ID INTO v_company FROM Job WHERE Job_ID = NEW.Job_ID;
    IF v_company <> NEW.Company_ID THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Placement.Company_ID does not match the job company';
    END IF;
END$$
DELIMITER ;


DROP TRIGGER IF EXISTS trg_application_deadline_check;
DELIMITER $$
CREATE TRIGGER trg_application_deadline_check
BEFORE INSERT ON Application
FOR EACH ROW
BEGIN
    DECLARE v_deadline DATE;
    SELECT Application_Deadline INTO v_deadline FROM Job WHERE Job_ID = NEW.Job_ID;
    IF NEW.Application_Date > v_deadline THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'The application deadline for this job has passed';
    END IF;
END$$
DELIMITER ;


DROP TRIGGER IF EXISTS trg_placement_select_application;
DELIMITER $$
CREATE TRIGGER trg_placement_select_application
AFTER INSERT ON Placement
FOR EACH ROW
BEGIN
    UPDATE Application
    SET Status = 'Selected'
    WHERE Student_ID = NEW.Student_ID
      AND Job_ID = NEW.Job_ID;
END$$
DELIMITER ;

SELECT fn_placement_percentage() AS College_Placement_Percentage;

CALL sp_eligible_students(1);

CALL sp_company_selection_summary();

SELECT * FROM vw_branch_placement_stats;
SELECT * FROM vw_company_selection_stats;
SELECT * FROM vw_unplaced_students;
