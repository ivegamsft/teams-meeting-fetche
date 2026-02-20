#!/usr/bin/env python3
"""
List current subscriptions and create Event Hub subscription for group calendar
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta

def run_command(cmd):
    """Run Azure CLI command"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=" * 70)
    print("Event Hub Subscription Setup for Group Calendar")
    print("=" * 70)
    print()
    
    groupId = "5e7708f8-b0d2-467d-97f9-d9da4818084a"
    ehNamespace = "tmf-ehns-eus-6an5wk"
    ehName = "tmf-eh-eus-6an5wk"
    
    print(f"Group ID: {groupId}")
    print(f"Event Hub: {ehNamespace}.servicebus.windows.net/{ehName}")
    print()
    
    # Get access token
    print("Getting access token...")
    token_cmd = "az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv"
    accessToken = run_command(token_cmd)
    if not accessToken:
        print("Failed to get access token")
        return 1
    
    print("✅ Got access token")
    print()
    
    # List current subscriptions
    print("Listing current subscriptions...")
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {accessToken}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)
        subscriptions = response.json().get("value", [])
        
        if subscriptions:
            print(f"Found {len(subscriptions)} subscription(s):")
            print()
            for sub in subscriptions:
                print(f"  ID: {sub['id']}")
                print(f"   Resource: {sub['resource']}")
                print(f"    State: {sub['state']}")
                print(f"    Notification: {sub['notificationUrl']}")
                print(f"    Expires: {sub['expirationDateTime']}")
                print()
        else:
            print("No subscriptions found")
            print()
        
        # Check if group calendar subscription already exists
        group_cal_sub = [s for s in subscriptions if f"groups/{groupId}/calendar/events" in s['resource']]
        if group_cal_sub:
            print(f"✅ Group calendar subscription already exists: {group_cal_sub[0]['id']}")
            return 0
        
    except Exception as e:
        print(f"Error listing subscriptions: {e}")
    
    # Create subscription
    print("Creating Event Hub subscription for group calendar...")
    
    notificationUrl = f"EventHub:https://{ehNamespace}.servicebus.windows.net/{ehName}"
    expiration = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    
    payload = {
        "changeType": "created,updated,deleted",
        "notificationUrl": notificationUrl,
        "resource": f"groups/{groupId}/calendar/events",
        "expirationDateTime": expiration
    }
    
    try:
        response = requests.post(
            "https://graph.microsoft.com/v1.0/subscriptions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 201:
            sub_data = response.json()
            print("✅ Subscription created!")
            print()
            print(f"  ID: {sub_data['id']}")
            print(f"  Resource: {sub_data['resource']}")
            print(f"  State: {sub_data['state']}")
            print(f"  Expires: {sub_data['expirationDateTime']}")
            return 0
        elif response.status_code == 409 or "already exists" in response.text:
            print("⚠️  Subscription already exists for this resource")
            return 0
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
