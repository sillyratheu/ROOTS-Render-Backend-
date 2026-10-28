from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "roots_english_institute_secure_secret_key"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            student_class TEXT,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 15
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            photo_filename TEXT,
            pdf_filename TEXT,
            batch_tag TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            target_class TEXT DEFAULT 'All Classes'
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

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

@app.route('/studentpanel', methods=['GET', 'POST'])
def student_panel():
    student = None
    class_announcements = []
    if 'student_email' in session:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (session['student_email'],))
        student = cursor.fetchone()
        
        if student:
            s_class = student[3]
            cursor.execute("SELECT * FROM announcements WHERE target_class = 'All Classes' OR target_class = ?", (s_class,))
            class_announcements = cursor.fetchall()
            
        conn.close()
    return render_template('student.html', student=student, class_announcements=class_announcements)

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

@app.route('/teacherpanel', methods=['GET', 'POST'])
def teacher_panel():
    error = None
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        password = request.form.get('password')
        
        if teacher_id == '123454' and password == 'mithu123@teacher':
            session.permanent = True
            session['is_teacher'] = True
            return redirect(url_for('teacher_dashboard'))
        else:
            error = "Invalid Teacher ID or Password!"
            
    return render_template('teacherpanel.html', error=error)

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
            tag = request.form.get('tag')
            
            photo_file = request.files.get('photo')
            pdf_file = request.files.get('pdf')
            
            photo_filename = ""
            pdf_filename = ""
            
            if photo_file and photo_file.filename:
                photo_filename = secure_filename(photo_file.filename)
                photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                
            if pdf_file and pdf_file.filename:
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_file.save(os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename))
                
            cursor.execute("INSERT INTO courses (title, description, photo_filename, pdf_filename, batch_tag) VALUES (?, ?, ?, ?, ?)", 
                           (title, desc, photo_filename, pdf_filename, tag))
            conn.commit()
            
        elif action == 'add_announcement':
            msg = request.form.get('message')
            target_class = request.form.get('target_class', 'All Classes')
            cursor.execute("INSERT INTO announcements (message, target_class) VALUES (?, ?)", (msg, target_class))
            conn.commit()

        elif action == 'delete_announcement':
            ann_id = request.form.get('ann_id')
            cursor.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))
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

@app.route('/info')
def info_page():
    return render_template('info.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
