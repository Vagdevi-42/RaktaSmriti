# backend/app/services/hospital_service.py
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

def get_hospital_from_db(hospital_id="HOSPITAL_CITY"):
    """Fetch hospital details from DynamoDB"""
    try:
        response = table.get_item(Key={'user_id': hospital_id})
        hospital = response.get('Item')
        if hospital:
            return {
                "name": hospital.get('name'),
                "address": hospital.get('address'),
                "latitude": float(hospital.get('latitude', 0)),
                "longitude": float(hospital.get('longitude', 0)),
                "phone": hospital.get('phone'),
                "timings": hospital.get('timings')
            }
        return None
    except Exception as e:
        print(f"Error fetching hospital: {e}")
        return None

def get_all_hospitals():
    """Get list of all hospitals"""
    try:
        # Scan for all items with role = "Hospital"
        response = table.scan()
        all_items = response.get('Items', [])
        
        hospitals = []
        for item in all_items:
            if item.get('role') == 'Hospital':
                hospitals.append({
                    "id": item.get('user_id'),
                    "name": item.get('name'),
                    "address": item.get('address'),
                    "latitude": float(item.get('latitude', 0)),
                    "longitude": float(item.get('longitude', 0))
                })
        
        print(f"Found {len(hospitals)} hospitals")  # Debug print
        return hospitals
    except Exception as e:
        print(f"Error: {e}")
        return []