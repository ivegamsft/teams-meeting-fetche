#!/usr/bin/env python3
"""
Get detailed subscription information including all fields
"""
import sys
import json
import requests
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

subscription_id = "353c8f0f-20f3-4289-a3b5-f18a3f77b5ce"

headers = get_graph_headers()

resp = requests.get(
    f'https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}',
    headers=headers,
    timeout=10
)

if resp.status_code != 200:
    print(f"❌ Failed to get subscription: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

subscription = resp.json()

print("📋 Event Hub Subscription Details:")
print("=" * 80)
print(json.dumps(subscription, indent=2))
