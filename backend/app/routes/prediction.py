# backend/app/routes/prediction.py - FIXED VERSION
from fastapi import APIRouter, HTTPException
import os
import boto3
from datetime import datetime, timedelta
from collections import defaultdict

router = APIRouter(prefix="/api/predict", tags=["prediction"])

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

@router.get("/patients/need-blood")
async def predict_patients_need_blood(days_ahead: int = 7):
    """
    Predict which patients will need blood in next X days
    """
    try:
        # Scan without filter (handle reserved keywords in code)
        response = table.scan(Limit=500)
        all_items = response.get('Items', [])
        
        today = datetime.now()
        need_blood = []
        urgent = []
        
        for item in all_items:
            # Get role safely
            role = get_value(item, 'role')
            
            # Check if this is a patient
            if not role or 'Patient' not in role:
                continue
            
            expected_date_str = get_value(item, 'expected_next_transfusion_date')
            if not expected_date_str:
                continue
            
            # Parse date
            try:
                expected_date = datetime.fromisoformat(expected_date_str.replace(' ', 'T'))
            except:
                try:
                    expected_date = datetime.strptime(expected_date_str, '%Y-%m-%d')
                except:
                    continue
            
            days_until = (expected_date - today).days
            
            patient_info = {
                "patient_id": get_value(item, 'user_id'),
                "blood_group": get_value(item, 'blood_group'),
                "last_transfusion": get_value(item, 'last_transfusion_date'),
                "expected_date": expected_date_str,
                "days_until": days_until
            }
            
            if 0 <= days_until <= days_ahead:
                need_blood.append(patient_info)
            elif days_until < 0:
                urgent.append(patient_info)
        
        # Sort by urgency
        need_blood.sort(key=lambda x: x['days_until'])
        urgent.sort(key=lambda x: x['days_until'])
        
        # Group by blood group
        bg_summary = defaultdict(int)
        for p in need_blood:
            if p['blood_group']:
                bg_summary[p['blood_group']] += 1
        
        return {
            "success": True,
            "days_ahead": days_ahead,
            "urgent_patients": len(urgent),
            "upcoming_patients": len(need_blood),
            "blood_group_summary": dict(bg_summary),
            "urgent_list": urgent[:10],
            "upcoming_list": need_blood[:20]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shortage/{blood_group}")
async def predict_shortage(blood_group: str):
    """
    Predict if there will be shortage for a blood group
    """
    try:
        # Get all items (filter in code to avoid reserved keywords)
        response = table.scan(Limit=500)
        all_items = response.get('Items', [])
        
        # Count patients needing this blood group
        patients_need = 0
        for item in all_items:
            role = get_value(item, 'role')
            bg = get_value(item, 'blood_group')
            expected_date = get_value(item, 'expected_next_transfusion_date')
            
            if role and 'Patient' in role and bg == blood_group and expected_date:
                patients_need += 1
        
        # Count active eligible donors for this blood group
        donors_available = 0
        for item in all_items:
            role = get_value(item, 'role')
            bg = get_value(item, 'blood_group')
            status = get_value(item, 'status')
            eligibility = get_value(item, 'eligibility_status')
            
            # Donor roles: Bridge Donor, Emergency Donor
            if role and ('Donor' in role) and bg == blood_group:
                if status == 'active' and eligibility == 'eligible':
                    donors_available += 1
        
        # Calculate shortage risk
        shortage_risk = "LOW"
        if donors_available < patients_need:
            shortage_risk = "HIGH"
        elif donors_available < patients_need * 1.5:
            shortage_risk = "MEDIUM"
        
        return {
            "success": True,
            "blood_group": blood_group,
            "patients_need": patients_need,
            "donors_available": donors_available,
            "shortage_risk": shortage_risk,
            "recommendation": f"Need {max(0, patients_need - donors_available)} more donors" if shortage_risk != "LOW" else "Sufficient donors available"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/donors/by-blood-group/{blood_group}")
async def get_donor_count_by_blood_group(blood_group: str):
    """
    Count donors by blood group
    """
    try:
        response = table.scan(Limit=500)
        all_items = response.get('Items', [])
        
        count = 0
        for item in all_items:
            role = get_value(item, 'role')
            bg = get_value(item, 'blood_group')
            status = get_value(item, 'status')
            eligibility = get_value(item, 'eligibility_status')
            
            if role and ('Donor' in role) and bg == blood_group:
                if status == 'active' and eligibility == 'eligible':
                    count += 1
        
        return {
            "success": True,
            "blood_group": blood_group,
            "eligible_donors": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))