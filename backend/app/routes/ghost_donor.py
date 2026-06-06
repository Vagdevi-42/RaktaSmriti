# backend/app/routes/ghost_donor.py - ADD QR CODE GENERATION
from fastapi import APIRouter, HTTPException, Response
import boto3
import uuid
import qrcode
from io import BytesIO
from datetime import datetime

router = APIRouter(prefix="/api/ghost", tags=["ghost_donor"])

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

@router.get("/qr/{campaign_id}")
async def generate_qr_registration(campaign_id: str):
    """Generate QR code for ghost donor registration"""
    reg_id = str(uuid.uuid4())[:8]
    
    # Store pending registration
    table.put_item(
        Item={
            'user_id': f"GHOST_{reg_id}",
            'role': 'Ghost_Donor',
            'status': 'pending_medical',
            'campaign_id': campaign_id,
            'registration_time': datetime.now().isoformat()
        }
    )
    
    # WhatsApp registration link
    whatsapp_link = f"https://wa.me/14155238886?text=I%20want%20to%20register%20as%20blood%20donor%20{reg_id}"
    
    # Generate QR code as base64
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(whatsapp_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for HTML display
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    import base64
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return {
        "success": True,
        "registration_id": reg_id,
        "whatsapp_link": whatsapp_link,
        "qr_code_base64": qr_base64,
        "qr_data": whatsapp_link,
        "instructions": "Scan this QR code with your phone camera to open WhatsApp and register"
    }

@router.get("/qr-image/{campaign_id}")
async def get_qr_image(campaign_id: str):
    """Return QR code as image (for direct display)"""
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