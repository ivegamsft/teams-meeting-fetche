#!/usr/bin/env python3
"""
Create tenant-wide meeting-started webhook subscription for the bot API.
"""
import sys
from datetime import datetime, timedelta, timezone
import requests

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config


def create_meeting_started_subscription(expiration_hours=24):
    config = get_config()
    webhook_url = config.get("bot_meeting_started_url") or config.get("bot_callbacks_url")
    client_state = config.get("webhook_secret", "")[:255]

    if not webhook_url:
        raise ValueError(
            "Missing BOT_MEETING_STARTED_URL (preferred) or BOT_CALLBACKS_URL in env"
        )

    headers = get_graph_headers()
    expiration = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)

    subscription_data = {
        "changeType": "created",
        "notificationUrl": webhook_url,
        "resource": "communications/onlineMeetings",
        "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        "clientState": client_state,
    }

    print("📝 Creating meeting-started subscription...")
    print(f"   Resource: {subscription_data['resource']}")
    print(f"   Notification URL: {webhook_url}")

    response = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=subscription_data,
        timeout=30,
    )

    if response.status_code == 201:
        result = response.json()
        print("\n✅ Subscription created!")
        print(f"   ID: {result['id']}")
        print(f"   Resource: {result['resource']}")
        print(f"   Expires: {result['expirationDateTime']}")
        print("\n💾 Save to DynamoDB:")
        print("python scripts/aws/subscription-tracker.py save ")
        print(f'  --id "{result["id"]}" ')
        print(f'  --resource "{result["resource"]}" ')
        print(f'  --expiry "{result["expirationDateTime"]}" ')
        print('  --type "meeting-started"')
        return result

    print("\n❌ Failed to create subscription!")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
    return None


if __name__ == "__main__":
    create_meeting_started_subscription()
