#!/usr/bin/env python3
"""
Show all active subscriptions and their webhook URLs
"""
import sys
import requests
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

headers = get_graph_headers()

# Get all subscriptions
resp = requests.get('https://graph.microsoft.com/v1.0/subscriptions', headers=headers, timeout=10)

if resp.status_code != 200:
    print(f"❌ Failed to get subscriptions: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

subs = resp.json().get('value', [])

print('📋 All Active Subscriptions:')
print('=' * 120)

for i, sub in enumerate(subs, 1):
    print(f"\n[{i}] ID: {sub['id']}")
    print(f"    Resource: {sub['resource']}")
    print(f"    Webhook: {sub['notificationUrl']}")
    print(f"    ChangeType: {sub['changeType']}")
    print(f"    Expires: {sub['expirationDateTime']}")
    
    # Check if it's the transcript subscription
    if 'getAllTranscripts' in sub['resource']:
        print(f"    ⬅️  THIS IS THE TRANSCRIPT SUBSCRIPTION")

print(f"\n✅ Total: {len(subs)} subscription(s)")

# Now check if webhook URLs are accessible
print("\n" + "=" * 120)
print("🔍 Testing webhook URL accessibility:")
print("=" * 120)

for sub in subs:
    if 'getAllTranscripts' in sub['resource']:
        url = sub['notificationUrl']
        print(f"\n📤 GET {url}")
        try:
            test_resp = requests.get(url, timeout=5)
            print(f"   Response: {test_resp.status_code}")
        except Exception as e:
            print(f"   Error: {str(e)[:100]}")
