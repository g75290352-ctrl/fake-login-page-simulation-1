import sqlite3

DB_NAME = "users.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # users table banaye agar exist na kare
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')

    # ek default user insert karo agar already nahi hai to
    c.execute("SELECT * FROM users WHERE email=?", ("test@test.com",))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@test.com", "12345"))

    conn.commit()
    conn.close()
    print("✅ Database ready! Default user: test@test.com | Password: 12345")

if __name__ == "__main__":
    create_db()
