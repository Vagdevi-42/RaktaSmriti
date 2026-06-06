import boto3
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

table = dynamodb.Table('Users')

# Scan all users
response = table.scan()
users = response.get('Items', [])

print(f"Found {len(users)} user(s) in database:\n")

for user in users:
    print(f"📧 Email: {user.get('email')}")
    print(f"👤 Name: {user.get('name')}")
    print(f"🩸 Blood Type: {user.get('blood_type')}")
    print(f"🆔 User ID: {user.get('user_id')}")
    print("-" * 40)