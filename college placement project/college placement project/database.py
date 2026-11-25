import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "college_placement_db"),
    "autocommit": False,
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def query_all(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def query_one(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid, cursor.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def create_placement(student_id, job_id, company_id, package, joining_date, status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        cursor.execute(
            """
            INSERT INTO Placement
                (Student_ID, Job_ID, Company_ID, Placement_Date,
                 Package_Offered, Joining_Date, Status)
            VALUES (%s, %s, %s, CURDATE(), %s, %s, %s)
            """,
            (student_id, job_id, company_id, package, joining_date, status),
        )
        placement_id = cursor.lastrowid
        cursor.execute(
            """
            UPDATE Application
            SET Status = 'Selected'
            WHERE Student_ID = %s AND Job_ID = %s
            """,
            (student_id, job_id),
        )
        conn.commit()
        return placement_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_placement(placement_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cursor.execute(
            "SELECT Student_ID, Job_ID FROM Placement WHERE Placement_ID = %s FOR UPDATE",
            (placement_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.rollback()
            return False

        cursor.execute("DELETE FROM Placement WHERE Placement_ID = %s", (placement_id,))
        cursor.execute(
            """
            UPDATE Application
            SET Status = 'Shortlisted'
            WHERE Student_ID = %s AND Job_ID = %s AND Status = 'Selected'
            """,
            (row["Student_ID"], row["Job_ID"]),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
