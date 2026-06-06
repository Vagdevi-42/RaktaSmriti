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

users_table = dynamodb.Table('team81-user')

class UserModel:
    
    @staticmethod
    def get_all_users(limit=100):
        try:
            response = users_table.scan(Limit=limit)
            return response.get('Items', [])
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    @staticmethod
    def get_donors_by_blood_group(blood_group):
        """Get Emergency Donors by blood group"""
        try:
            # First get all Emergency Donors
            response = users_table.scan(
                FilterExpression='role = :role',
                ExpressionAttributeValues={':role': 'Emergency Donor'}
            )
            all_donors = response.get('Items', [])
            
            # Filter by blood group in Python (more reliable)
            filtered = []
            for donor in all_donors:
                if donor.get('blood_group') == blood_group:
                    filtered.append(donor)
            
            return filtered
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    @staticmethod
    def get_donation_stats():
        try:
            users = UserModel.get_all_users(500)
            
            total_donors = 0
            eligible_donors = 0
            blood_group_count = {}
            
            for user in users:
                if user.get('role') == 'Emergency Donor':
                    total_donors += 1
                    if user.get('eligibility_status') == 'eligible':
                        eligible_donors += 1
                    
                    bg = user.get('blood_group', 'Unknown')
                    blood_group_count[bg] = blood_group_count.get(bg, 0) + 1
            
            return {
                'total_donors': total_donors,
                'eligible_donors': eligible_donors,
                'blood_group_distribution': blood_group_count
            }
        except Exception as e:
            print(f"Error: {e}")
            return {}