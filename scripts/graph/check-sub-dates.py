#!/usr/bin/env python3
import requests
import sys
sys.path.append('scripts/graph')
from auth_helper import get_graph_headers

headers = get_graph_headers()
resp = requests.get('https://graph.microsoft.com/beta/subscriptions', headers=headers)
subs = resp.json().get('value', [])

for sub in subs:
    print(f"ID: {sub['id']}")
    print(f"  Resource: {sub['resource']}")
    print(f"  Created: {sub.get('createdDateTime', 'N/A')}")
    print(f"  Expires: {sub['expirationDateTime']}")
    print(f"  NotificationUrl: {sub['notificationUrl'][:60]}...")
    print()
