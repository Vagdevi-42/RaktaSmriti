# backend/test_dynamodb.py
import boto3
from botocore.exceptions import ClientError

def test_connection():
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1'  # Change to your AWS region
        )
        table = dynamodb.Table('RaktaSmriti_Data')
        response = table.scan(Limit=1)
        print("✅ Connected to DynamoDB!")
        print(f"Table has data: {len(response.get('Items', []))} items")
        return True
    except ClientError as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()