#!/usr/bin/env python3
"""
Create a test calendar event to trigger Event Hub notifications.
"""
import sys
import requests
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers


def create_test_event():
    """Create a test online meeting event."""
    headers = get_graph_headers()
    
    # Create a test meeting 30 minutes from now
    start = datetime.now(timezone.utc) + timedelta(minutes=30)
    end = start + timedelta(hours=1)
    
    event = {
        'subject': 'Test Event Hub Notification',
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'UTC'
        },
        'isOnlineMeeting': True,
        'onlineMeetingProvider': 'teamsForBusiness'
    }
    
    print("📅 Creating test calendar event...")
    print(f"   Subject: {event['subject']}")
    print(f"   Start: {start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    response = requests.post(
        'https://graph.microsoft.com/v1.0/users/boldoriole@ibuyspy.net/events',
        headers=headers,
        json=event,
        timeout=30
    )
    
    if response.status_code == 201:
        result = response.json()
        print("✅ Event created successfully!")
        print(f"   Event ID: {result['id']}")
        print(f"   Subject: {result['subject']}")
        print(f"   Start: {result['start']['dateTime']}")
        if 'onlineMeeting' in result:
            print(f"   Join URL: {result['onlineMeeting']['joinUrl'][:60]}...")
        print()
        print("💡 Check Lambda logs in ~10 seconds to see Event Hub notification")
        return result
    else:
        print(f"❌ Failed to create event: {response.status_code}")
        print(response.text)
        return None


if __name__ == "__main__":
    create_test_event()
