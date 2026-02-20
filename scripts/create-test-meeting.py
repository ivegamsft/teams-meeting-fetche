#!/usr/bin/env python3
"""
Create a Teams meeting for trustingboar@ibuyspy.net
Uses Azure CLI for authentication (user's account)
"""

import subprocess
import json
from datetime import datetime, timedelta
import sys

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
    print("Create Teams Meeting - Using Azure CLI Authentication")
    print("=" * 70)
    print()
    
    # Get access token using Azure CLI (user's account)
    print("Getting access token...")
    token_cmd = "az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv"
    access_token = run_command(token_cmd)
    
    if not access_token:
        print("❌ Failed to get access token")
        return 1
    
    print("✅ Got access token")
    print()
    
    # Prepare meeting data
    user_email = "trustingboar@ibuyspy.net"
    subject = "Test Meeting with Transcript - Event Hub Test"
    start_time = (datetime.utcnow() + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    end_time = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    
    print(f"📅 Creating Teams meeting...")
    print(f"   Organizer: {user_email}")
    print(f"   Subject: {subject}")
    print(f"   Start: {start_time} UTC (in ~5 minutes)")
    print(f"   Duration: 60 minutes")
    print()
    
    # Create meeting using Azure CLI
    body = json.dumps({
        "subject": subject,
        "start": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "UTC"
        },
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    })
    
    # Escape for PowerShell
    escaped_body = body.replace('"', '\\"')
    
    create_cmd = (
        f'az rest --method post '
        f'--url "https://graph.microsoft.com/v1.0/users/{user_email}/events" '
        f'--headers "Content-Type=application/json" '
        f'--body "{escaped_body}"'
    )
    
    result = run_command(create_cmd)
    
    if not result:
        print("❌ Failed to create meeting")
        return 1
    
    try:
        meeting = json.loads(result)
        
        print("✅ Meeting created successfully!")
        print()
        print("Meeting Details:")
        print(f"  Event ID: {meeting['id']}")
        print(f"  Subject: {meeting['subject']}")
        print(f"  Start: {meeting['start']['dateTime']} UTC")
        print(f"  Join URL: {meeting.get('onlineMeetingUrl', 'N/A')}")
        print()
        print("=" * 70)
        print("📝 Next Steps:")
        print("=" * 70)
        print("1. Join the Teams meeting at the URL above")
        print("2. The meeting will trigger a Graph change notification")
        print("3. Notification will be sent to Event Hub")
        print("4. Lambda will receive and process it")
        print("5. Event will be stored in DynamoDB")
        print()
        print("⏱️  Check Event Hub metrics (30 sec - 1 min delay for notification)")
        print()
        
        return 0
        
    except json.JSONDecodeError:
        print("❌ Failed to parse meeting response")
        print(f"Response: {result}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
