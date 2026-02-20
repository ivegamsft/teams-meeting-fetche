#!/usr/bin/env python3
"""
Create Event Hub subscription for GROUP calendar events with RBAC
"""
import sys
import argparse
from datetime import datetime, timedelta, timezone
import requests
import os
from dotenv import load_dotenv

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config

load_dotenv('.env.local.azure')
load_dotenv('nobots-eventhub/.env')

def create_group_eventhub_subscription(group_id, expiration_hours=48, change_type="created,updated"):
    """
    Create Event Hub subscription for group calendar events with RBAC.
    
    Args:
        group_id: Azure AD group ID
        expiration_hours: Subscription duration in hours
        change_type: Comma-separated change types
    """
    config = get_config()
    tenant_id = config.get("tenant_id")
    
    eh_namespace = os.getenv('EVENT_HUB_NAMESPACE')
    eh_name = os.getenv('EVENT_HUB_NAME')
    
    if not all([tenant_id, eh_namespace, eh_name]):
        raise ValueError("Missing EVENT_HUB_NAMESPACE or EVENT_HUB_NAME")
    
    # Get tenant domain
    use_guid = os.getenv('GRAPH_TENANT_DOMAIN_GUID') == 'true'
    
    if use_guid:
        tenant_domain = tenant_id
    else:
        tenant_domain = os.getenv('GRAPH_TENANT_DOMAIN')
        if not tenant_domain:
            raise ValueError("Set GRAPH_TENANT_DOMAIN environment variable")
    
    # Build Event Hub notification URL
    notification_url = f"EventHub:https://{eh_namespace}/eventhubname/{eh_name}?tenantId={tenant_domain}"
    
    headers = get_graph_headers()
    expiration = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
    
    # GROUP-BASED SUBSCRIPTION - monitor group calendar
    resource = f"/groups/{group_id}/calendar/events"
    
    subscription_data = {
        "changeType": change_type,
        "notificationUrl": notification_url,
        "resource": resource,
        "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
    }
    
    print("📝 Creating Group-based Event Hub subscription...")
    print(f"   Group ID: {group_id}")
    print(f"   Resource: {resource}")
    print(f"   Change Type: {change_type}")
    print(f"   Event Hub: {eh_namespace}/{eh_name}")
    print(f"   Tenant Domain: {tenant_domain}")
    print(f"   Notification URL: {notification_url}")
    print(f"   Expires: {subscription_data['expirationDateTime']}")
    print()
    
    response = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=subscription_data,
        timeout=30,
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    
    print("✅ Subscription created successfully!")
    print(f"   ID: {result['id']}")
    print(f"   Resource: {result['resource']}")
    print(f"   Expires: {result['expirationDateTime']}")
    print()
    print(f"📋 Save subscription ID: {result['id']}")
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create group-based Event Hub subscription")
    parser.add_argument("--group-id", required=True, help="Group ID to monitor")
    parser.add_argument("--expiration-hours", type=int, default=48, help="Subscription duration in hours")
    parser.add_argument("--change-type", default="created,updated", help="Change types to monitor")
    
    args = parser.parse_args()
    
    result = create_group_eventhub_subscription(
        group_id=args.group_id,
        expiration_hours=args.expiration_hours,
        change_type=args.change_type
    )
    
    if not result:
        sys.exit(1)
