#!/usr/bin/env python3
"""
Test meeting-bot API with manual webhook payload.
"""
import sys
import json
import requests
from datetime import datetime

sys.path.append("scripts/graph")
from auth_helper import get_config


def test_bot_webhook(webhook_url):
    config = get_config()
    webhook_secret = config.get("webhook_secret", "")[:255]

    test_payload = {
        "value": [
            {
                "subscriptionId": "test-123",
                "changeType": "created",
                "clientState": webhook_secret,
                "resource": "communications/onlineMeetings",
                "resourceData": {
                    "id": "test-meeting-id",
                },
                "tenantId": "test-tenant",
                "sequenceNumber": 1,
                "lifecycleEvent": "missed",
            }
        ]
    }

    print(f"🧪 Testing meeting-bot webhook endpoint...")
    print(f"   URL: {webhook_url}")
    print(f"   Payload: test notification")

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            webhook_url, json=test_payload, headers=headers, timeout=10
        )

        print(f"\n✅ Response Status: {response.status_code}")
        if response.status_code in (200, 202):
            print(f"   ✅ Webhook accepted")
            try:
                body = response.json()
                print(f"   Response: {json.dumps(body, indent=2)[:200]}")
            except:
                print(f"   Response: {response.text[:200]}")
        else:
            print(f"   ❌ Error response")
            print(f"   Body: {response.text[:300]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    config = get_config()
    bot_url = config.get("bot_meeting_started_url")

    if not bot_url:
        print("❌ BOT_MEETING_STARTED_URL not set in env")
        sys.exit(1)

    test_bot_webhook(bot_url)
