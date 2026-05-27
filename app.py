from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import joblib
import sqlite3
import random

app = Flask(__name__)

# Load trained AI model
model = joblib.load('model.pkl')


# ---------------------------
# HOME
# ---------------------------
@app.route('/')
def home():
    return redirect(url_for('dashboard'))


# ---------------------------
# DASHBOARD
# ---------------------------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    result = ""
    risk_score = 0
    css_class = ""

    if request.method == 'POST':

        employee_name = request.form['employee_name']
        login_hour = int(request.form['login_hour'])
        files_accessed = int(request.form['files_accessed'])
        usb_used = int(request.form['usb_used'])

        sample_data = pd.DataFrame({
            'login_hour': [login_hour],
            'files_accessed': [files_accessed],
            'usb_used': [usb_used]
        })

        prediction = model.predict(sample_data)

        if prediction[0] == -1:
            result = f"⚠ HIGH RISK THREAT DETECTED for {employee_name}"
            risk_score = random.randint(75, 99)
            css_class = "high"
        else:
            result = f"✅ NORMAL ACTIVITY for {employee_name}"
            risk_score = random.randint(10, 40)
            css_class = "normal"

        conn = sqlite3.connect('threat_logs.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO threats 
            (employee_name, login_hour, files_accessed, usb_used, result, risk_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (employee_name, login_hour, files_accessed, usb_used, result, risk_score))

        conn.commit()
        conn.close()

    return render_template(
        'dashboard.html',
        result=result,
        risk_score=risk_score,
        css_class=css_class
    )


# ---------------------------
# GRAPH PAGE
# ---------------------------
@app.route('/graph')
def graph():
    conn = sqlite3.connect('threat_logs.db')
    df = pd.read_sql_query("SELECT risk_score FROM threats", conn)
    conn.close()

    return render_template('graph.html', data=df['risk_score'].tolist())


# ---------------------------
# HISTORY PAGE (FIXED)
# ---------------------------
@app.route('/history', methods=['GET', 'POST'])
def history():

    search = request.form.get('search') if request.method == 'POST' else None

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


# ---------------------------
# RUN APP
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)