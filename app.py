from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import joblib
import sqlite3
import random
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

model = joblib.load('model.pkl')

# CREATE DATABASE TABLE

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

# Create table when app starts
create_table()

# AUTO ANALYSIS FUNCTION


def analyze_database():
    conn = sqlite3.connect('threat_logs.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, login_hour, files_accessed, usb_used FROM threats")
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

# RUN AUTO SCHEDULER

scheduler = BackgroundScheduler()
scheduler.add_job(analyze_database, 'interval', seconds=10)
scheduler.start()

# HOME

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

# DASHBOARD

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if request.method == 'POST':

        employee_name = request.form['employee_name']
        login_hour = int(request.form['login_hour'])
        files_accessed = int(request.form['files_accessed'])
        usb_used = int(request.form['usb_used'])

        conn = sqlite3.connect('threat_logs.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO threats
            (employee_name, login_hour, files_accessed, usb_used, result, risk_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (employee_name, login_hour, files_accessed, usb_used, "PENDING", 0))

        conn.commit()
        conn.close()

        return redirect(url_for('history'))

    return render_template('dashboard.html')


# HISTORY PAGE
@app.route('/history', methods=['GET', 'POST'])
def history():

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

    return render_template('history.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)