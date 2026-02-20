#!/usr/bin/env python3
"""
Delete Microsoft Graph subscriptions by ID or filter.

Usage:
    # Delete specific subscription
    python scripts/graph/delete-subscription.py --id "abc123-def456"
    
    # Delete all Event Hub subscriptions
    python scripts/graph/delete-subscription.py --filter-eventhub
    
    # Delete HTTP webhook subscriptions
    python scripts/graph/delete-subscription.py --filter-webhook
    
    # Delete all subscriptions (use with caution!)
    python scripts/graph/delete-subscription.py --all --confirm
"""
import sys
import argparse
import requests

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers


def list_subscriptions():
    """List all active subscriptions."""
    headers = get_graph_headers()
    response = requests.get(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        print(f"❌ Failed to list subscriptions: {response.status_code}")
        print(response.text)
        return []


def delete_subscription(subscription_id):
    """Delete a specific subscription by ID."""
    headers = get_graph_headers()
    response = requests.delete(
        f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 204:
        return True
    else:
        print(f"❌ Failed to delete subscription {subscription_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Delete Microsoft Graph subscriptions")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="Subscription ID to delete")
    group.add_argument("--filter-eventhub", action="store_true",
                      help="Delete all Event Hub subscriptions")
    group.add_argument("--filter-webhook", action="store_true",
                      help="Delete all HTTP webhook subscriptions")
    group.add_argument("--all", action="store_true",
                      help="Delete ALL subscriptions (requires --confirm)")
    
    parser.add_argument("--confirm", action="store_true",
                       help="Confirm deletion (required for --all)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be deleted without actually deleting")
    
    args = parser.parse_args()
    
    # Single subscription deletion
    if args.id:
        if args.dry_run:
            print(f"[DRY RUN] Would delete subscription: {args.id}")
            return
        
        print(f"Deleting subscription: {args.id}")
        if delete_subscription(args.id):
            print(f"✅ Deleted subscription: {args.id}")
        else:
            sys.exit(1)
        return
    
    # Bulk deletion - list subscriptions first
    print("📋 Listing all subscriptions...")
    subscriptions = list_subscriptions()
    
    if not subscriptions:
        print("No subscriptions found.")
        return
    
    # Filter subscriptions
    to_delete = []
    
    if args.filter_eventhub:
        to_delete = [s for s in subscriptions if s.get("notificationUrl", "").startswith("EventHub:")]
        print(f"\n🎯 Found {len(to_delete)} Event Hub subscriptions")
    elif args.filter_webhook:
        to_delete = [s for s in subscriptions if s.get("notificationUrl", "").startswith("https://")]
        print(f"\n🎯 Found {len(to_delete)} HTTP webhook subscriptions")
    elif args.all:
        if not args.confirm:
            print("\n❌ --all requires --confirm flag for safety")
            print(f"   Found {len(subscriptions)} total subscriptions")
            sys.exit(1)
        to_delete = subscriptions
        print(f"\n⚠️  Deleting ALL {len(to_delete)} subscriptions")
    
    if not to_delete:
        print("No subscriptions match the filter.")
        return
    
    # Show what will be deleted
    print("\nSubscriptions to delete:")
    for sub in to_delete:
        print(f"  • {sub['id']}")
        print(f"    Resource: {sub.get('resource', 'N/A')}")
        print(f"    Notification URL: {sub.get('notificationUrl', 'N/A')[:80]}")
        print()
    
    if args.dry_run:
        print(f"[DRY RUN] Would delete {len(to_delete)} subscriptions")
        return
    
    # Confirm before deleting
    if not args.all and not args.confirm:  # Skip prompt if --confirm provided
        response = input(f"Delete {len(to_delete)} subscriptions? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
    
    # Delete subscriptions
    print(f"\nDeleting {len(to_delete)} subscriptions...")
    deleted = 0
    failed = 0
    
    for sub in to_delete:
        sub_id = sub['id']
        if delete_subscription(sub_id):
            deleted += 1
            print(f"  ✅ Deleted: {sub_id}")
        else:
            failed += 1
            print(f"  ❌ Failed: {sub_id}")
    
    print(f"\n📊 Summary:")
    print(f"   Deleted: {deleted}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(to_delete)}")


if __name__ == "__main__":
    main()
