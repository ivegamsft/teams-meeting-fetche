#!/usr/bin/env python3
"""
Update transcript subscription to use direct Lambda Function URL
Eliminates API Gateway layer - simpler, more direct
"""
import requests
import sys
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

headers = get_graph_headers()
user_email = "boldoriole@ibuyspy.net"

# Direct Lambda Function URL (no API Gateway)
webhook_url = "https://deyehwh2y34qk6yrsfsrrri36m0syhsj.lambda-url.us-east-1.on.aws/"
sub_id = "801b3487-83eb-4f26-abb1-7e0570c7aa8e"

print("🔄 Updating subscription to use direct Lambda URL...")
print(f"   Subscription ID: {sub_id}")
print(f"   New webhook URL: {webhook_url}\n")

# Get user ID
user_resp = requests.get(f'https://graph.microsoft.com/v1.0/users/{user_email}', headers=headers, timeout=10)
user_id = user_resp.json()['id']

# Delete old subscription
print("🗑️  Deleting old subscription...")
del_resp = requests.delete(
    f'https://graph.microsoft.com/v1.0/subscriptions/{sub_id}',
    headers=headers,
    timeout=10
)

if del_resp.status_code == 204:
    print("✅ Deleted")
else:
    print(f"❌ Delete failed: {del_resp.status_code}")
    sys.exit(1)

# Create new subscription with Lambda URL
print("\n📝 Creating new subscription with Lambda Function URL...")
expiration = datetime.now(timezone.utc) + timedelta(hours=1)

subscription_data = {
    "changeType": "created",
    "notificationUrl": webhook_url,
    "resource": f"users/{user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{user_id}')",
    "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
    "clientState": "tmf-bot-lambda-direct",
}

response = requests.post(
    "https://graph.microsoft.com/v1.0/subscriptions",
    headers=headers,
    json=subscription_data,
    timeout=30,
)

if response.status_code == 201:
    result = response.json()
    print(f"✅ New subscription created!")
    print(f"   ID: {result['id']}")
    print(f"   Expires: {result['expirationDateTime']}")
    print(f"\n🎯 Graph will now send webhooks DIRECTLY to Lambda:")
    print(f"   {webhook_url}")
    print(f"\n✨ No API Gateway layer = simpler, faster, zero latency!")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
    sys.exit(1)
