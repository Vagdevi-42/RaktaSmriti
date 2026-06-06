# backend/app/routes/coordinator.py - FIXED
from fastapi import APIRouter, HTTPException
import boto3
from datetime import datetime

router = APIRouter(prefix="/api/coordinator", tags=["coordinator"])

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

def get_value(item, key):
    """Extract value from DynamoDB item"""
    if key in item:
        val = item[key]
        if isinstance(val, dict):
            return val.get('S', val.get('N', str(val)))
        return str(val)
    return None

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