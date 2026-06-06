# backend/setup_demo_numbers_fast.py
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

YOUR_PHONE = "+917207190981"

print("=" * 50)
print("Setting up demo phone numbers (FAST VERSION)...")
print("=" * 50)

# Use batch writer for faster updates
donor_count = 0

# Scan all donors
response = table.scan()
all_items = response.get('Items', [])

print(f"Found {len(all_items)} total records. Processing...")

for item in all_items:
    role = item.get('role', '')
    
    # Update Bridge and Emergency donors without phone numbers
    if ('Bridge' in role or 'Emergency' in role) and not item.get('phone_number'):
        table.update_item(
            Key={'user_id': item['user_id']},
            UpdateExpression="SET phone_number = :phone",
            ExpressionAttributeValues={":phone": YOUR_PHONE}
        )
        donor_count += 1
        if donor_count % 10 == 0:
            print(f"  Updated {donor_count} donors...")

# Handle patient
patients = [i for i in all_items if 'Patient' in i.get('role', '')]

if patients:
    patient = patients[0]
    if not patient.get('phone_number'):
        table.update_item(
            Key={'user_id': patient['user_id']},
            UpdateExpression="SET phone_number = :phone",
            ExpressionAttributeValues={":phone": YOUR_PHONE}
        )
        print(f"✅ Updated existing patient")
else:
    # Create test patient
    test_patient = {
        'user_id': f"PATIENT_{str(uuid.uuid4())[:8]}",
        'role': 'Patient',
        'blood_group': 'O Positive',
        'phone_number': YOUR_PHONE,
        'last_transfusion_date': '2026-05-01',
        'expected_next_transfusion_date': '2026-06-15',
        'status': 'active',
        'eligibility_status': 'eligible'
    }
    table.put_item(Item=test_patient)
    print(f"✅ Created new patient with YOUR phone")

print("=" * 50)
print(f"✅ Added YOUR phone number to {donor_count} donors")
print(f"✅ Your phone: {YOUR_PHONE}")
print("=" * 50)