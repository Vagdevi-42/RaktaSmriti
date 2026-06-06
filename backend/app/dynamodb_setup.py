import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

def create_tables():
    """Create all required DynamoDB tables"""
    
    # Users Table
    try:
        users_table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'phone', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'EmailIndex',
                    'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'PhoneIndex',
                    'KeySchema': [{'AttributeName': 'phone', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✅ Users table created")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✅ Users table already exists")
        else:
            print(f"❌ Error creating Users table: {e}")
    
    print("\n🎉 DynamoDB setup complete!")

if __name__ == '__main__':
    create_tables()