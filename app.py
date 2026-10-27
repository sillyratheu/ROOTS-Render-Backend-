from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "roots_secret_key_12345"  # সেশন সিকিউরিটির জন্য


# ডাটাবেজ ইনিশিয়ালাইজেশন
def init_db():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()

  # স্টুডেন্ট টেবিল
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            status TEXT DEFAULT 'pending', -- 'pending' or 'approved'
            progress INTEGER DEFAULT 0
        )
    """)

  # কোর্স/শিট টেবিল (বড় চাচা যা আপলোড করবেন)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            file_link TEXT
        )
    """)

  # রেফারেল টেবিল
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            friend_name TEXT,
            friend_phone TEXT
        )
    """)

  conn.commit()
  conn.close()


# --- Routes ---


@app.route("/Dashboard")
def dashboard():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM courses")
  courses = cursor.fetchall()
  conn.close()
  return render_template("dashboard.html", courses=courses)


@app.route("/studentpanel", methods=["GET", "POST"])
def student_panel():
  student = None
  if "student_email" in session:
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM students WHERE email = ?", (session["student_email"],)
    )
    student = cursor.fetchone()
    conn.close()

  return render_template("studentpanel.html", student=student)


# সিমুলেটেড Google Login / Signup
@app.route("/student-login", methods=["POST"])
def student_login():
  name = request.form.get("name")
  email = request.form.get("email")

  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
  existing = cursor.fetchone()

  if not existing:
    # নতুন অ্যাকাউন্ট ১ দিনের জন্য 'pending' থাকবে
    cursor.execute(
        "INSERT INTO students (name, email, status, progress) VALUES (?, ?,"
        " 'pending', 10)",
        (name, email),
    )
    conn.commit()

  conn.close()
  session["student_email"] = email
  return redirect(url_for("student_panel"))


@app.route("/student-logout")
def student_logout():
  session.pop("student_email", None)
  return redirect(url_for("student_panel"))


@app.route("/teacherpanel", methods=["GET", "POST"])
def teacher_panel():
  error = None
  if request.method == "POST":
    teacher_id = request.form.get("teacher_id")
    password = request.form.get("password")

    # সিক্রেট আইডি ও পাসওয়ার্ড (তুমি আর চাচা জানবে)
    if teacher_id == "roots_admin" and password == "chacha123":
      session["is_teacher"] = True
      return redirect(url_for("teacher_dashboard"))
    else:
      error = "Invalid Teacher ID or Password!"

  return render_template("teacherpanel.html", error=error)


@app.route("/teacher/dashboard", methods=["GET", "POST"])
def teacher_dashboard():
  if not session.get("is_teacher"):
    return redirect(url_for("teacher_panel"))

  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()

  if request.method == "POST":
    action = request.form.get("action")

    if action == "add_course":
      title = request.form.get("title")
      desc = request.form.get("desc")
      link = request.form.get("link")
      cursor.execute(
          "INSERT INTO courses (title, description, file_link) VALUES (?, ?, ?)",
          (title, desc, link),
      )
      conn.commit()

    elif action == "approve":
      student_id = request.form.get("student_id")
      cursor.execute(
          "UPDATE students SET status = 'approved' WHERE id = ?", (student_id,)
      )
      conn.commit()

    elif action == "delete":
      student_id = request.form.get("student_id")
      cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
      conn.commit()

  cursor.execute("SELECT * FROM students")
  students = cursor.fetchall()
  cursor.execute("SELECT * FROM courses")
  courses = cursor.fetchall()
  conn.close()

  return render_template(
      "teacher_dashboard.html", students=students, courses=courses
  )


@app.route("/teacher-logout")
def teacher_logout():
  session.pop("is_teacher", None)
  return redirect(url_for("teacher_panel"))


@app.route("/info", methods=["GET", "POST"])
def info_page():
  success = None
  if request.method == "POST":
    student_name = request.form.get("student_name")
    friend_name = request.form.get("friend_name")
    friend_phone = request.form.get("friend_phone")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO referrals (student_name, friend_name, friend_phone) VALUES"
        " (?, ?, ?)",
        (student_name, friend_name, friend_phone),
    )
    conn.commit()
    conn.close()
    success = "Referral submitted successfully! Your reward is on the way."

  return render_template("info.html", success=success)


if __name__ == "__main__":
  init_db()
  app.run(host="0.0.0.0", port=5000, debug=True)
