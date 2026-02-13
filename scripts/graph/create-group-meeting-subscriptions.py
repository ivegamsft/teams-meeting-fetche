#!/usr/bin/env python3
"""
Create tenant-wide meeting event subscriptions filtered by group.
This will capture meeting creation/updates for the Monitored Meetings group.
"""
import requests
import sys
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config

config = get_config()
headers = get_graph_headers()

# Bot webhook URL
webhook_url = "https://h0m58vi4y5.execute-api.us-east-1.amazonaws.com/dev/bot/callbacks"
group_id = config.get("group_id")  # Monitored Meetings group

if not group_id:
    print("❌ group_id not found in config")
    sys.exit(1)

print(f"📝 Creating tenant-wide meeting subscriptions")
print(f"   Group ID: {group_id}")
print(f"   Webhook: {webhook_url}\n")

# Subscription 1: Group events (meeting creation/updates)
subs_to_create = [
    {
        "name": "Group Events (Meetings)",
        "changeType": "created,updated,deleted",
        "resource": f"groups/{group_id}/events",
        "notificationUrl": webhook_url,
    },
    {
        "name": "Group Conversations (Meeting Chats)",
        "changeType": "created,updated",
        "resource": f"groups/{group_id}/conversations",
        "notificationUrl": webhook_url,
    },
]

expiration = datetime.now(timezone.utc) + timedelta(hours=1)

for sub_config in subs_to_create:
    print(f"🔗 Creating: {sub_config['name']}")
    print(f"   Resource: {sub_config['resource']}")
    
    subscription_data = {
        "changeType": sub_config["changeType"],
        "notificationUrl": webhook_url,
        "resource": sub_config["resource"],
        "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        "clientState": "tmf-bot-meeting-hook",
    }
    
    response = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=subscription_data,
        timeout=30,
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"   ✅ Created! ID: {result['id']}")
    else:
        error_msg = response.json().get("error", {}).get("message", "Unknown error")
        print(f"   ❌ Failed: {response.status_code} - {error_msg[:100]}")
    print()

print("\n✅ Subscriptions setup complete!")
print("\n📊 These subscriptions will now:")
print("   - Monitor meeting creation/updates in the Monitored Meetings group")
print("   - Send webhooks to bot API when meetings are created/updated")
print("   - Include meeting metadata for the bot to process")
