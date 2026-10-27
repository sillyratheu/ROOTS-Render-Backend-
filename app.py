from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "roots_english_institute_secure_secret_key"

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            student_class TEXT,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 10
        )
    ''')
    
    # Courses / PDF Sheets Table (with Photo & PDF Link)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            photo_link TEXT,
            pdf_link TEXT,
            batch_tag TEXT
        )
    ''')

    # Announcements Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

# Dashboard Page (Coursera Style Course Cards & Announcements)
@app.route('/Dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    cursor.execute("SELECT * FROM announcements")
    announcements = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', courses=courses, announcements=announcements)

# Student Portal & Google Sign-in Flow
@app.route('/studentpanel', methods=['GET', 'POST'])
def student_panel():
    student = None
    if 'student_email' in session:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (session['student_email'],))
        student = cursor.fetchone()
        conn.close()
    return render_template('student.html', student=student)

@app.route('/student-login', methods=['POST'])
def student_login():
    name = request.form.get('name')
    email = request.form.get('email')
    student_class = request.form.get('student_class')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute("INSERT INTO students (name, email, student_class, status, progress) VALUES (?, ?, ?, 'pending', 15)", 
                       (name, email, student_class))
        conn.commit()
    
    conn.close()
    session['student_email'] = email
    return redirect(url_for('student_panel'))

@app.route('/student-logout')
def student_logout():
    session.pop('student_email', None)
    return redirect(url_for('student_panel'))

# Teacher Panel Login (ID: 123454, Pass: mithu123@teacher)
@app.route('/teacherpanel', methods=['GET', 'POST'])
def teacher_panel():
    error = None
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        password = request.form.get('password')
        
        if teacher_id == '123454' and password == 'mithu123@teacher':
            session['is_teacher'] = True
            return redirect(url_for('teacher_dashboard'))
        else:
            error = "Invalid Teacher ID or Password!"
            
    return render_template('teacherpanel.html', error=error)

# Teacher Control Dashboard (Manage Students, Progress, Courses, Announcements)
@app.route('/teacher/dashboard', methods=['GET', 'POST'])
def teacher_dashboard():
    if not session.get('is_teacher'):
        return redirect(url_for('teacher_panel'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_course':
            title = request.form.get('title')
            desc = request.form.get('desc')
            photo = request.form.get('photo')
            pdf = request.form.get('pdf')
            tag = request.form.get('tag')
            cursor.execute("INSERT INTO courses (title, description, photo_link, pdf_link, batch_tag) VALUES (?, ?, ?, ?, ?)", 
                           (title, desc, photo, pdf, tag))
            conn.commit()
            
        elif action == 'add_announcement':
            msg = request.form.get('message')
            cursor.execute("INSERT INTO announcements (message) VALUES (?)", (msg,))
            conn.commit()

        elif action == 'approve':
            student_id = request.form.get('student_id')
            cursor.execute("UPDATE students SET status = 'approved' WHERE id = ?", (student_id,))
            conn.commit()
            
        elif action == 'update_progress':
            student_id = request.form.get('student_id')
            new_prog = request.form.get('progress')
            cursor.execute("UPDATE students SET progress = ? WHERE id = ?", (new_prog, student_id))
            conn.commit()

        elif action == 'delete_student':
            student_id = request.form.get('student_id')
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()

        elif action == 'delete_course':
            course_id = request.form.get('course_id')
            cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
            
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    cursor.execute("SELECT * FROM announcements")
    announcements = cursor.fetchall()
    conn.close()
    
    return render_template('teacher_dashboard.html', students=students, courses=courses, announcements=announcements)

@app.route('/teacher-logout')
def teacher_logout():
    session.pop('is_teacher', None)
    return redirect(url_for('teacher_panel'))

# Info Page
@app.route('/info')
def info_page():
    return render_template('info.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
