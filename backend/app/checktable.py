# backend/check_table.py
import boto3
from botocore.exceptions import ClientError

def check_table():
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('team81-user')
        
        # Check if table exists
        status = table.table_status
        print(f"✅ Table 'team81-user' exists!")
        print(f"   Status: {status}")
        
        # Scan to see data
        response = table.scan(Limit=5)
        items = response.get('Items', [])
        
        print(f"\n📊 Found {len(items)} items in scan")
        
        if len(items) > 0:
            print("\n📋 Sample data:")
            for item in items[:2]:
                print(f"   user_id: {item.get('user_id', 'N/A')[:30]}...")
                print(f"   role: {item.get('role', 'N/A')}")
                print(f"   blood_group: {item.get('blood_group', 'N/A')}")
                print("   ---")
        else:
            print("\n⚠️ Table is empty. Need to load data.")
            
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("❌ Table 'team81-user' does not exist!")
        else:
            print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_table()