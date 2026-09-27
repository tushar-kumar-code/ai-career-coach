import sqlite3, os

db_path = "aicareercoach.db"
if not os.path.exists(db_path):
    print("DB not found at:", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(assessment_responses)")
columns = [row[1] for row in cursor.fetchall()]
print("Existing columns:", columns)

if "user_level" not in columns:
    cursor.execute('ALTER TABLE assessment_responses ADD COLUMN user_level TEXT DEFAULT "beginner"')
    conn.commit()
    print("SUCCESS: user_level column added")
else:
    print("Column already exists, skipping")

conn.close()
