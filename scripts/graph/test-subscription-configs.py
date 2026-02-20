#!/usr/bin/env python3
"""
Test different subscription parameters for Event Hub delivery
"""
import sys
import json
from datetime import datetime, timedelta, timezone
import requests
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config
import os
from dotenv import load_dotenv

load_dotenv('.env.local.azure')
load_dotenv('nobots-eventhub/.env')

config = get_config()
tenant_id = config.get("tenant_id")
eh_namespace = os.getenv('EVENT_HUB_NAMESPACE')
eh_name = os.getenv('EVENT_HUB_NAME')

# Build Event Hub notification URL
notification_url = f"EventHub:https://{eh_namespace}/eventhubname/{eh_name}?tenantId={tenant_id}"

headers = get_graph_headers()

# Test with includeResourceData: true
test_configs = [
    {
        "name": "With includeResourceData",
        "resource": "/users/boldoriole@ibuyspy.net/events",
        "changeType": "created,updated,deleted",
        "includeResourceData": True,
        "notificationUrl": notification_url,
        "expirationDateTime": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
    },
    {
        "name": "User calendar (alternative path)",
        "resource": "/users/boldoriole@ibuyspy.net/calendar/events",
        "changeType": "created,updated,deleted",
        "notificationUrl": notification_url,
        "expirationDateTime": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
    }
]

print("🧪 Testing Event Hub Subscription Configurations")
print("=" * 80)

for test in test_configs:
    print(f"\n▶ {test['name']}")
    print(f"   Payload: {json.dumps(test, indent=2)}")
    
    resp = requests.post(
        'https://graph.microsoft.com/v1.0/subscriptions',
        headers=headers,
        json=test,
        timeout=10
    )
    
    print(f"   Status: {resp.status_code}")
    if resp.status_code >= 201:
        result = resp.json()
        print(f"   Subscription ID: {result.get('id')}")
        print(f"   Resource: {result.get('resource')}")
        print(f"   ✅ Created successfully")
        # Don't delete - keep for testing
    else:
        print(f"   ❌ Failed:")
        print(f"   {json.dumps(resp.json(), indent=3)}")
