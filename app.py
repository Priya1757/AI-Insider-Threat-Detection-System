from flask import Flask, render_template, request
import pandas as pd
import joblib
import random
import sqlite3
app = Flask(__name__)

model = joblib.load('model.pkl')

@app.route('/', methods=['GET', 'POST'])

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
            # Store data in database

        conn = sqlite3.connect('threat_logs.db')

        cursor = conn.cursor()

        cursor.execute('''
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
        ''',

        (
            employee_name,
            login_hour,
            files_accessed,
            usb_used,
            result,
            risk_score
        ))

        conn.commit()

        conn.close()

    return render_template(
        'dashboard.html',
        result=result,
        risk_score=risk_score,
        css_class=css_class
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)