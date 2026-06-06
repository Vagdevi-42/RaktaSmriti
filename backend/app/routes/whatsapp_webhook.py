# backend/app/routes/whatsapp_webhook.py
from fastapi import APIRouter, Request, HTTPException
from twilio.rest import Client
from ..config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, PATIENT_WHATSAPP_NUMBER
from .ghost_donor import register_ghost_donor_from_message

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Hospital data
HOSPITAL = {
    "name": "City Blood Bank",
    "address": "123 Main Road, Near Railway Station, City - 500001",
    "latitude": 17.3922792,
    "longitude": 78.4602749,
    "phone": "+911234567890"
}

def normalize_whatsapp_number(number: str) -> str:
    """Normalize incoming Twilio WhatsApp numbers to a safe format."""
    if not number:
        return ""
    cleaned = str(number).strip().replace("whatsapp:", "")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned


def send_whatsapp(to_number, message):
    """Send WhatsApp message and return a clear success/error result."""
    try:
        formatted_to = normalize_whatsapp_number(to_number)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{formatted_to}"
        )
        print(f"✅ Message sent! SID: {msg.sid}")
        return True, msg.sid
    except Exception as e:
        print(f"❌ Twilio send error: {e}")
        return False, str(e)

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        form = await request.form()
        body = (form.get('Body') or '').strip()
        reply = body.upper().strip()
        from_number = normalize_whatsapp_number(form.get('From'))
        
        print(f"📱 Incoming WhatsApp message: '{body}' from {from_number}")

        # Registration messages from the QR flow should create/update ghost donor records.
        if 'register' in body.lower() or 'blood donor' in body.lower():
            result = register_ghost_donor_from_message(from_number, body)
            if result.get('success'):
                send_whatsapp(from_number, "🩸 Your ghost donor registration was received successfully. The coordinator dashboard will update shortly.")
            return {"success": result.get('success', False), "message": result.get('message'), "donor_id": result.get('donor_id')}

        if reply == 'YES':
            # Message 1: Donor confirmation
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
            
            result1, sid1 = send_whatsapp(from_number, donor_msg)
            
            # Message 2: Patient confirmation
            patient_msg = f"""🩸 *DONOR CONFIRMED!*

A donor is coming to help you!

📍 *Hospital:* {HOSPITAL['name']}
📌 *Address:* {HOSPITAL['address']}
⏰ *Time:* Tomorrow, 10:00 AM

Please reach on time with your documents.

*Stay strong!* 💪"""
            
            patient_number = (
                normalize_whatsapp_number(PATIENT_WHATSAPP_NUMBER)
                or normalize_whatsapp_number(HOSPITAL['phone'])
                or from_number
            )
            result2, sid2 = send_whatsapp(patient_number, patient_msg)

            if not result1 or not result2:
                return {
                    "success": False,
                    "donor_message_sent": result1,
                    "patient_message_sent": result2,
                    "donor_sid": sid1,
                    "patient_sid": sid2,
                }

            return {
                "success": True,
                "donor_message_sent": True,
                "patient_message_sent": True,
                "donor_sid": sid1,
                "patient_sid": sid2,
            }
            
        elif reply == 'NO':
            send_whatsapp(from_number, "❌ Thank you for letting us know. We'll find another donor.")
            return {"success": True}
        else:
            send_whatsapp(from_number, "🩸 Reply YES to confirm donation, or NO to decline.")
            return {"success": True}
        
    except Exception as e:
        print(f"Error in webhook: {e}")
        return {"success": False, "error": str(e)}

@router.get("/webhook-status")
async def whatsapp_webhook_status():
    """Simple health/status route for the WhatsApp webhook."""
    return {"message": "Webhook is active. Send POST requests with WhatsApp replies."}