from fastapi import APIRouter, Request
from twilio.rest import Client

from ..config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def get_hospital():
    """Return the default hospital details used for donor confirmations."""
    return {
        "name": "City Blood Bank",
        "address": "123 Main Road, Near Railway Station, City - 500001",
        "latitude": 17.3922792,
        "longitude": 78.4602749,
        "phone": "+911234567890",
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
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{normalize_whatsapp_number(to_number)}"
        )
        return True, msg.sid
    except Exception as e:
        return False, str(e)

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Handle donor's YES/NO reply"""
    try:
        form = await request.form()
        reply = (form.get('Body') or '').upper().strip()
        from_number = normalize_whatsapp_number(form.get('From'))
        
        print(f"📱 Donor replied: '{reply}'")
        
        if reply == 'YES':
            hospital = get_hospital()
            
            # Message 1: Donor confirmation with location
            donor_msg = f"""✅ *DONATION CONFIRMED!*

Thank you for saving a life!

📍 *Hospital:* {hospital['name']}
📌 *Address:* {hospital['address']}
⏰ *Time:* Tomorrow, 10:00 AM

🗺️ *Location:* 
https://maps.google.com/?q={hospital['latitude']},{hospital['longitude']}

📞 *Contact:* {hospital['phone']}

Please bring ID proof. Reach 30 minutes early.

*You are a hero!* 🩸"""
            
            result1, sid1 = send_whatsapp(from_number, donor_msg)
            
            # Message 2: Patient confirmation (same number for demo)
            patient_msg = f"""🩸 *DONOR CONFIRMED!*

A donor is coming to help you!

📍 *Hospital:* {hospital['name']}
📌 *Address:* {hospital['address']}
⏰ *Time:* Tomorrow, 10:00 AM

Please reach on time with your documents.

*Stay strong!* 💪"""
            
            patient_number = normalize_whatsapp_number(hospital['phone']) or from_number
            result2, sid2 = send_whatsapp(patient_number, patient_msg)

            if not result1 or not result2:
                return {"success": False, "donor_message_sent": result1, "patient_message_sent": result2, "donor_sid": sid1, "patient_sid": sid2}

            return {"success": True, "donor_message_sent": True, "patient_message_sent": True, "donor_sid": sid1, "patient_sid": sid2}
            
        elif reply == 'NO':
            send_whatsapp(from_number, "❌ Thank you for letting us know. We'll find another donor.")
        else:
            send_whatsapp(from_number, "🩸 Reply YES to confirm donation, or NO to decline.")
        
        return {"success": True}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}