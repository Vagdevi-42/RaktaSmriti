# backend/add_hospitals.py
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

hospitals = [
    {
        "user_id": "HOSPITAL_CITY",
        "role": "Hospital",
        "name": "City Blood Bank",
        "address": "123 Main Road, Near Railway Station, City - 500001",
        "latitude": "17.3922792",
        "longitude": "78.4602749",
        "phone": "+911234567890",
        "timings": "24x7",
        "status": "active"
    }
]

print("Adding hospitals to DynamoDB...")

for hospital in hospitals:
    try:
        table.put_item(Item=hospital)
        print(f"✅ Added: {hospital['name']}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("Done!")