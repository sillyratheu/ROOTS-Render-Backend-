from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "roots_english_institute_secret_2026"


# Database Setup (Student, Courses, Referrals)
def init_db():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 15
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            file_link TEXT
        )
    """)

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


@app.route("/")
def home():
  return redirect(url_for("dashboard"))


# Dashboard Route (Course Materials)
@app.route("/Dashboard")
def dashboard():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM courses")
  courses = cursor.fetchall()
  conn.close()
  return render_template("dashboard.html", courses=courses)


# Student Panel Route
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


# Student Google Login / Create ROOT Account Simulation
@app.route("/student-login", methods=["POST"])
def student_login():
  name = request.form.get("name")
  email = request.form.get("email")

  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
  existing = cursor.fetchone()

  if not existing:
    # 1 দিন বা ডিফল্ট পেন্ডিং স্ট্যাটাস
    cursor.execute(
        "INSERT INTO students (name, email, status, progress) VALUES (?, ?,"
        " 'pending', 15)",
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


# Teacher Panel Login (Secret ID & Password)
@app.route("/teacherpanel", methods=["GET", "POST"])
def teacher_panel():
  error = None
  if request.method == "POST":
    teacher_id = request.form.get("teacher_id")
    password = request.form.get("password")

    # শুধু তুমি আর বড় চাচা জানবে
    if teacher_id == "roots_admin" and password == "chacha123":
      session["is_teacher"] = True
      return redirect(url_for("teacher_dashboard"))
    else:
      error = "Invalid Teacher ID or Password!"

  return render_template("teacherpanel.html", error=error)


# Teacher Control Dashboard (Approve, Delete, Upload PDF)
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


# Info & Refer Page
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
    success = "Referral submitted successfully!"

  return render_template("info.html", success=success)


if __name__ == "__main__":
  init_db()
  app.run(host="0.0.0.0", port=5000, debug=True)