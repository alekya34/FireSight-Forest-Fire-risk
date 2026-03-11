import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env
load_dotenv()

ALERT_EMAIL = os.getenv('ALERT_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))

def test_email():
    print("--- Email Configuration ---")
    print(f"Host: {EMAIL_HOST}")
    print(f"Port: {EMAIL_PORT}")
    print(f"User: {ALERT_EMAIL}")
    print(f"Pass: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'NOT SET'}")
    
    if not (ALERT_EMAIL and EMAIL_PASSWORD):
        print("ERROR: ALERT_EMAIL or EMAIL_PASSWORD is missing in .env")
        return

    to_email = ALERT_EMAIL # Send to self for testing
    msg = MIMEText("This is a test email from the Forest Fire Prediction App.")
    msg['Subject'] = "Forest Fire App - SMTP Test"
    msg['From'] = ALERT_EMAIL
    msg['To'] = to_email

    print(f"\nAttempting to connect to {EMAIL_HOST}:{EMAIL_PORT}...")
    try:
        # Try SSL first (Port 465)
        if EMAIL_PORT == 465:
            with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=10) as server:
                print("Connected! Attempting login...")
                server.login(ALERT_EMAIL, EMAIL_PASSWORD)
                print("Login successful! Sending mail...")
                server.sendmail(ALERT_EMAIL, [to_email], msg.as_string())
                print("✅ Email sent successfully!")
        # Try TLS (Port 587)
        else:
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10) as server:
                print("Connected! Starting TLS...")
                server.starttls()
                print("TLS started. Attempting login...")
                server.login(ALERT_EMAIL, EMAIL_PASSWORD)
                print("Login successful! Sending mail...")
                server.sendmail(ALERT_EMAIL, [to_email], msg.as_string())
                print("✅ Email sent successfully!")

    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication Failed!")
        print("Tip: If using Gmail, you likely need an 'App Password'.")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification")
        print("3. Search for 'App Passwords' and generate one.")
        print("4. Update EMAIL_PASSWORD in .env with that 16-character code.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_email()
