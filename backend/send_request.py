# backend/send_request.py
from twilio.rest import Client

account_sid = "ACe74c319d295d672ea021bd93974e9773"
auth_token = "dc5fdb0f8cbce7ee447465eabfd8244e"
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
    from_="whatsapp:+14155238886",
    to="whatsapp:+917207190981"
)
print("✅ Donation request sent!")