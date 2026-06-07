# backend/send_request.py
import os
from pathlib import Path

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
to_number = os.getenv("PATIENT_WHATSAPP_NUMBER", "+917207190981")

if not account_sid or not auth_token or not from_number:
    raise RuntimeError("Twilio credentials are not set in backend/.env. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER first.")

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="""🩸 *URGENT: Blood Donation Request*

Patient needs O+ blood at:
🏥 City Hospital
⏰ Tomorrow, 10:00 AM

Reply:
✅ YES - I can donate
❌ NO - I cannot donate

*You can save a life!*""",
    from_=from_number,
    to=f"whatsapp:{to_number.lstrip('whatsapp:')}" if not str(to_number).startswith("whatsapp:") else to_number
)
print("✅ Donation request sent!")
print(f"SID: {message.sid}")