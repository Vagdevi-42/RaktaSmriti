from fastapi import APIRouter, HTTPException, Query
import boto3

router = APIRouter(prefix="/api/donors", tags=["donors"])

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

def get_value(item, key):
    """Extract value from DynamoDB item (handles S, N, or direct)"""
    if key in item:
        val = item[key]
        if isinstance(val, dict):
            return val.get('S', val.get('N', str(val)))
        return str(val)
    return None

@router.get("/blood-group/{blood_group}")
async def get_by_blood_group(blood_group: str, limit: int = Query(20)):
    try:
        response = table.scan(Limit=100)
        all_donors = response.get('Items', [])
        
        # Filter by blood group
        matched = []
        for donor in all_donors:
            donor_bg = get_value(donor, 'blood_group')
            if donor_bg == blood_group:
                donor['blood_group'] = donor_bg
                matched.append(donor)
                if len(matched) >= limit:
                    break
        
        return {
            "success": True,
            "blood_group": blood_group,
            "count": len(matched),
            "donors": matched
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_by_id(user_id: str):
    try:
        response = table.get_item(Key={'user_id': user_id})
        donor = response.get('Item')
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        return {"success": True, "donor": donor}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))