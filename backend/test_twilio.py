# backend/test_twilio.py
from twilio.rest import Client

# YOUR CORRECT CREDENTIALS
ACCOUNT_SID = "ACe74c319d295d672ea021bd93974e9773"
AUTH_TOKEN = "9f43abc6aa023271c3165e9a20639c1e"

print("Testing Twilio with CORRECT credentials...")

try:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    print("✅ Twilio client created")
    
    message = client.messages.create(
        body="🩸 RaktaSmriti Test: Your blood donation system is working! Reply YES to test.",
        from_="whatsapp:+14155238886",
        to="whatsapp:+917207190981"
    )
    print("✅ WhatsApp message sent!")
    print(f"Message SID: {message.sid}")
    print("Check your phone now!")
    
except Exception as e:
    print(f"❌ Error: {e}")