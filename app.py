from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import joblib
import sqlite3
import random
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "socproject123"

# Load AI Model
model = joblib.load('model.pkl')


# ---------------------------
# CREATE DATABASE TABLE
# ---------------------------
def create_table():
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
    conn.close()

create_table()


# ---------------------------
# AUTO ANALYSIS FUNCTION
# ---------------------------
def analyze_database():

    conn = sqlite3.connect('threat_logs.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, login_hour, files_accessed, usb_used FROM threats"
    )

    rows = cursor.fetchall()

    for row in rows:

        threat_id, login_hour, files_accessed, usb_used = row

        sample = pd.DataFrame({
            'login_hour': [login_hour],
            'files_accessed': [files_accessed],
            'usb_used': [usb_used]
        })

        prediction = model.predict(sample)

        if prediction[0] == -1:
            result = "⚠ SUSPICIOUS"
            risk_score = random.randint(75, 99)
        else:
            result = "NORMAL"
            risk_score = random.randint(10, 40)

        cursor.execute("""
        UPDATE threats
        SET result=?, risk_score=?
        WHERE id=?
        """, (result, risk_score, threat_id))

    conn.commit()
    conn.close()


# ---------------------------
# SCHEDULER
# ---------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(analyze_database, 'interval', seconds=10)
scheduler.start()


# ---------------------------
# LOGIN PAGE
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":

            session['user'] = username

            return redirect(url_for('dashboard'))

        else:

            return render_template(
                'login.html',
                error="Invalid Username or Password"
            )

    return render_template('login.html')


# ---------------------------
# HOME
# ---------------------------
@app.route('/')
def home():
    return redirect(url_for('login'))


# ---------------------------
# DASHBOARD
# ---------------------------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        employee_name = request.form['employee_name']
        login_hour = int(request.form['login_hour'])
        files_accessed = int(request.form['files_accessed'])
        usb_used = int(request.form['usb_used'])

        conn = sqlite3.connect('threat_logs.db')
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO threats
        (
            employee_name,
            login_hour,
            files_accessed,
            usb_used,
            result,
            risk_score
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            employee_name,
            login_hour,
            files_accessed,
            usb_used,
            "PENDING",
            0
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('history'))

    conn = sqlite3.connect('threat_logs.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM threats")
    total_records = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM threats WHERE result='⚠ SUSPICIOUS'"
    )
    suspicious_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM threats WHERE result='NORMAL'"
    )
    normal_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',
        total_records=total_records,
        suspicious_count=suspicious_count,
        normal_count=normal_count
    )


# ---------------------------
# HISTORY PAGE
# ---------------------------
@app.route('/history', methods=['GET', 'POST'])
def history():

    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.form.get('search')

    conn = sqlite3.connect('threat_logs.db')
    cursor = conn.cursor()

    if search:

        cursor.execute(
            "SELECT * FROM threats WHERE employee_name LIKE ?",
            ('%' + search + '%',)
        )

    else:

        cursor.execute("SELECT * FROM threats")

    data = cursor.fetchall()

    conn.close()
    conn = sqlite3.connect('threat_logs.db')
    cursor = conn.cursor()

# Total records
    cursor.execute("SELECT COUNT(*) FROM threats")
    total_records = cursor.fetchone()[0]

# Suspicious records
    cursor.execute("SELECT COUNT(*) FROM threats WHERE result='⚠ SUSPICIOUS'")
    suspicious_count = cursor.fetchone()[0]
    if suspicious_count > 0:
        alert_message = f"🚨 ALERT: {suspicious_count} Suspicious Threat(s) Detected"
    else:
        alert_message = "✅ No Active Threats"

# Normal records
    cursor.execute("SELECT COUNT(*) FROM threats WHERE result='NORMAL'")
    normal_count = cursor.fetchone()[0]

    conn.close()
    return render_template(
    'dashboard.html',
    total_records=total_records,
    suspicious_count=suspicious_count,
    normal_count=normal_count,
    alert_message=alert_message
    )

# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# ---------------------------
# RUN APP
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)