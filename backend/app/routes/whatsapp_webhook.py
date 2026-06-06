# backend/app/routes/whatsapp_webhook.py
from fastapi import APIRouter, Request
from twilio.rest import Client

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

TWILIO_ACCOUNT_SID = "ACe74c319d295d672ea021bd93974e9773"
TWILIO_AUTH_TOKEN = "dc5fdb0f8cbce7ee447465eabfd8244e"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Hospital data
HOSPITAL = {
    "name": "City Blood Bank",
    "address": "123 Main Road, Near Railway Station, City - 500001",
    "latitude": 17.3922792,
    "longitude": 78.4602749,
    "phone": "+911234567890"
}

def send_whatsapp(to_number, message):
    client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to_number}"
    )

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        form = await request.form()
        reply = form.get('Body', '').upper().strip()
        from_number = form.get('From', '').replace('whatsapp:', '')
        
        print(f"📱 Donor replied: '{reply}'")
        
        if reply == 'YES':
            # Message 1: Donor confirmation with FULL details
            donor_msg = f"""✅ *DONATION CONFIRMED!*

Thank you for saving a life!

📍 *Hospital:* {HOSPITAL['name']}
📌 *Address:* {HOSPITAL['address']}
⏰ *Time:* Tomorrow, 10:00 AM

🗺️ *Google Maps:* 
https://maps.google.com/?q={HOSPITAL['latitude']},{HOSPITAL['longitude']}

📞 *Contact:* {HOSPITAL['phone']}

Please bring ID proof. Reach 30 minutes early.

*You are a hero!* 🩸"""
            
            send_whatsapp(from_number, donor_msg)
            
            # Message 2: Patient confirmation
            patient_msg = f"""🩸 *DONOR CONFIRMED!*

A donor is coming to help you!

📍 *Hospital:* {HOSPITAL['name']}
📌 *Address:* {HOSPITAL['address']}
⏰ *Time:* Tomorrow, 10:00 AM

Please reach on time with your documents.

*Stay strong!* 💪"""
            
            send_whatsapp(from_number, patient_msg)
            
        elif reply == 'NO':
            send_whatsapp(from_number, "❌ Thank you for letting us know. We'll find another donor.")
        else:
            send_whatsapp(from_number, "🩸 Reply YES to confirm donation, or NO to decline.")
        
        return {"success": True}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}