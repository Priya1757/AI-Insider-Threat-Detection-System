import sqlite3

conn = sqlite3.connect('threat_logs.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT,
    login_hour INTEGER,
    files_accessed INTEGER,
    usb_used INTEGER,
    result TEXT,
    risk_score INTEGER
)
''')

conn.commit()

print("Database created successfully")