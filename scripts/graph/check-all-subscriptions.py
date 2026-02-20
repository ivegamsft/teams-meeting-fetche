#!/usr/bin/env python3
"""
Check status of both subscriptions
"""
import sys
import json
import requests
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

subscription_ids = {
    "HTTP Webhook": "918fd295-8d0e-4a6e-9c2d-21e7d2f374ce",
    "Event Hub /events": "353c8f0f-20f3-4289-a3b5-f18a3f77b5ce", 
    "Event Hub /calendar/events": "8d40a5fb-e2ff-4b6d-9350-015dbe292666"
}

headers = get_graph_headers()

print("📋 Subscription Status Check")
print("=" * 80)

for name, sub_id in subscription_ids.items():
    print(f"\n{name} ({sub_id}):")
    
    resp = requests.get(
        f'https://graph.microsoft.com/beta/subscriptions/{sub_id}',
        headers=headers,
        timeout=10
    )
    
    if resp.status_code != 200:
        print(f"   ❌ Not found or error")
        continue
    
    sub = resp.json()
    print(f"   Resource: {sub.get('resource')}")
    print(f"   Created: {sub.get('createdDateTime', 'N/A')}")
    print(f"   Expires: {sub.get('expirationDateTime')}")
    print(f"   Status Code: {sub.get('latestStatusCode', 'N/A')}")
    print(f"   Failure Reason: {sub.get('latestFailureReason', 'None')}")
