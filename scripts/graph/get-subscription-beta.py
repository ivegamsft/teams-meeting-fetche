#!/usr/bin/env python3
"""
Get subscription status using beta API
"""
import sys
import json
import requests
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

subscription_id = "353c8f0f-20f3-4289-a3b5-f18a3f77b5ce"

headers = get_graph_headers()

# Try beta endpoint for more details
resp = requests.get(
    f'https://graph.microsoft.com/beta/subscriptions/{subscription_id}',
    headers=headers,
    timeout=10
)

if resp.status_code != 200:
    print(f"❌ Failed: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

subscription = resp.json()

print("📋 Event Hub Subscription Details (Beta):")
print("=" * 80)

# Print key fields
print(f"ID: {subscription.get('id')}")
print(f"Resource: {subscription.get('resource')}")
print(f"NotificationURL: {subscription.get('notificationUrl')}")
print(f"Status: {subscription.get('latestStatusCode', 'N/A')}")
print(f"Failure Reason: {subscription.get('latestFailureReason', 'N/A')}")
print(f"Created: {subscription.get('createdDateTime', 'N/A')}")
print(f"Expires: {subscription.get('expirationDateTime')}")
print(f"\nFull response:")
print(json.dumps(subscription, indent=2, default=str))
