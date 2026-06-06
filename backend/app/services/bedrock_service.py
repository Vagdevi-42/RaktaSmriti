# backend/app/services/bedrock_service.py
import boto3
import json

# Initialize Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # Make sure Bedrock is available in this region
)

def generate_thank_you_message(donor_name, donation_count, hospital_name):
    """
    Use Claude (AWS Bedrock) to generate a personalized thank you message
    """
    prompt = f"""You are a compassionate blood bank coordinator. Write a warm, personalized thank you message to a blood donor.

Donor Name: {donor_name}
Total Donations: {donation_count}
Hospital: {hospital_name}

The message should:
1. Be heartfelt and appreciative
2. Mention that they saved lives
3. Be conversational and warm (like a real person)
4. Be 2-3 sentences only
5. Include emojis

Write the message directly (no quotes, no labels):"""

    try:
        # Claude 3 Sonnet model
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        message = response_body['content'][0]['text']
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        print(f"Bedrock error: {e}")
        # Fallback message if Bedrock fails
        return {
            "success": False,
            "message": f"Thank you {donor_name}! Your {donation_count}th donation saved lives at {hospital_name}. You're a hero! 🩸"
        }

def generate_follow_up_reminder(donor_name, next_eligible_date):
    """
    Generate a follow-up reminder message for when donor becomes eligible again
    """
    prompt = f"""Write a short, friendly WhatsApp message reminding a blood donor that they will be eligible to donate again on {next_eligible_date}.

Donor Name: {donor_name}

The message should be encouraging and warm. Keep it to 2 sentences."""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 150,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        message = response_body['content'][0]['text']
        
        return {"success": True, "message": message}
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Hi {donor_name}! You'll be eligible to donate again on {next_eligible_date}. We hope to see you then! 🩸"
        }