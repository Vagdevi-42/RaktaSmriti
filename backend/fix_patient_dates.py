# backend/fix_patient_dates_demo.py
import boto3
from datetime import datetime, timedelta
import random

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

# Scan all patients
response = table.scan()
all_items = response.get('Items', [])

today = datetime.now()
count = 0

for item in all_items:
    role = item.get('role', '')
    if 'Patient' in role:
        # Random days between 1 and 7 for demo
        random_days = random.randint(1, 7)
        new_expected_date = (today + timedelta(days=random_days)).isoformat()
        
        table.update_item(
            Key={'user_id': item['user_id']},
            UpdateExpression="SET expected_next_transfusion_date = :new_date",
            ExpressionAttributeValues={":new_date": new_expected_date}
        )
        count += 1
        print(f"Updated patient: will need blood in {random_days} days")

print(f"\n✅ Updated {count} patients - they will need blood in 1-7 days")