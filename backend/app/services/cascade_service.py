# backend/app/services/cascade_service.py
import os
import boto3
from datetime import datetime, timedelta
import math
from .update_service import mark_donor_response
from .whatsapp_service import send_donation_request

dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table('team81-user')

def get_eligible_donors(blood_group, required_units=1):
    """
    Step 1: Get all donors matching blood group + active + eligible
    """
    response = table.scan(
        FilterExpression="blood_group = :bg AND status = :status AND eligibility_status = :elig",
        ExpressionAttributeValues={
            ":bg": blood_group,
            ":status": "active",
            ":elig": "eligible"
        }
    )
    return response.get('Items', [])

def calculate_reliability_score(donor):
    """Calculate score based on donation history"""
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
        score += 10  # New donors get base score
    
    if donor.get('status') == 'active':
        score += 15
    if donor.get('eligibility_status') == 'eligible':
        score += 15
    
    return min(score, 100)

def get_cascade_tiers(donors, top_percent=20):
    """
    Divide donors into tiers based on reliability score.
    Returns 4 tiers
    """
    if not donors:
        return [], [], [], []
    
    # Calculate reliability score for each donor
    for donor in donors:
        donor['reliability_score'] = calculate_reliability_score(donor)
    
    # Sort by score (highest first)
    donors.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
    
    total = len(donors)
    tier_size = math.ceil(total * top_percent / 100)
    
    tier1 = donors[:tier_size]
    tier2 = donors[tier_size: tier_size * 2] if tier_size * 2 <= total else donors[tier_size:]
    tier3 = donors[tier_size * 2: tier_size * 3] if tier_size * 3 <= total else []
    tier4 = donors[tier_size * 3:] if tier_size * 3 < total else []
    
    return tier1, tier2, tier3, tier4

def send_to_tier(donors, patient_info, hospital_info, donation_time):
    """
    Send WhatsApp notification to all donors in a tier
    """
    sent_count = 0
    for donor in donors:
        result = send_donation_request(donor, patient_info, hospital_info, donation_time)
        if result.get('success'):
            sent_count += 1
            # Mark that we sent notification to this donor
            mark_donor_response(donor['user_id'], 'sent')
    return sent_count

def check_responses(donor_ids, required_units):
    """
    Check how many donors said YES
    """
    yes_count = 0
    for donor_id in donor_ids:
        response = table.get_item(Key={'user_id': donor_id})
        donor = response.get('Item', {})
        if donor.get('notification_response') == 'yes':
            yes_count += 1
    return yes_count

def run_cascade(blood_group, patient_info, hospital_info, donation_time, required_units=1):
    """
    MAIN CASCADE FUNCTION:
    1. Get all eligible donors
    2. Split into tiers
    3. Send to Tier 1
    4. Wait 5 hours, check responses
    5. If not enough, move to Tier 2
    6. Continue until enough donors confirmed
    """
    # Step 1: Get eligible donors
    all_donors = get_eligible_donors(blood_group, required_units)
    
    if not all_donors:
        return {"success": False, "message": "No eligible donors found"}
    
    # Step 2: Create tiers
    tier1, tier2, tier3, tier4 = get_cascade_tiers(all_donors)
    
    result = {
        "success": True,
        "blood_group": blood_group,
        "total_donors": len(all_donors),
        "tier1_count": len(tier1),
        "tier2_count": len(tier2),
        "tier3_count": len(tier3),
        "tier4_count": len(tier4),
        "confirmed_donors": [],
        "cascade_history": []
    }
    
    # Step 3: Send to Tier 1
    sent = send_to_tier(tier1, patient_info, hospital_info, donation_time)
    result["cascade_history"].append({"tier": 1, "notified": sent, "timestamp": datetime.now().isoformat()})
    
    return result

def check_and_escalate(request_id, blood_group, required_units=1):
    """
    Called every hour to check if escalation needed
    Returns True if escalated to next tier
    """
    # Check responses from current tier
    # This would be implemented with a background job
    
    # For now, return placeholder
    return {"escalated": False, "message": "No escalation needed"}