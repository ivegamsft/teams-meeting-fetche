#!/usr/bin/env python3
"""
Manual Webhook Trigger - Test end-to-end transcript flow
Simulates a Graph API webhook notification and sends it to the Lambda function.
"""
import requests
import json
import sys
from datetime import datetime
sys.path.append("scripts/graph")
from auth_helper import get_config

print("=" * 80)
print("🔔 MANUAL WEBHOOK TRIGGER")
print("=" * 80)

config = get_config()
webhook_url = config['webhook_url']
webhook_secret = config.get('webhook_secret', '')

print(f"\n📋 Webhook Configuration:")
print(f"   URL: {webhook_url}")
print(f"   Auth Secret: {webhook_secret[:20]}..." if webhook_secret else "   Auth Secret: NOT SET")

# Example transcript notification payload (real structure from Graph API)
# This simulates what Microsoft Graph sends when a transcript is created
# Replace <USER_OID> with the actual user object ID from Azure AD
sample_user_id = "<USER_OID>"
sample_transcript_id = "MiMjSEVYX0lEX0hFUkU="

notification_payload = {
    "value": [
        {
            "subscriptionId": "00000000-0000-0000-0000-000000000000",
            "changeType": "created",
            "clientState": webhook_secret,
            "resource": f"users/{sample_user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{sample_user_id}')/{sample_transcript_id}",
            "resourceData": {
                "@odata.type": "#Microsoft.Graph.onlineMeetingTranscript",
                "@odata.id": f"users/{sample_user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{sample_user_id}')/{sample_transcript_id}",
                "id": sample_transcript_id
            },
            "tenantId": "<YOUR_TENANT_ID>",
            "sequenceNumber": 1,
            "lifecycleEvent": "missed"
        }
    ]
}

print(f"\n📨 Sending test notification...")
print(f"   Payload size: {len(json.dumps(notification_payload))} bytes")

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {webhook_secret}'
}

try:
    response = requests.post(
        webhook_url,
        json=notification_payload,
        headers=headers,
        timeout=10
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    
    if response.status_code in [200, 202]:
        print(f"\n✅ SUCCESS! Webhook accepted")
        print(f"   The Lambda function should process this notification")
        print(f"\n📍 Check S3 bucket for new webhook payload within 5 seconds:")
        print(f"   s3://tmf-webhook-payloads-dev/webhooks/")
        print(f"\n🔍 Run this to see latest S3 files:")
        print(f"   aws s3 ls s3://tmf-webhook-payloads-dev/webhooks/ --profile tmf-dev --recursive | tail -5")
    else:
        print(f"\n❌ Request failed")
        try:
            error_text = response.json()
            print(f"   Error: {error_text}")
        except:
            print(f"   Response: {response.text}")
            
except requests.exceptions.Timeout:
    print(f"\n⏳ Request timed out - webhook may still be processing")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)
print("\nℹ️  NEXT STEPS:")
print("   1. Check AWS Lambda logs:")
print("      aws logs tail /aws/lambda/tmf-webhook-writer-dev --follow --profile tmf-dev")
print("\n   2. Check S3 for the webhook payload:")
print("      aws s3 ls s3://tmf-webhook-payloads-dev/webhooks/ --profile tmf-dev --recursive | tail -10")
print("\n   3. If successful, the Lambda will have stored the notification in S3")
print("=" * 80)
