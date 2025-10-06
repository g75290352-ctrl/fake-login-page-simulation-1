import sqlite3

DB_NAME = "users.db"

# Connect to DB
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# ALTER TABLE: verified column add karna
try:
    c.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
    print("✅ 'verified' column successfully added!")
except sqlite3.OperationalError as e:
    print("⚠️ Column may already exist or another error:", e)

conn.commit()
conn.close()
