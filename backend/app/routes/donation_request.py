# backend/app/routes/donation_request.py
from fastapi import APIRouter
from twilio.rest import Client
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from ..config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
import os
import boto3

router = APIRouter(prefix="/api/donation", tags=["donation"])


def normalize_blood_group(blood_group: str) -> str:
    """Normalize standard blood-group labels used by donors and prediction results."""
    aliases = {
        "o+": "O Positive",
        "o positive": "O Positive",
        "o-": "O Negative",
        "o negative": "O Negative",
        "a+": "A Positive",
        "a positive": "A Positive",
        "a-": "A Negative",
        "a negative": "A Negative",
        "b+": "B Positive",
        "b positive": "B Positive",
        "b-": "B Negative",
        "b negative": "B Negative",
        "ab+": "AB Positive",
        "ab positive": "AB Positive",
        "ab-": "AB Negative",
        "ab negative": "AB Negative",
    }
    return aliases.get((blood_group or "").strip().lower(), (blood_group or "").strip())


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table('team81-user')

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two points"""
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        R = 6371
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    except:
        return 999

def calculate_reliability_score(donor):
    """Calculate donor reliability score (0-100)"""
    donations = int(donor.get('donations_till_date', 0) or 0)
    total_calls = int(donor.get('total_calls', 0) or 1)
    
    score = 0
    if donations >= 10:
        score += 40
    elif donations >= 5:
        score += 30
    elif donations >= 2:
        score += 20
    elif donations >= 1:
        score += 10
    
    if donations > 0:
        ratio = total_calls / donations
        if ratio <= 1:
            score += 30
        elif ratio <= 2:
            score += 25
        elif ratio <= 5:
            score += 15
    else:
        score += 10
    
    if donor.get('status') == 'active':
        score += 15
    if donor.get('eligibility_status') == 'eligible':
        score += 15
    
    return min(score, 100)

@router.post("/send")
async def send_donation_request():
    """Simple send to your number (for testing)"""
    try:
        print("📨 Sending donation request to Twilio...")
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
        
        print(f"✅ Twilio donation request accepted. SID: {message.sid}")
        return {
            "success": True,
            "message": "Donation request sent!",
            "sid": message.sid
        }
    except Exception as e:
        print(f"❌ Twilio donation request failed: {e}")
        return {"success": False, "error": str(e)}

@router.post("/send-to-nearby")
async def send_to_nearby_donors(
    blood_group: str = "O Positive",
    hospital_id: str = "HOSPITAL_CITY",
    max_distance_km: float = 5,
    donation_time: str = "Tomorrow, 10:00 AM"
):
    """
    Send donation request ONLY to donors within X km of hospital
    Follows cascade logic: Tier 1 first, then Tier 2, etc.
    """
    try:
        normalized_blood_group = normalize_blood_group(blood_group)

        # Step 1: Get hospital details
        hospital_resp = table.get_item(Key={'user_id': hospital_id})
        hospital = hospital_resp.get('Item')
        
        if not hospital:
            return {"success": False, "error": "Hospital not found"}
        
        hospital_lat = float(hospital.get('latitude', 0))
        hospital_lon = float(hospital.get('longitude', 0))
        
        # Step 2: Get all donors
        response = table.scan(Limit=500)
        all_donors = response.get('Items', [])
        
        # Step 3: Filter nearby donors and calculate scores
        nearby_donors = []
        for donor in all_donors:
            donor_bg = donor.get('blood_group', '')
            donor_status = donor.get('status', '')
            donor_eligibility = donor.get('eligibility_status', '')
            
            if (donor_bg == normalized_blood_group and 
                donor_status == 'active' and 
                donor_eligibility == 'eligible'):
                
                donor_lat = donor.get('latitude')
                donor_lon = donor.get('longitude')
                
                if donor_lat and donor_lon:
                    distance = calculate_distance(donor_lat, donor_lon, hospital_lat, hospital_lon)
                    
                    if distance <= max_distance_km:
                        donor['reliability_score'] = calculate_reliability_score(donor)
                        donor['distance_km'] = round(distance, 2)
                        nearby_donors.append(donor)
        
        # Step 4: Sort by reliability score
        nearby_donors.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
        
        # Step 5: Create cascade tiers (20% each)
        total = len(nearby_donors)
        tier_size = max(1, total // 5) if total > 0 else 0
        
        tier1 = nearby_donors[:tier_size]
        tier2 = nearby_donors[tier_size: tier_size * 2] if tier_size > 0 else []
        tier3 = nearby_donors[tier_size * 2: tier_size * 3] if tier_size > 0 else []
        tier4 = nearby_donors[tier_size * 3:] if tier_size > 0 else []
        
        # Step 6: Send WhatsApp to Tier 1 donors
        notified_count = 0
        for donor in tier1:
            phone = donor.get('phone_number')
            if phone and phone != 'null' and phone != 'None':
                try:
                    print(f"📨 Sending donation request to donor {phone}...")
                    message = client.messages.create(
                        body=f"""🩸 *URGENT: Blood Donation Request*

A patient needs {blood_group} blood at:
🏥 {hospital.get('name')}
📍 {hospital.get('address')}
⏰ {donation_time}
📏 You are {donor.get('distance_km')} km away

Reply:
✅ *YES* - I can donate
❌ *NO* - I cannot donate

*You can save a life!* 🩸""",
                        from_=TWILIO_WHATSAPP_NUMBER,
                        to=f"whatsapp:{phone}"
                    )
                    notified_count += 1
                    print(f"✅ Twilio message accepted for {phone}. SID: {message.sid}")
                    
                    # Update donor notification status
                    table.update_item(
                        Key={'user_id': donor['user_id']},
                        UpdateExpression="SET notification_tier = :tier, last_notification_time = :time, notification_response = :resp",
                        ExpressionAttributeValues={
                            ":tier": "tier1",
                            ":time": datetime.now().isoformat(),
                            ":resp": "sent"
                        }
                    )
                except Exception as e:
                    print(f"Error sending to {phone}: {e}")
        
        return {
            "success": True,
            "hospital": hospital.get('name'),
            "blood_group": normalized_blood_group,
            "max_distance_km": max_distance_km,
            "total_nearby_donors": total,
            "cascade": {
                "tier1_count": len(tier1),
                "tier2_count": len(tier2),
                "tier3_count": len(tier3),
                "tier4_count": len(tier4)
            },
            "notified_count": notified_count,
            "message": f"Sent donation requests to {notified_count} nearby donors (Tier 1)"
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/hospitals")
async def list_hospitals():
    """Get all hospitals"""
    try:
        response = table.scan()
        hospitals = []
        for item in response.get('Items', []):
            if item.get('role') == 'Hospital':
                hospitals.append({
                    "id": item.get('user_id'),
                    "name": item.get('name'),
                    "address": item.get('address'),
                    "latitude": item.get('latitude'),
                    "longitude": item.get('longitude')
                })
        return {"success": True, "hospitals": hospitals}
    except Exception as e:
        return {"success": False, "error": str(e)}