# backend/add_sample_patients.py
import boto3
from datetime import datetime, timedelta
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

# Sample patients with different future dates
today = datetime.now()
sample_patients = [
    {
        "user_id": f"PATIENT_{str(uuid.uuid4())[:8]}",
        "role": "Patient",
        "blood_group": "O Positive",
        "status": "active",
        "eligibility_status": "eligible",
        "last_transfusion_date": (today - timedelta(days=25)).isoformat(),
        "expected_next_transfusion_date": (today + timedelta(days=2)).isoformat(),
        "phone_number": "+917207190981",
        "name": "Urgent Patient O+"
    },
    {
        "user_id": f"PATIENT_{str(uuid.uuid4())[:8]}",
        "role": "Patient",
        "blood_group": "A Positive",
        "status": "active",
        "eligibility_status": "eligible",
        "last_transfusion_date": (today - timedelta(days=20)).isoformat(),
        "expected_next_transfusion_date": (today + timedelta(days=4)).isoformat(),
        "phone_number": "+917207190981",
        "name": "Upcoming Patient A+"
    },
    {
        "user_id": f"PATIENT_{str(uuid.uuid4())[:8]}",
        "role": "Patient",
        "blood_group": "B Positive",
        "status": "active",
        "eligibility_status": "eligible",
        "last_transfusion_date": (today - timedelta(days=30)).isoformat(),
        "expected_next_transfusion_date": (today + timedelta(days=5)).isoformat(),
        "phone_number": "+917207190981",
        "name": "Upcoming Patient B+"
    },
    {
        "user_id": f"PATIENT_{str(uuid.uuid4())[:8]}",
        "role": "Patient",
        "blood_group": "O Positive",
        "status": "active",
        "eligibility_status": "eligible",
        "last_transfusion_date": (today - timedelta(days=35)).isoformat(),
        "expected_next_transfusion_date": (today + timedelta(days=7)).isoformat(),
        "phone_number": "+917207190981",
        "name": "Week Ahead Patient O+"
    },
    {
        "user_id": f"PATIENT_{str(uuid.uuid4())[:8]}",
        "role": "Patient",
        "blood_group": "AB Positive",
        "status": "active",
        "eligibility_status": "eligible",
        "last_transfusion_date": (today - timedelta(days=28)).isoformat(),
        "expected_next_transfusion_date": (today + timedelta(days=3)).isoformat(),
        "phone_number": "+917207190981",
        "name": "Upcoming Patient AB+"
    },
    {
        "user_id": f"PATIENT_{str(uuid.uuid4())[:8]}",
        "role": "Patient",
        "blood_group": "O Negative",
        "status": "active",
        "eligibility_status": "eligible",
        "last_transfusion_date": (today - timedelta(days=40)).isoformat(),
        "expected_next_transfusion_date": (today - timedelta(days=2)).isoformat(),
        "phone_number": "+917207190981",
        "name": "OVERDUE Patient O-"
    }
]

print("=" * 50)
print("Adding sample patients with future dates...")
print("=" * 50)

count = 0
for patient in sample_patients:
    try:
        table.put_item(Item=patient)
        count += 1
        print(f"Added: {patient['name']} - Blood: {patient['blood_group']} - Expected: {patient['expected_next_transfusion_date']}")
    except Exception as e:
        print(f"Error: {e}")

print("=" * 50)
print(f"Added {count} sample patients to database!")
print("Now refresh your dashboard - you should see patients needing blood.")