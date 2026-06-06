# backend/test_new_columns.py
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

# Get one donor to test with
response = table.scan(Limit=1)
donors = response.get('Items', [])

if not donors:
    print("❌ No donors found in table")
    exit()

test_donor = donors[0]
donor_id = test_donor.get('user_id')

print(f"Testing with donor: {donor_id[:50]}...")

# Add new columns to this donor (DynamoDB will add them automatically)
try:
    table.update_item(
        Key={'user_id': donor_id},
        UpdateExpression="SET notification_tier = :tier, notification_response = :resp, last_notification_time = :time",
        ExpressionAttributeValues={
            ":tier": "pending",
            ":resp": "none",
            ":time": datetime.now().isoformat()
        }
    )
    print("✅ Successfully added new columns to donor!")
    print("   - notification_tier")
    print("   - notification_response") 
    print("   - last_notification_time")
    
    # Verify they were added
    verify = table.get_item(Key={'user_id': donor_id})
    item = verify.get('Item', {})
    
    print("\n✅ Verification - New fields added:")
    print(f"   notification_tier: {item.get('notification_tier', 'NOT FOUND')}")
    print(f"   notification_response: {item.get('notification_response', 'NOT FOUND')}")
    print(f"   last_notification_time: {item.get('last_notification_time', 'NOT FOUND')}")
    
except Exception as e:
    print(f"❌ Error: {e}")