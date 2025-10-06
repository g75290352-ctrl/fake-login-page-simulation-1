from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os, bcrypt, smtplib, random
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "users.db"

# --- Database Setup ---
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        verified INTEGER DEFAULT 0
                    )''')
        conn.commit()
        conn.close()

# --- Email Sending Function ---
def send_email(to_email, subject, body):
    sender_email = "yourgmail@gmail.com"   # apna Gmail daalo
    app_password = "your_app_password"     # Gmail app password yahan daalo

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, msg.as_string())

# ===== ROUTES =====

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password, verified FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode("utf-8"), user[0]):
        if user[1] == 0:
            return render_template("login.html", message="⚠️ Please verify your email first.")
        session["user"] = email
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", message="❌ Invalid Email or Password")

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    else:
        return redirect(url_for("home"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        otp = str(random.randint(100000, 999999))  # 6-digit OTP

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password, verified) VALUES (?, ?, ?)", (email, hashed_pw, 0))
            conn.commit()
            conn.close()

            # ✅ Send OTP Email
            send_email(email, "Email Verification OTP", f"Your OTP is {otp}")

            # Save OTP in session
            session["pending_user"] = email
            session["otp"] = otp

            return redirect(url_for("verify"))
        except sqlite3.IntegrityError:
            return render_template("signup.html", message="⚠️ Email already exists.")
    return render_template("signup.html")

# ===== Combined Verify Route =====
@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        # OTP verification
        if "otp" in request.form:
            otp_entered = request.form["otp"]
            if otp_entered == session.get("otp"):
                email = session.get("pending_user")
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("UPDATE users SET verified=1 WHERE email=?", (email,))
                conn.commit()
                conn.close()

                session.pop("pending_user", None)
                session.pop("otp", None)

                return render_template("login.html", message="✅ Email verified! Please login.")
            else:
                return render_template("verify.html", message="❌ Invalid OTP.")

        # Manual email verification
        elif "email" in request.form:
            email = request.form["email"]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            if user:
                c.execute("UPDATE users SET verified=1 WHERE email=?", (email,))
                conn.commit()
                conn.close()
                return render_template("login.html", message="✅ Email manually verified! Please login.")
            else:
                conn.close()
                return render_template("verify.html", message="❌ Email not found.")

    return render_template("verify.html")

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["new_password"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        if user:
            hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            c.execute("UPDATE users SET password=? WHERE email=?", (hashed_pw, email))
            conn.commit()
            conn.close()
            return render_template("login.html", message="🔑 Password reset successful. Please login.")
        else:
            conn.close()
            return render_template("forgot.html", message="❌ Email not found.")
    return render_template("forgot.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# ===== MAIN =====
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
