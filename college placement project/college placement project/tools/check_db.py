import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB_CONFIG, get_connection

TABLES = [
    "Student",
    "Company",
    "Job",
    "Application",
    "Recruitment_Round",
    "Interview",
    "Placement",
    "Placement_Officer",
    "Report",
]


def main():
    print("Connecting to MySQL ...")
    print(f"  host     : {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  user     : {DB_CONFIG['user']}")
    print(f"  database : {DB_CONFIG['database']}")
    print()

    try:
        conn = get_connection()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        print()
        print("Checklist:")
        print("  1. Is the MySQL80 service running?  (services.msc)")
        print("  2. Does .env exist and is DB_PASSWORD correct?")
        print("  3. Did you run database/schema.sql in MySQL Workbench?")
        return 1

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION(), CURRENT_USER(), DATABASE()")
        version, user, database = cursor.fetchone()
        print(f"[OK]   MySQL {version} as {user} on {database}")
        print()
        print(f"{'Table':<22}{'Rows':>8}")
        print("-" * 30)
        total = 0
        for table in TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            total += count
            print(f"{table:<22}{count:>8}")
        print("-" * 30)
        print(f"{'TOTAL':<22}{total:>8}")

        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = [row[0] for row in cursor.fetchall()]
        print()
        print(f"Views found ({len(views)}): {', '.join(views) if views else 'none'}")

        cursor.execute(
            """
            SELECT ROUTINE_TYPE, ROUTINE_NAME
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = DATABASE()
            ORDER BY ROUTINE_TYPE, ROUTINE_NAME
            """
        )
        routines = cursor.fetchall()
        print(f"Procedures/functions ({len(routines)}):")
        for routine_type, routine_name in routines:
            print(f"  {routine_type:<10} {routine_name}")

        cursor.execute(
            """
            SELECT TRIGGER_NAME
            FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = DATABASE()
            ORDER BY TRIGGER_NAME
            """
        )
        triggers = [row[0] for row in cursor.fetchall()]
        print(f"Triggers ({len(triggers)}): {', '.join(triggers) if triggers else 'none'}")
        cursor.close()
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
