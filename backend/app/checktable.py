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

table = dynamodb.Table('team81-user')

# Scan first 5 items to see structure
response = table.scan(Limit=5)
items = response.get('Items', [])

print(f"Found {len(items)} sample items\n")

for item in items:
    print("Item structure:")
    for key, value in item.items():
        print(f"  {key}: {value}")
    print("-" * 50)