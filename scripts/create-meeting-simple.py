#!/usr/bin/env python3
"""
Create Teams meeting on organizer's calendar with trustingboar as attendee
"""

import subprocess
import json
from datetime import datetime, timedelta

def run_cli_command(method, url, body):
    """Run Azure CLI rest command"""
    # Escape JSON for PowerShell
    escaped_body = json.dumps(body).replace('"', '\\"')
    
    cmd = f'az rest --method {method} --url "{url}" --headers "Content-Type=application/json" --body "{escaped_body}"'
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    return result.stdout.strip()

def main():
    print("=" * 70)
    print("Creating Teams Meeting for Event Hub Testing")
    print("=" * 70)
    print()
    
    # Meeting details
    subject = "Test Meeting with Transcript - Event Hub Test"
    start_dt = datetime.utcnow() + timedelta(minutes=5)
    end_dt = start_dt + timedelta(hours=1)
    
    start_time = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Build payload
    payload = {
        "subject": subject,
        "start": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "UTC"
        },
        "attendees": [
            {
                "emailAddress": {
                    "address": "trustingboar@ibuyspy.net",
                    "name": "TMF Trustingboar"
                },
                "type": "required"
            }
        ],
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }
    
    print(f"📅 Meeting Details:")
    print(f"   Subject: {subject}")
    print(f"   Start: {start_time} UTC (in ~5 minutes)")
    print(f"   Duration: 60 minutes")
    print(f"   Attendee: trustingboar@ibuyspy.net")
    print()
    print("Creating meeting...")
    print()
    
    # Create meeting
    result = run_cli_command("post", "https://graph.microsoft.com/v1.0/me/events", payload)
    
    if not result:
        print("❌ Failed to create meeting")
        return 1
    
    try:
        meeting = json.loads(result)
        
        print("✅ Meeting created successfully!")
        print()
        print("Event Details:")
        print(f"  Event ID: {meeting['id']}")
        print(f"  Subject: {meeting['subject']}")
        print(f"  Join URL: {meeting.get('onlineMeetingUrl', 'N/A')}")
        print(f"  Start: {meeting['start']['dateTime']} UTC")
        print()
        print("=" * 70)
        print("📝 NEXT: Join the meeting!")
        print("=" * 70)
        print()
        print("When you join the meeting, Graph will send a change notification")
        print("to Event Hub, which will be processed by Lambda and stored in DynamoDB.")
        print()
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        print(f"Response: {result[:200]}...")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
