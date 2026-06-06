# backend/app/routes/ghost_donor.py - COMPLETE WORKING VERSION
from fastapi import APIRouter, HTTPException, Request, Response
import boto3
import uuid
import qrcode
from io import BytesIO
import base64
from datetime import datetime

router = APIRouter(prefix="/api/ghost", tags=["ghost_donor"])

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

def get_value(item, key):
    if key in item:
        val = item[key]
        if isinstance(val, dict):
            return val.get('S', val.get('N', str(val)))
        return str(val)
    return None

@router.get("/qr/{campaign_id}")
async def generate_qr_registration(campaign_id: str):
    reg_id = str(uuid.uuid4())[:8]
    
    table.put_item(
        Item={
            'user_id': f"GHOST_{reg_id}",
            'role': 'Ghost_Donor',
            'status': 'pending_medical',
            'campaign_id': campaign_id,
            'registration_time': datetime.now().isoformat()
        }
    )
    
    whatsapp_link = f"https://wa.me/14155238886?text=I%20want%20to%20register%20as%20blood%20donor%20{reg_id}"
    
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(whatsapp_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return {
        "success": True,
        "registration_id": reg_id,
        "whatsapp_link": whatsapp_link,
        "qr_code_base64": qr_base64,
        "instructions": "Scan this QR code with your phone camera to open WhatsApp and register"
    }

@router.get("/qr-image/{campaign_id}")
async def get_qr_image(campaign_id: str):
    reg_id = str(uuid.uuid4())[:8]
    
    table.put_item(
        Item={
            'user_id': f"GHOST_{reg_id}",
            'role': 'Ghost_Donor',
            'status': 'pending_medical',
            'campaign_id': campaign_id,
            'registration_time': datetime.now().isoformat()
        }
    )
    
    whatsapp_link = f"https://wa.me/14155238886?text=I%20want%20to%20register%20as%20blood%20donor%20{reg_id}"
    
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(whatsapp_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    
    return Response(content=buffered.getvalue(), media_type="image/png")

@router.post("/register")
async def register_ghost_donor(request: Request):
    try:
        form = await request.form()
        reg_id = form.get('reg_id')
        name = form.get('name')
        blood_group = form.get('blood_group')
        phone_number = form.get('phone_number')
        latitude = form.get('latitude')
        longitude = form.get('longitude')
        
        donor_id = f"GHOST_{reg_id}"
        
        table.update_item(
            Key={'user_id': donor_id},
            UpdateExpression="SET #name = :name, blood_group = :bg, phone_number = :phone, latitude = :lat, longitude = :lon, status = :status, registration_complete = :complete",
            ExpressionAttributeNames={"#name": "name"},
            ExpressionAttributeValues={
                ":name": name,
                ":bg": blood_group,
                ":phone": phone_number,
                ":lat": latitude,
                ":lon": longitude,
                ":status": "pending_medical_check",
                ":complete": datetime.now().isoformat()
            }
        )
        
        return {"success": True, "message": "Registration complete!", "donor_id": donor_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/medical-check/{donor_id}")
async def pass_medical_check(donor_id: str, is_eligible: bool = True):
    try:
        if is_eligible:
            table.update_item(
                Key={'user_id': donor_id},
                UpdateExpression="SET role = :new_role, status = :status, eligibility_status = :elig, medical_check_date = :date, is_ghost_converted = :converted",
                ExpressionAttributeValues={
                    ":new_role": "Emergency Donor",
                    ":status": "active",
                    ":elig": "eligible",
                    ":date": datetime.now().isoformat(),
                    ":converted": True
                }
            )
            return {"success": True, "message": "Ghost donor converted to Emergency Donor!", "donor_id": donor_id}
        else:
            table.update_item(
                Key={'user_id': donor_id},
                UpdateExpression="SET status = :status",
                ExpressionAttributeValues={":status": "medical_ineligible"}
            )
            return {"success": False, "message": "Donor not eligible"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_ghost_donors():
    """List all ghost donors"""
    try:
        response = table.scan()
        all_items = response.get('Items', [])
        
        ghost_donors = []
        for item in all_items:
            role = get_value(item, 'role')
            if role and 'Ghost' in role:
                ghost_donors.append({
                    "user_id": get_value(item, 'user_id'),
                    "role": role,
                    "status": get_value(item, 'status'),
                    "name": get_value(item, 'name'),
                    "blood_group": get_value(item, 'blood_group'),
                    "registration_time": get_value(item, 'registration_time')
                })
        
        return {
            "success": True,
            "count": len(ghost_donors),
            "ghost_donors": ghost_donors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))