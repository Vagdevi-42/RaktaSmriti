# backend/find_donors_with_blood.py
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('team81-user')

response = table.scan(Limit=100)

print("Searching for records with blood_group...")
print("=" * 60)

count_with_bg = 0
for item in response.get('Items', []):
    if 'blood_group' in item:
        count_with_bg += 1
        role = item.get('role', {}).get('S', 'N/A')
        bg = item.get('blood_group', {}).get('S', 'N/A')
        print(f"Role: {role} | Blood Group: {bg}")
        if count_with_bg >= 10:
            break

print("=" * 60)
print(f"Found {count_with_bg} records with blood_group in first 100 records")

if count_with_bg == 0:
    print("\n❌ No blood_group found in any record!")
    print("Your table needs to be populated with donor data from the CSV.")