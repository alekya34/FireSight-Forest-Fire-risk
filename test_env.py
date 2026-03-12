from dotenv import load_dotenv
import os

load_dotenv()

print("ALERT_EMAIL:", repr(os.getenv('ALERT_EMAIL')))
print("EMAIL_PASSWORD:", repr(os.getenv('EMAIL_PASSWORD')))
