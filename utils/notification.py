import smtplib
from email.message import EmailMessage
import datetime

# -------------------------
# ⛔ Alert Triggers
# -------------------------

def detect_alerts(row, office_start="09:00:00", office_end="17:00:00"):
    alerts = []

    if not row["Check-in Time"]:
        alerts.append("❗ Missing Check-in")
    if not row["Check-out Time"]:
        alerts.append("❗ Missing Check-out")

    try:
        in_time = datetime.datetime.strptime(row["Check-in Time"], "%H:%M:%S").time()
        if in_time > datetime.datetime.strptime(office_start, "%H:%M:%S").time():
            alerts.append("⏰ Late Arrival")
    except:
        pass

    try:
        out_time = datetime.datetime.strptime(row["Check-out Time"], "%H:%M:%S").time()
        if out_time < datetime.datetime.strptime(office_end, "%H:%M:%S").time():
            alerts.append("🏃 Early Exit")
    except:
        pass

    return ", ".join(alerts)


# -------------------------
# ✉️ Email Notification
# -------------------------

def send_email_alert(to_email, subject, body, smtp_server, smtp_port, sender_email, sender_password):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False
