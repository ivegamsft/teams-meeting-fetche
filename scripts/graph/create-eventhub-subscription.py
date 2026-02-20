#!/usr/bin/env python3
"""
Create Microsoft Graph subscription with Event Hub delivery (RBAC authentication).

This script creates a change notification subscription that delivers to Azure Event Hub
using RBAC (Role-Based Access Control) authentication instead of SAS keys.

Requirements:
- The Azure AD application (GRAPH_CLIENT_ID) must have "Azure Event Hubs Data Sender" role
  on the Event Hub namespace for Graph API to deliver notifications
- Event Hub notification URL format: EventHub:https://<namespace>.servicebus.windows.net/<eventhub-name>?tenantId=<guid>
- Tenant ID MUST be a GUID, not a domain name

Usage:
    python scripts/graph/create-eventhub-subscription.py --resource "/users/user@domain.com/events"
    python scripts/graph/create-eventhub-subscription.py --resource "/groups/{group-id}" --expiration-hours 72
"""
import sys
import argparse
from datetime import datetime, timedelta, timezone
import requests

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config


def create_eventhub_subscription(resource, expiration_hours=48, change_type="created,updated"):
    """
    Create Graph subscription with Event Hub delivery using RBAC.
    
    Args:
        resource: Graph resource to monitor (e.g., "/users/{id}/events" or "/groups/{id}/calendar/events")
        expiration_hours: Subscription duration in hours (default: 48)
        change_type: Comma-separated change types: created, updated, deleted (default: "created,updated")
    
    Returns:
        dict: Created subscription details from Graph API
    """
    config = get_config()
    tenant_id = config.get("tenant_id")
    
    # Get Event Hub settings from environment
    import os
    from dotenv import load_dotenv
    load_dotenv('.env.local.azure')
    load_dotenv('nobots-eventhub/.env')
    
    eh_namespace = os.getenv('EVENT_HUB_NAMESPACE')
    eh_name = os.getenv('EVENT_HUB_NAME')
    
    if not all([tenant_id, eh_namespace, eh_name]):
        raise ValueError(
            "Missing required environment variables:\n"
            "- GRAPH_TENANT_ID (for tenant GUID)\n"
            "- EVENT_HUB_NAMESPACE\n"
            "- EVENT_HUB_NAME\n"
        )
    
    # For Event Hub notifications, tenantId can be DOMAIN NAME or GUID
    # Microsoft Learn docs say domain, but test with GUID if GRAPH_TENANT_DOMAIN_GUID is set
    use_guid = os.getenv('GRAPH_TENANT_DOMAIN_GUID') == 'true'
    
    if use_guid:
        tenant_domain = tenant_id  # use the GUID from config
    else:
        # Extract domain from tenant_id if it contains a domain, otherwise derive from config
        if '@' in tenant_id:
            # If tenant_id looks like a domain, use it
            tenant_domain = tenant_id
        elif '.' in tenant_id:
            # If it's a domain-like format
            tenant_domain = tenant_id
        else:
            # If it's a GUID, we need the domain
            # Try to get from environment or derive from graph app email
            tenant_domain = os.getenv('GRAPH_TENANT_DOMAIN')
            if not tenant_domain:
                # Fallback
                raise ValueError(
                    "Cannot determine tenant domain. Set GRAPH_TENANT_DOMAIN environment variable."
                )
    
    # Build Event Hub notification URL with RBAC using DOMAIN NAME for tenantId
    # Format: EventHub:https://<namespace>.servicebus.windows.net/eventhubname/<eventhub-name>?tenantId=<domain>
    notification_url = f"EventHub:https://{eh_namespace}/eventhubname/{eh_name}?tenantId={tenant_domain}"
    
    headers = get_graph_headers()
    expiration = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
    
    subscription_data = {
        "changeType": change_type,
        "notificationUrl": notification_url,
        "resource": resource,
        "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        # Client state not needed for Event Hub delivery
    }
    
    print("📝 Creating Event Hub subscription (RBAC authentication)...")
    print(f"   Resource: {resource}")
    print(f"   Change Type: {change_type}")
    print(f"   Event Hub: {eh_namespace}/{eh_name}")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Notification URL: {notification_url}")
    print(f"   Expires: {subscription_data['expirationDateTime']}")
    print()
    print("⚠️  IMPORTANT: The app must have 'Azure Event Hubs Data Sender' role")
    print(f"   assigned on Event Hub namespace '{eh_namespace}'")
    print()
    
    response = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=subscription_data,
        timeout=30,
    )
    
    if response.status_code == 201:
        result = response.json()
        print("✅ Subscription created successfully!")
        print(f"   ID: {result['id']}")
        print(f"   Resource: {result['resource']}")
        print(f"   Change Type: {result['changeType']}")
        print(f"   Notification URL: {result['notificationUrl']}")
        print(f"   Expires: {result['expirationDateTime']}")
        print()
        print("📋 Save subscription ID for renewal:")
        print(f"   {result['id']}")
        return result
    else:
        print("❌ Failed to create subscription!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        print()
        
        if response.status_code == 400:
            print("💡 Common issues:")
            print("   1. App doesn't have 'Azure Event Hubs Data Sender' role on the namespace")
            print("   2. Event Hub namespace or name is incorrect")
            print("   3. Tenant ID is not a GUID")
            print("   4. Resource path is invalid")
        
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Create Microsoft Graph subscription with Event Hub delivery (RBAC)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor user's calendar events
  python scripts/graph/create-eventhub-subscription.py --resource "/users/user@domain.com/events"
  
  # Monitor group calendar with 72-hour expiration
  python scripts/graph/create-eventhub-subscription.py \\
    --resource "/groups/12345678-1234-1234-1234-123456789abc/calendar/events" \\
    --expiration-hours 72
  
  # Monitor only created events
  python scripts/graph/create-eventhub-subscription.py \\
    --resource "/users/user@domain.com/events" \\
    --change-type "created"
"""
    )
    
    parser.add_argument(
        "--resource",
        required=True,
        help="Graph resource to monitor (e.g., '/users/{id}/events' or '/groups/{id}/calendar/events')"
    )
    parser.add_argument(
        "--expiration-hours",
        type=int,
        default=48,
        help="Subscription duration in hours (default: 48, max: depends on resource type)"
    )
    parser.add_argument(
        "--change-type",
        default="created,updated",
        help="Comma-separated change types: created, updated, deleted (default: 'created,updated')"
    )
    
    args = parser.parse_args()
    
    result = create_eventhub_subscription(
        resource=args.resource,
        expiration_hours=args.expiration_hours,
        change_type=args.change_type
    )
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
