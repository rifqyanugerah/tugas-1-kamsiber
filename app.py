from flask import Flask, render_template, request, redirect, url_for, session, flash  # Ditambahkan 'session' dan 'flash'
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3
from functools import wraps  # Ditambahkan untuk decorator login_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key_for_session_management'  # Ditambahkan untuk session management
db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'


# Decorator untuk proteksi login
def login_required(f): # Ditambahkan untuk melindungi akses CRUD
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Silakan login terlebih dahulu.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST']) # Ditambahkan untuk autentikasi login
def login(): 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifikasi login
        if username == 'admin00' and password == 'kamsiber00':
            session['logged_in'] = True
            flash('Login berhasil!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout') # Ditambahkan untuk logout
def logout():
    session.pop('logged_in', None)
    flash('Logout berhasil!', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required # Ditambahkan untuk membatasi akses ke rute ini
def index():
    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

@app.route('/add', methods=['POST'])
@login_required # Ditambahkan untuk membatasi akses ke rute ini
def add_student():
    name = request.form['name']
    age = request.form['age']
    grade = request.form['grade']

    connection = sqlite3.connect('instance/students.db')
    cursor = connection.cursor()

    query = f"INSERT INTO student (name, age, grade) VALUES ('{name}', {age}, '{grade}')"
    cursor.execute(query)
    connection.commit()
    connection.close()
    return redirect(url_for('index'))


@app.route('/delete/<string:id>')
@login_required # Ditambahkan untuk membatasi akses ke rute ini
def delete_student(id):
    # RAW Query
    db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required # Ditambahkan untuk membatasi akses ke rute ini
def edit_student(id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']

        if not age.isdigit(): # Ditambahkan untuk validasi input
            flash('Usia harus berupa angka!', 'danger')
            return redirect(url_for('edit_student', id=id))

        age = int(age)  # Mengkonversi ke integer setelah validasi

        
        db.session.execute(
            text("UPDATE student SET name=:name, age=:age, grade=:grade WHERE id=:id"),
            {'name': name, 'age': age, 'grade': grade, 'id': id}
        ) # Dimodifikasi dengan menggunakan parameter binding untuk mencegah SQL Injection
        db.session.commit()
        return redirect(url_for('index'))
    else:
        student = db.session.execute(text(f"SELECT * FROM student WHERE id={id}")).fetchone()
        return render_template('edit.html', student=student)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
