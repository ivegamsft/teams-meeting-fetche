#!/usr/bin/env python3
"""
Create transcript subscription pointing to the BOT API (not webhook writer)
"""
import sys
import requests
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config

config = get_config()
headers = get_graph_headers()
user_email = config.get('user_email', 'boldoriole@ibuyspy.net')

# Get user ID
print(f"👤 Getting user ID for {user_email}...")
user_resp = requests.get(f'https://graph.microsoft.com/v1.0/users/{user_email}', headers=headers, timeout=10)
user_id = user_resp.json()['id']
print(f"   ✅ User ID: {user_id}")

# Create subscription to transcripts pointing to BOT API
webhook_url = config.get('BOT_CALLBACKS_URL') or config.get('bot_callbacks_url')
if not webhook_url:
    print("❌ BOT_CALLBACKS_URL not configured")
    sys.exit(1)

client_state = config.get('webhook_secret', 'tmf-bot')[:255]
# For this resource type, Graph requires lifecycleNotificationUrl for expiry > 1 hour
# Use shorter expiry to avoid needing lifecycle URL
expiration = datetime.now(timezone.utc) + timedelta(hours=1)

subscription_data = {
    "changeType": "created",
    "notificationUrl": webhook_url,
    "resource": f"users/{user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{user_id}')",
    "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
    "clientState": client_state,
}

print(f"\n📝 Creating transcript subscription...")
print(f"   Resource: users/{user_id}/onlineMeetings/getAllTranscripts(...)")
print(f"   Webhook: {webhook_url}")

response = requests.post(
    "https://graph.microsoft.com/v1.0/subscriptions",
    headers=headers,
    json=subscription_data,
    timeout=30,
)

if response.status_code == 201:
    result = response.json()
    print(f"\n✅ Subscription created!")
    print(f"   ID: {result['id']}")
    print(f"   Expires: {result['expirationDateTime']}")
    print(f"\n🎯 Transcript notifications will now go to: {webhook_url}")
else:
    print(f"\n❌ Failed: {response.status_code}")
    print(response.text[:300])
    sys.exit(1)
