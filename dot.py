import email
import smtplib
from datetime import datetime
import os
import schedule
import time

import requests

def create_session_info(center, session):
    return {"name": center["name"],
            "date": session["date"],
            "capacity": session["available_capacity"],
            "age_limit": session["min_age_limit"]}

def get_sessions(data):
    for center in data["centers"]:
        for session in center["sessions"]:
            yield create_session_info(center, session)

def is_available(session):
    return session["capacity"] > 0

def is_eighteen_plus(session):
    return session["age_limit"] == 18

def get_for_seven_days(start_date):
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict"
    params = {"district_id": 571, "date": start_date.strftime("%d-%m-%Y")}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"}
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()
    return [session for session in get_sessions(data) if is_eighteen_plus(session) and is_available(session)]

def create_output(session_info):
    return f"{session_info['date']} - {session_info['name']} ({session_info['capacity']})"

def start():
    print(get_for_seven_days(datetime.today()))
    content = "\n".join([create_output(session_info) for session_info in get_for_seven_days(datetime.today())])
    username = os.environ.get('usr')
    password = os.environ.get('pass')
    # Try a loop to get emails from table and send the notifications back
    to = os.environ.get('to')

    if not content:
        print("No availability")
    else:
        email_msg = email.message.EmailMessage()
        email_msg['Subject'] = "Vaccination Slot Open"
        email_msg['From'] = username
        email_msg['To'] = to
        email_msg.set_content(content)

        with smtplib.SMTP(host='smtp.gmail.com', port='587') as server:
            server.starttls()
            server.login(username, password)
            server.send_message(email_msg)
            server.quit()

if __name__ == "__main__":
    schedule.every(30).seconds.do(start)

    while True:
        # Checks whether a scheduled task
        # is pending to run or not
        schedule.run_pending()
        time.sleep(1)