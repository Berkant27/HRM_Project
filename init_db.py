import sqlite3
import hashlib
import os

DB_FILE = 'hrm.db'  # Veritabanı kök dizine yazılacak

# Eğer dosya zaten varsa, tekrar oluşturma
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Kullanıcılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Departmanlar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # Roller
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # Çalışanlar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department_id INTEGER,
            role_id INTEGER,
            email TEXT,
            phone TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    ''')

    # İzinler
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    # Performans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date TEXT,
            note TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    # Admin kullanıcı ekle
    username = 'admin'
    password = 'admin123'
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, 'admin'))

    conn.commit()
    conn.close()
    print("✅ Veritabanı başarıyla oluşturuldu.")
else:
    print("ℹ️ Veritabanı zaten mevcut, yeniden oluşturulmadı.")
