# backend/app/routes/patient_prediction.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from collections import defaultdict
import os
import boto3

from .donation_request import send_to_nearby_donors

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

def _normalize_blood_group(blood_group: str) -> str:
    """Normalize common blood-group aliases to match donor records."""
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


@router.get("/patients")
async def predict_patients_needing_blood(
    days_ahead: int = Query(7, ge=1, le=30, description="Look ahead X days"),
    include_overdue: bool = Query(True, description="Include overdue patients"),
    auto_trigger: bool = Query(False, description="Automatically send donation requests for predicted blood groups"),
    hospital_id: str = Query("HOSPITAL_CITY", description="Hospital id used for auto-trigger"),
    max_distance_km: float = Query(5, ge=1, le=50, description="Donor radius for auto-trigger"),
    donation_time: str = Query("Tomorrow, 10:00 AM", description="Donation time text shown to donors")
):
    """
    AI Prediction: Find patients who will need blood in next X days
    Based on expected_next_transfusion_date from medical history
    """
    try:
        # Scan all records
        response = table.scan(Limit=500)
        all_items = response.get('Items', [])
        
        today = datetime.now()
        need_blood = []
        urgent = []
        blood_group_summary = defaultdict(int)
        
        for item in all_items:
            # Check if this is a patient
            role = get_value(item, 'role')
            if not role or 'Patient' not in role:
                continue
            
            # Get expected transfusion date
            expected_date_str = get_value(item, 'expected_next_transfusion_date')
            if not expected_date_str:
                continue
            
            # Parse date (handles different formats)
            try:
                expected_date = datetime.fromisoformat(expected_date_str.replace(' ', 'T'))
            except:
                try:
                    expected_date = datetime.strptime(expected_date_str, '%Y-%m-%d')
                except:
                    continue
            
            days_until = (expected_date - today).days
            blood_group = get_value(item, 'blood_group') or 'Unknown'
            
            patient_info = {
                "patient_id": get_value(item, 'user_id'),
                "blood_group": blood_group,
                "last_transfusion": get_value(item, 'last_transfusion_date'),
                "expected_date": expected_date_str,
                "days_until": days_until,
                "status": get_value(item, 'status')
            }
            
            # Check if overdue
            if days_until < 0 and include_overdue:
                urgent.append(patient_info)
                blood_group_summary[blood_group] += 1
            
            # Check if needs blood in upcoming days
            elif 0 <= days_until <= days_ahead:
                need_blood.append(patient_info)
                blood_group_summary[blood_group] += 1
        
        # Sort by urgency (closest first)
        need_blood.sort(key=lambda x: x['days_until'])
        urgent.sort(key=lambda x: x['days_until'])  # Most overdue first

        response = {
            "success": True,
            "days_ahead": days_ahead,
            "total_patients_scanned": len([i for i in all_items if 'Patient' in get_value(i, 'role')]),
            "urgent_patients": len(urgent),
            "upcoming_patients": len(need_blood),
            "blood_group_summary": dict(blood_group_summary),
            "urgent_list": urgent[:10],
            "upcoming_list": need_blood[:20],
            "message": f"Found {len(urgent)} urgent and {len(need_blood)} upcoming patients needing blood"
        }

        if auto_trigger:
            triggered_requests = []
            for blood_group_name, patients_needing in blood_group_summary.items():
                if patients_needing <= 0:
                    continue
                normalized_group = _normalize_blood_group(blood_group_name)
                send_result = await send_to_nearby_donors(
                    blood_group=normalized_group,
                    hospital_id=hospital_id,
                    max_distance_km=max_distance_km,
                    donation_time=donation_time
                )
                triggered_requests.append({
                    "blood_group": normalized_group,
                    "patients_needing": patients_needing,
                    "result": send_result
                })
            response["auto_triggered"] = True
            response["triggered_requests"] = triggered_requests

        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trigger/{blood_group}")
async def auto_trigger_donation(blood_group: str, days_ahead: int = 7, demo_mode: bool = False):
    """
    AI Auto-Trigger: prepare donation requests for patients.
    In demo mode it returns the generated message payload without sending real WhatsApp messages.
    """
    try:
        # First, get patients needing this blood group
        prediction = await predict_patients_needing_blood(days_ahead)
        
        if not prediction.get('success'):
            return {"success": False, "error": "Prediction failed"}
        
        # Count how many patients need this blood group
        patients_needing = prediction.get('blood_group_summary', {}).get(blood_group, 0)

        if patients_needing == 0:
            return {
                "success": True,
                "demo_mode": demo_mode,
                "message": f"No patients need {blood_group} blood in next {days_ahead} days",
                "patients_needing": 0,
                "urgent_count": prediction.get('urgent_patients', 0),
                "action": "Demo mode only: no real Twilio message is sent." if demo_mode else "Would automatically trigger donation requests to nearby donors"
            }

        demo_message = (
            f"AI Prediction demo: {patients_needing} patient(s) need {blood_group} blood in next {days_ahead} days. "
            "This response is for demonstration only; Twilio is not called in demo mode."
        )

        if demo_mode:
            return {
                "success": True,
                "demo_mode": True,
                "message": demo_message,
                "patients_needing": patients_needing,
                "urgent_count": prediction.get('urgent_patients', 0),
                "action": "Demo mode only: no real Twilio message is sent.",
                "next_step": "Use demo mode to show the prediction flow without consuming Twilio credits"
            }

        send_result = await send_to_nearby_donors(
            blood_group=blood_group,
            hospital_id="HOSPITAL_CITY",
            max_distance_km=5,
            donation_time="Tomorrow, 10:00 AM"
        )

        return {
            "success": send_result.get('success', False),
            "demo_mode": False,
            "message": f"AI Prediction: {patients_needing} patient(s) need {blood_group} blood in next {days_ahead} days",
            "patients_needing": patients_needing,
            "urgent_count": prediction.get('urgent_patients', 0),
            "action": "Triggered nearby donor WhatsApp requests",
            "twilio": send_result,
            "next_step": "Check the Twilio logs or donor replies to continue the donation flow"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))