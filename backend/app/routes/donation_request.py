# backend/app/routes/donation_request.py
from fastapi import APIRouter
from twilio.rest import Client

router = APIRouter(prefix="/api/donation", tags=["donation"])

TWILIO_ACCOUNT_SID = "ACe74c319d295d672ea021bd93974e9773"
TWILIO_AUTH_TOKEN = "dc5fdb0f8cbce7ee447465eabfd8244e"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@router.post("/send")
async def send_donation_request():
    """Send donation request to your WhatsApp"""
    try:
        message = client.messages.create(
            body="""🩸 *URGENT: Blood Donation Request*

A patient needs O+ blood at:
🏥 City Blood Bank
📍 123 Main Road, City
⏰ Tomorrow, 10:00 AM

Reply:
✅ *YES* - I can donate
❌ *NO* - I cannot donate

*You can save a life!* 🩸""",
            from_=TWILIO_WHATSAPP_NUMBER,
            to="whatsapp:+917207190981"
        )
        
        return {
            "success": True,
            "message": "Donation request sent to your WhatsApp!",
            "sid": message.sid
        }
    except Exception as e:
        return {"success": False, "error": str(e)}