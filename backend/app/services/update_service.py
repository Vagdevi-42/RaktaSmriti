# backend/app/services/update_service.py
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table('team81-user')

def update_donor_after_donation(donor_id, coordinator_verified=True):
    """
    Called when donor actually donates blood.
    Updates:
    - donations_till_date (+1)
    - last_donation_date (today)
    - next_eligible_date (today + 90 days)
    - eligibility_status (becomes "not eligible" for 90 days)
    - reliability_score (recalculated)
    """
    try:
        # Get current donor
        response = table.get_item(Key={'user_id': donor_id})
        donor = response.get('Item', {})
        
        # Current values
        current_donations = int(donor.get('donations_till_date', 0) or 0)
        new_donations = current_donations + 1
        
        today = datetime.now().isoformat()
        next_eligible = (datetime.now() + timedelta(days=90)).isoformat()
        
        # Update donor
        table.update_item(
            Key={'user_id': donor_id},
            UpdateExpression="""
                SET donations_till_date = :new_donations,
                    last_donation_date = :today,
                    next_eligible_date = :next_eligible,
                    eligibility_status = :status,
                    last_donation_verified = :verified,
                    coordinator_verified_time = :verify_time
            """,
            ExpressionAttributeValues={
                ":new_donations": new_donations,
                ":today": today,
                ":next_eligible": next_eligible,
                ":status": "not eligible",
                ":verified": coordinator_verified,
                ":verify_time": datetime.now().isoformat()
            }
        )
        
        # Also update notification response to 'completed'
        table.update_item(
            Key={'user_id': donor_id},
            UpdateExpression="SET notification_response = :resp",
            ExpressionAttributeValues={":resp": "completed"}
        )
        
        return {"success": True, "donor_id": donor_id, "new_donations": new_donations}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_patient_after_transfusion(patient_id, blood_units_used=1):
    """
    Called when patient receives blood.
    Updates:
    - last_transfusion_date (today)
    - expected_next_transfusion_date (recalculate based on history)
    """
    try:
        response = table.get_item(Key={'user_id': patient_id})
        patient = response.get('Item', {})
        
        today = datetime.now().isoformat()
        
        # Calculate next expected date (default 30 days, can be customized)
        next_expected = (datetime.now() + timedelta(days=30)).isoformat()
        
        table.update_item(
            Key={'user_id': patient_id},
            UpdateExpression="""
                SET last_transfusion_date = :today,
                    expected_next_transfusion_date = :next_expected,
                    last_transfusion_units = :units
            """,
            ExpressionAttributeValues={
                ":today": today,
                ":next_expected": next_expected,
                ":units": blood_units_used
            }
        )
        
        return {"success": True, "patient_id": patient_id}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def mark_donor_response(donor_id, response, scheduled_date=None):
    """
    Update donor's response to notification.
    Responses: 'yes', 'no', 'scheduled', 'completed', 'no_show'
    """
    try:
        update_expr = "SET notification_response = :resp, response_time = :time"
        expr_values = {
            ":resp": response,
            ":time": datetime.now().isoformat()
        }
        
        if scheduled_date:
            update_expr += ", scheduled_donation_time = :sched"
            expr_values[":sched"] = scheduled_date
        
        table.update_item(
            Key={'user_id': donor_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        return {"success": True, "donor_id": donor_id, "response": response}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_multiple_yes_responses(donation_request_id, donors_who_said_yes, units_needed=1):
    """
    Scenario: 3 donors said YES, but only 2 units needed.
    - First 2 donors get confirmed
    - 3rd donor gets "on standby" notification
    
    Returns: confirmed_donors, standby_donors
    """
    confirmed = donors_who_say_yes[:units_needed]
    standby = donors_who_say_yes[units_needed:]
    
    for donor in confirmed:
        mark_donor_response(donor['user_id'], 'confirmed')
        # Send confirmation message
        
    for donor in standby:
        mark_donor_response(donor['user_id'], 'standby')
        # Send standby message
    
    return {
        "confirmed": confirmed,
        "standby": standby,
        "units_needed": units_needed,
        "units_fulfilled": len(confirmed)
    }