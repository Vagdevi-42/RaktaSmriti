# backend/app/routes/coordinator.py
from fastapi import APIRouter, HTTPException
import boto3
from datetime import datetime, timedelta
import json
from ..config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER

router = APIRouter(prefix="/api/coordinator", tags=["coordinator"])

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

# Twilio credentials for WhatsApp


# Initialize Twilio client (only if needed)
try:
    from twilio.rest import Client
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    TWILIO_AVAILABLE = True
except:
    TWILIO_AVAILABLE = False
    print("Twilio not available")

# Initialize Bedrock client
try:
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )
    BEDROCK_AVAILABLE = True
except:
    BEDROCK_AVAILABLE = False
    print("Bedrock not available")

def format_phone_number(phone):
    """Ensure phone number has + prefix for Twilio"""
    phone = str(phone).strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

def get_value(item, key):
    """Extract value from DynamoDB item"""
    if key in item:
        val = item[key]
        if isinstance(val, dict):
            return val.get('S', val.get('N', str(val)))
        return str(val)
    return None

def generate_thank_you_message(donor_name, donation_count, hospital_name):
    """Generate personalized thank you message using AWS Bedrock Claude"""
    if not BEDROCK_AVAILABLE:
        # Fallback message
        return f"Thank you {donor_name}! Your {donation_count}th donation saved lives at {hospital_name}. You're a hero! 🩸"
    
    try:
        prompt = f"""You are a compassionate blood bank coordinator. Write a warm, personalized thank you message to a blood donor.

Donor Name: {donor_name}
Total Donations: {donation_count}
Hospital: {hospital_name}

The message should:
1. Be heartfelt and appreciative
2. Mention that they saved lives
3. Be conversational and warm
4. Be 2-3 sentences only
5. Include emojis

Write the message directly (no quotes, no labels):"""

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        message = response_body['content'][0]['text']
        return message
        
    except Exception as e:
        print(f"Bedrock error: {e}")
        # Fallback message
        return f"Thank you {donor_name}! Your {donation_count}th donation saved lives at {hospital_name}. You're a hero! 🩸"

def send_whatsapp_message(to_number, message):
    """Send WhatsApp message to donor"""
    if not TWILIO_AVAILABLE:
        print(f"WhatsApp not sent to {to_number}: {message}")
        return False
    
    try:
        twilio_client.messages.create(
            body=message,   
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}"
        )
        return True
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        return False

@router.get("/statistics")
async def get_statistics():
    """Get overall statistics for dashboard"""
    try:
        response = table.scan(Limit=500)
        all_items = response.get('Items', [])
        
        bridge_count = 0
        emergency_count = 0
        ghost_count = 0
        patient_count = 0
        
        for item in all_items:
            role = get_value(item, 'role')
            
            if role:
                if 'Bridge' in role:
                    bridge_count += 1
                elif 'Emergency' in role:
                    emergency_count += 1
                elif 'Ghost' in role:
                    ghost_count += 1
                elif 'Patient' in role:
                    patient_count += 1
        
        return {
            "success": True,
            "total_scanned": len(all_items),
            "bridge_donors": bridge_count,
            "emergency_donors": emergency_count,
            "ghost_donors": ghost_count,
            "patients": patient_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/donor/checkin")
async def mark_donor_checkin(donor_id: str, showed_up: bool):
    """Coordinator marks if donor showed up for donation"""
    try:
        response = table.get_item(Key={'user_id': donor_id})
        donor = response.get('Item', {})
        
        current_donations = int(get_value(donor, 'donations_till_date') or 0)
        current_score = int(get_value(donor, 'reliability_score') or 70)
        donor_name = get_value(donor, 'name') or 'Dear Donor'
        donor_phone = get_value(donor, 'phone_number')
        
        if showed_up:
            new_score = min(current_score + 5, 100)
            new_donations = current_donations + 1
            
            # Update donor in database (keeping your existing logic)
            table.update_item(
                Key={'user_id': donor_id},
                UpdateExpression="SET reliability_score = :score, donations_till_date = :donations, last_checkin = :time, last_donation_date = :donation_date, next_eligible_date = :next_eligible, eligibility_status = :status",
                ExpressionAttributeValues={
                    ":score": new_score,
                    ":donations": new_donations,
                    ":time": datetime.now().isoformat(),
                    ":donation_date": datetime.now().isoformat(),
                    ":next_eligible": (datetime.now() + timedelta(days=90)).isoformat(),
                    ":status": "not eligible"
                }
            )
            
            # Generate personalized thank you message using Bedrock
            hospital_name = "City Blood Bank"
            thank_you_message = generate_thank_you_message(donor_name, new_donations, hospital_name)
            
            # Send WhatsApp message to donor
            whatsapp_sent = False
            if donor_phone:
                whatsapp_message = f"🩸 *Thank You for Saving Lives!*\n\n{thank_you_message}\n\n📍 {hospital_name}\n📅 {datetime.now().strftime('%B %d, %Y')}\n\n*You are eligible to donate again after 90 days.*\n\nWith gratitude,\nRaktaSmriti Team"
                whatsapp_sent = send_whatsapp_message(donor_phone, whatsapp_message)
            
        else:
            new_score = max(current_score - 15, 0)
            
            table.update_item(
                Key={'user_id': donor_id},
                UpdateExpression="SET reliability_score = :score, last_missed = :time",
                ExpressionAttributeValues={
                    ":score": new_score,
                    ":time": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "donor_id": donor_id,
            "showed_up": showed_up,
            "new_reliability_score": new_score,
            "thank_you_sent": whatsapp_sent if showed_up else None,
            "bedrock_message": thank_you_message if showed_up else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))