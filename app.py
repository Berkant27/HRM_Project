from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
import sqlite3
import hashlib
from functools import wraps
from datetime import datetime
import plotly.graph_objs as go
import plotly
import json
import os

# Flask uygulaması oluşturuluyor
app = Flask(__name__)
app.secret_key = 'hrm_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

DATABASE = 'hrm.db'

#-----------------------------------------------------YARDIMCI FONKSİYONLAR---------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Giriş yapmanız gerekiyor', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Bu işlemi gerçekleştirmek için yetkiniz yok', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        user = conn.execute('SELECT id, role FROM users WHERE username=? AND password=?',
                            (username, hashed_password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Hatalı kullanıcı adı veya şifre!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#--------------------------------------------- DEPARTMANLAR ------------------------------------------------

@app.route('/departments')
@login_required
def departments():
    conn = get_db_connection()
    departments = conn.execute('SELECT * FROM departments').fetchall()
    conn.close()
    return render_template('departments.html', departments=departments)

@app.route('/departments/add', methods=['GET', 'POST'])
@admin_required
def add_department():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()
        conn.execute('INSERT INTO departments (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        return redirect(url_for('departments'))
    return render_template('add_department.html')

@app.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_department(id):
    conn = get_db_connection()
    department = conn.execute('SELECT * FROM departments WHERE id=?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        conn.execute('UPDATE departments SET name=? WHERE id=?', (name, id))
        conn.commit()
        conn.close()
        return redirect(url_for('departments'))

    conn.close()
    return render_template('edit_department.html', department=department)

#--------------------------------------------- ROLLER ------------------------------------------------

@app.route('/roles')
@login_required
def roles():
    conn = get_db_connection()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    return render_template('roles.html', roles=roles)

@app.route('/roles/add', methods=['GET', 'POST'])
@admin_required
def add_role():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()
        conn.execute('INSERT INTO roles (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        return redirect(url_for('roles'))
    return render_template('add_role.html')

@app.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_role(id):
    conn = get_db_connection()
    role = conn.execute('SELECT * FROM roles WHERE id=?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        conn.execute('UPDATE roles SET name=? WHERE id=?', (name, id))
        conn.commit()
        conn.close()
        return redirect(url_for('roles'))

    conn.close()
    return render_template('edit_role.html', role=role)

#--------------------------------------------- ÇALIŞANLAR ------------------------------------------------

@app.route('/employees')
@login_required
def employees():
    conn = get_db_connection()
    employees = conn.execute('''
        SELECT employees.*, departments.name AS department_name, roles.name AS role_name
        FROM employees
        LEFT JOIN departments ON employees.department_id = departments.id
        LEFT JOIN roles ON employees.role_id = roles.id
    ''').fetchall()
    conn.close()
    return render_template('employees.html', employees=employees)

@app.route('/employees/add', methods=['GET', 'POST'])
@admin_required
def add_employee():
    conn = get_db_connection()
    departments = conn.execute('SELECT * FROM departments').fetchall()
    roles = conn.execute('SELECT * FROM roles').fetchall()

    if request.method == 'POST':
        name = request.form['name']
        department_id = request.form['department']
        role_id = request.form['role']
        email = request.form['email']
        phone = request.form['phone']

        conn.execute('''
            INSERT INTO employees (name, department_id, role_id, email, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, department_id, role_id, email, phone))
        conn.commit()
        conn.close()
        return redirect(url_for('employees'))

    conn.close()
    return render_template('add_employee.html', departments=departments, roles=roles)

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_employee(id):
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id=?', (id,)).fetchone()
    departments = conn.execute('SELECT * FROM departments').fetchall()
    roles = conn.execute('SELECT * FROM roles').fetchall()

    if request.method == 'POST':
        name = request.form['name']
        department_id = request.form['department']
        role_id = request.form['role']
        email = request.form['email']
        phone = request.form['phone']

        conn.execute('''
            UPDATE employees
            SET name=?, department_id=?, role_id=?, email=?, phone=?
            WHERE id=?
        ''', (name, department_id, role_id, email, phone, id))
        conn.commit()
        conn.close()
        return redirect(url_for('employees'))

    conn.close()
    return render_template('edit_employee.html', employee=employee, departments=departments, roles=roles)

@app.route('/employees/delete/<int:id>')
@admin_required
def delete_employee(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM employees WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('employees'))

#--------------------------------------------- İZİNLER ------------------------------------------------

@app.route('/leaves')
@login_required
def leaves():
    conn = get_db_connection()
    leaves = conn.execute('''
        SELECT leaves.*, employees.name AS employee_name
        FROM leaves
        LEFT JOIN employees ON leaves.employee_id = employees.id
    ''').fetchall()
    conn.close()
    return render_template('leaves.html', leaves=leaves)

@app.route('/leaves/add', methods=['GET', 'POST'])
@admin_required
def add_leave():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()

    if request.method == 'POST':
        employee_id = request.form['employee']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']

        conn.execute('''
            INSERT INTO leaves (employee_id, start_date, end_date, reason)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, start_date, end_date, reason))
        conn.commit()
        conn.close()
        return redirect(url_for('leaves'))

    conn.close()
    return render_template('add_leave.html', employees=employees)

@app.route('/leaves/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_leave(id):
    conn = get_db_connection()
    leave = conn.execute('SELECT * FROM leaves WHERE id=?', (id,)).fetchone()
    employees = conn.execute('SELECT * FROM employees').fetchall()

    if request.method == 'POST':
        employee_id = request.form['employee']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        status = request.form['status']

        conn.execute('''
            UPDATE leaves
            SET employee_id=?, start_date=?, end_date=?, reason=?, status=?
            WHERE id=?
        ''', (employee_id, start_date, end_date, reason, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('leaves'))

    conn.close()
    return render_template('edit_leave.html', leave=leave, employees=employees)

#--------------------------------------------- PERFORMANS ------------------------------------------------

@app.route('/performance')
@login_required
def performance():
    conn = get_db_connection()
    records = conn.execute('''
        SELECT performance.*, employees.name AS employee_name
        FROM performance
        LEFT JOIN employees ON performance.employee_id = employees.id
    ''').fetchall()
    conn.close()
    return render_template('performance.html', records=records)

@app.route('/performance/add', methods=['GET', 'POST'])
@admin_required
def add_performance():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()

    if request.method == 'POST':
        employee_id = request.form['employee']
        date = request.form['date']
        note = request.form['note']

        conn.execute('''
            INSERT INTO performance (employee_id, date, note)
            VALUES (?, ?, ?)
        ''', (employee_id, date, note))
        conn.commit()
        conn.close()
        return redirect(url_for('performance'))

    conn.close()
    return render_template('add_performance.html', employees=employees)

@app.route('/performance/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_performance(id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM performance WHERE id=?', (id,)).fetchone()
    employees = conn.execute('SELECT * FROM employees').fetchall()

    if request.method == 'POST':
        employee_id = request.form['employee']
        date = request.form['date']
        note = request.form['note']

        conn.execute('''
            UPDATE performance
            SET employee_id=?, date=?, note=?
            WHERE id=?
        ''', (employee_id, date, note, id))
        conn.commit()
        conn.close()
        return redirect(url_for('performance'))

    conn.close()
    return render_template('edit_performance.html', performance=record, employees=employees)

#--------------------------------------------- ANALİTİK ------------------------------------------------

@app.route('/analytics')
@admin_required
def analytics():
    conn = get_db_connection()
    data = conn.execute('''
        SELECT employees.name, AVG(LENGTH(note)) as avg_score
        FROM performance
        LEFT JOIN employees ON performance.employee_id = employees.id
        GROUP BY employee_id
    ''').fetchall()
    conn.close()

    bar = go.Bar(
        x=[row['name'] for row in data],
        y=[row['avg_score'] for row in data]
    )
    graph_data = json.dumps([bar], cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('analytics.html', graph_data=graph_data)

#--------------------------------------------- SUNUCU ------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
