import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # Load .env file

from_email = os.getenv("GMAIL_USER")
password = os.getenv("GMAIL_PASSWORD")
to_email = "chetraso721@gmail.com"

msg = MIMEText("This is a test email from my Python script.")
msg["Subject"] = "Test Email"
msg["From"] = from_email
msg["To"] = to_email

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()
    print("✅ Test Email Sent Successfully!")
except Exception as e:
    print(f"❌ Test Email Failed: {e}")
