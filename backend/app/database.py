import boto3
import os

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'team81-user')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def get_table():
    return table

def get_donor_by_id(user_id: str):
    try:
        response = table.get_item(Key={'user_id': user_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error: {e}")
        return None

def scan_donors(filter_expression=None, expression_values=None, limit=100):
    try:
        if filter_expression:
            response = table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values,
                Limit=limit
            )
        else:
            response = table.scan(Limit=limit)
        return response.get('Items', [])
    except Exception as e:
        print(f"Error: {e}")
        return []