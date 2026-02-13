#!/usr/bin/env python3
"""
Recreate transcript subscription to force fresh webhook delivery
"""
import requests
import sys
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

headers = get_graph_headers()
user_email = "boldoriole@ibuyspy.net"

# Delete the old subscription
print("🗑️  Deleting old subscription...")
old_sub_id = "9a3cb044-d749-4768-aed4-17caf5a3b427"
del_resp = requests.delete(
    f"https://graph.microsoft.com/v1.0/subscriptions/{old_sub_id}",
    headers=headers,
    timeout=10
)

if del_resp.status_code == 204:
    print("✅ Deleted")
else:
    print(f"❌ Delete failed: {del_resp.status_code}")

# Get user ID
print("\n👤 Getting user ID...")
user_resp = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_email}", headers=headers, timeout=10)
user_id = user_resp.json()["id"]
print(f"✅ User: {user_id}")

# Create new subscription
print("\n📝 Creating new subscription...")
expiration = datetime.now(timezone.utc) + timedelta(hours=1)
webhook_url = "https://h0m58vi4y5.execute-api.us-east-1.amazonaws.com/dev/bot/callbacks"

subscription_data = {
    "changeType": "created",
    "notificationUrl": webhook_url,
    "resource": f"users/{user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{user_id}')",
    "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
    "clientState": "tmf-bot-webhook-v2",
}

print(f"Webhook URL: {webhook_url}")

response = requests.post(
    "https://graph.microsoft.com/v1.0/subscriptions",
    headers=headers,
    json=subscription_data,
    timeout=30,
)

if response.status_code == 201:
    result = response.json()
    print(f"✅ New subscription created")
    print(f"   ID: {result['id']}")
    print(f"   Expires: {result['expirationDateTime']}")
    print(f"\n🎯 Webhook ready to receive transcript notifications")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text[:300])
