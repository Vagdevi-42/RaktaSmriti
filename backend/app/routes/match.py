# backend/app/routes/match.py - COMPLETE REPLACEMENT
from fastapi import APIRouter, HTTPException, Query
import os
import boto3
import math
from datetime import datetime
from datetime import datetime, timedelta  # Add this
router = APIRouter(prefix="/api/match", tags=["matching"])

dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table('team81-user')

def get_value(item, key):
    """Extract value from DynamoDB item"""
    if key in item:
        val = item[key]
        if isinstance(val, dict):
            return val.get('S', val.get('N', str(val)))
        return str(val)
    return None

def calculate_reliability_score(donor):
    """Calculate donor reliability score (0-100)"""
    donations = int(get_value(donor, 'donations_till_date') or 0)
    total_calls = int(get_value(donor, 'total_calls') or 1)
    
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
    
    if get_value(donor, 'status') == 'active':
        score += 15
    if get_value(donor, 'eligibility_status') == 'eligible':
        score += 15
    
    return min(score, 100)

def get_cascade_tiers(donors, top_percent=20):
    """Divide donors into tiers based on reliability score"""
    if not donors:
        return [], [], [], []
    
    # Calculate scores
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

@router.get("/donors")
async def match_donors(
    blood_group: str = Query(..., description="Required blood group"),
    limit: int = Query(5, ge=1, le=20)
):
    """5-Step Filtering: Get top donors by reliability score"""
    try:
        # Scan donors
        response = table.scan(Limit=200)
        all_donors = response.get('Items', [])
        
        # Filter: blood group match + active + eligible
        eligible_donors = []
        for donor in all_donors:
            donor_bg = get_value(donor, 'blood_group')
            donor_status = get_value(donor, 'status')
            donor_eligibility = get_value(donor, 'eligibility_status')
            
            if (donor_bg == blood_group and 
                donor_status == 'active' and 
                donor_eligibility == 'eligible'):
                
                donor['reliability_score'] = calculate_reliability_score(donor)
                donor['blood_group'] = donor_bg
                eligible_donors.append(donor)
        
        # Sort by reliability score
        eligible_donors.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
        
        # Get tiers for cascade
        tier1, tier2, tier3, tier4 = get_cascade_tiers(eligible_donors)
        
        return {
            "success": True,
            "blood_group": blood_group,
            "total_matched": len(eligible_donors),
            "returned": min(len(eligible_donors), limit),
            "donors": eligible_donors[:limit],
            "cascade_tiers": {
                "tier1_count": len(tier1),
                "tier2_count": len(tier2),
                "tier3_count": len(tier3),
                "tier4_count": len(tier4)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cascade/start")
async def start_cascade(
    blood_group: str,
    hospital_name: str,
    hospital_address: str,
    donation_time: str,
    required_units: int = 1
):
    """Start cascade notification - sends to Tier 1 first"""
    try:
        # Get eligible donors
        response = table.scan(Limit=200)
        all_donors = response.get('Items', [])
        
        eligible_donors = []
        for donor in all_donors:
            donor_bg = get_value(donor, 'blood_group')
            donor_status = get_value(donor, 'status')
            donor_eligibility = get_value(donor, 'eligibility_status')
            
            if (donor_bg == blood_group and 
                donor_status == 'active' and 
                donor_eligibility == 'eligible'):
                donor['reliability_score'] = calculate_reliability_score(donor)
                eligible_donors.append(donor)
        
        # Get tiers
        tier1, tier2, tier3, tier4 = get_cascade_tiers(eligible_donors)
        
        # Mark that we notified Tier 1
        for donor in tier1:
            table.update_item(
                Key={'user_id': donor['user_id']},
                UpdateExpression="SET notification_tier = :tier, last_notification_time = :time, notification_response = :resp",
                ExpressionAttributeValues={
                    ":tier": "tier1",
                    ":time": datetime.now().isoformat(),
                    ":resp": "sent"
                }
            )
        
        return {
            "success": True,
            "blood_group": blood_group,
            "required_units": required_units,
            "tier1_notified": len(tier1),
            "tier2_standby": len(tier2),
            "tier3_standby": len(tier3),
            "tier4_standby": len(tier4),
            "message": f"Notified {len(tier1)} donors. Next tier will be notified after 5 hours if no response."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/donor/response")
async def donor_response(
    donor_id: str,
    response: str,  # "yes", "no", "schedule"
    scheduled_days: int = 0
):
    """Update donor's response to notification"""
    try:
        update_expr = "SET notification_response = :resp, response_time = :time"
        expr_values = {":resp": response, ":time": datetime.now().isoformat()}
        
        if response == "schedule" and scheduled_days > 0:
            scheduled_date = (datetime.now() + timedelta(days=scheduled_days)).isoformat()
            update_expr += ", scheduled_donation_time = :sched"
            expr_values[":sched"] = scheduled_date
        
        table.update_item(
            Key={'user_id': donor_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        return {"success": True, "donor_id": donor_id, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Add this to your existing match.py (after your existing code)

from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers"""
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

def get_hospital(hospital_id="HOSPITAL_CITY"):
    """Get hospital from database"""
    try:
        response = table.get_item(Key={'user_id': hospital_id})
        return response.get('Item')
    except:
        return None

@router.get("/donors/nearby")
async def get_nearby_donors(
    blood_group: str = Query(...),
    hospital_id: str = Query("HOSPITAL_CITY"),
    max_distance_km: float = Query(5, ge=1, le=50),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Get donors by: blood group + active + eligible + WITHIN distance of hospital
    Then sort by reliability score
    """
    try:
        # First, get hospital
        hospital = get_hospital(hospital_id)
        if not hospital:
            return {"success": False, "error": "Hospital not found"}
        
        hospital_lat = float(hospital.get('latitude', 0))
        hospital_lon = float(hospital.get('longitude', 0))
        
        # Get all eligible donors (same as your existing logic)
        response = table.scan(Limit=500)
        all_donors = response.get('Items', [])
        
        eligible_donors = []
        for donor in all_donors:
            donor_bg = get_value(donor, 'blood_group')
            donor_status = get_value(donor, 'status')
            donor_eligibility = get_value(donor, 'eligibility_status')
            
            # Step 1-2: Blood group + Active + Eligible
            if (donor_bg == blood_group and 
                donor_status == 'active' and 
                donor_eligibility == 'eligible'):
                
                # Step 3: Check distance
                donor_lat = get_value(donor, 'latitude')
                donor_lon = get_value(donor, 'longitude')
                
                if donor_lat and donor_lon:
                    distance = calculate_distance(donor_lat, donor_lon, hospital_lat, hospital_lon)
                    
                    # Only include if within max_distance_km
                    if distance <= max_distance_km:
                        donor['distance_km'] = round(distance, 2)
                        donor['reliability_score'] = calculate_reliability_score(donor)
                        donor['blood_group'] = donor_bg
                        eligible_donors.append(donor)
        
        # Step 4: Sort by reliability score (highest first)
        eligible_donors.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
        
        # Step 5: Get cascade tiers
        tier1, tier2, tier3, tier4 = get_cascade_tiers(eligible_donors)
        
        return {
            "success": True,
            "hospital": hospital.get('name'),
            "hospital_location": {"lat": hospital_lat, "lon": hospital_lon},
            "blood_group": blood_group,
            "max_distance_km": max_distance_km,
            "total_nearby_donors": len(eligible_donors),
            "returned": min(len(eligible_donors), limit),
            "donors": eligible_donors[:limit],
            "cascade_tiers": {
                "tier1_count": len(tier1),
                "tier2_count": len(tier2),
                "tier3_count": len(tier3),
                "tier4_count": len(tier4)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))