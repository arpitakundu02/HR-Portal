import os
import pymysql
from dotenv import load_dotenv

def main():
    # Load environment variables
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
    load_dotenv(env_path)

    db_host = os.environ.get("DB_HOST", "localhost")
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "hr_portal")
    db_port = int(os.environ.get("DB_PORT", "3306"))

    print(f"Connecting to database '{db_name}' at {db_host}:{db_port} as user '{db_user}'...\n")

    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            # 1. Total holiday count currently stored
            cursor.execute("SELECT COUNT(*) AS total FROM holidays")
            total_count = cursor.fetchone()['total']
            print(f"=== 1. Total Holiday Count: {total_count} ===\n")

            # 2. Holidays grouped by year
            cursor.execute("SELECT YEAR(date) AS year, COUNT(*) AS count FROM holidays GROUP BY YEAR(date) ORDER BY year")
            year_groups = cursor.fetchall()
            print("=== 2. Holidays Grouped by Year ===")
            for row in year_groups:
                print(f"  Year {row['year']}: {row['count']} holidays")
            print()

            # 3. First 10 holiday records
            cursor.execute("SELECT id, name, date, description FROM holidays ORDER BY date ASC LIMIT 10")
            first_10 = cursor.fetchall()
            print("=== 3. First 10 Holiday Records ===")
            print(f"{'ID':<5} | {'Date':<10} | {'Name':<30} | {'Description'}")
            print("-" * 75)
            for row in first_10:
                desc = row['description'] if row['description'] else "None"
                print(f"{row['id']:<5} | {str(row['date']):<10} | {row['name']:<30} | {desc}")
            print()

            # 4 & 5. Check current (2026) and next (2027) year existence
            cursor.execute("SELECT COUNT(*) AS count FROM holidays WHERE YEAR(date) = 2026")
            count_2026 = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) AS count FROM holidays WHERE YEAR(date) = 2027")
            count_2027 = cursor.fetchone()['count']

            print("=== 4 & 5. Year Verification ===")
            print(f"  Current year (2026) holidays exist? {'YES (' + str(count_2026) + ' records)' if count_2026 > 0 else 'NO'}")
            print(f"  Next year (2027) holidays exist?    {'YES (' + str(count_2027) + ' records)' if count_2027 > 0 else 'NO'}")
            print()

    finally:
        conn.close()

if __name__ == '__main__':
    main()
