#!/usr/bin/env python3
import requests
import sys
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

subscription_id = "510c629b-4d99-46be-afbc-60332898bd54"

headers = get_graph_headers()

resp = requests.get(
    f'https://graph.microsoft.com/beta/subscriptions/{subscription_id}',
    headers=headers,
    timeout=10
)

if resp.status_code != 200:
    print(f"❌ Error: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

sub = resp.json()

print(f"Subscription: {sub['id']}")
print(f"  Resource: {sub['resource']}")
print(f"  NotificationURL: {sub['notificationUrl']}")
print(f"  Status: {sub.get('latestStatusCode', 'N/A')}")
print(f"  Failure: {sub.get('latestFailureReason', 'None')}")
print(f"  Content Type: {sub.get('notificationContentType', 'N/A')}")
