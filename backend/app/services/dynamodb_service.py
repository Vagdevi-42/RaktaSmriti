import boto3
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

# Use your existing table
users_table = dynamodb.Table('team81-user')

class UserModel:
    
    @staticmethod
    def find_by_user_id(user_id):
        """Find a user by user_id (Partition Key)"""
        try:
            response = users_table.get_item(Key={'user_id': user_id})
            return response.get('Item')
        except Exception as e:
            print(f"Error finding user: {e}")
            return None
    
    @staticmethod
    def scan_all(limit=100):
        """Get all users (use carefully)"""
        try:
            response = users_table.scan(Limit=limit)
            return response.get('Items', [])
        except Exception as e:
            print(f"Error scanning users: {e}")
            return []
    
    @staticmethod
    def get_donors_by_blood_group(blood_group):
        """Get donors by blood group"""
        try:
            response = users_table.scan(
                FilterExpression='blood_group = :blood_group AND role = :role',
                ExpressionAttributeValues={
                    ':blood_group': blood_group,
                    ':role': 'Emergency Donor'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error finding donors: {e}")
            return []
    
    @staticmethod
    def get_eligible_donors():
        """Get all eligible donors"""
        try:
            response = users_table.scan(
                FilterExpression='eligibility_status = :status',
                ExpressionAttributeValues={':status': 'eligible'}
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error finding eligible donors: {e}")
            return []