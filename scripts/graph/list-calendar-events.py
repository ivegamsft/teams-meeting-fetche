#!/usr/bin/env python3
"""
Query calendar events from Graph API to verify they exist.
"""
import sys
import requests
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers


def list_calendar_events():
    """List recent calendar events for the user."""
    headers = get_graph_headers()
    
    # Get events from today
    start = datetime.now(timezone.utc).date()
    filter_query = f"start/dateTime ge '{start.isoformat()}T00:00:00Z'"
    
    print("📅 Querying calendar events from Graph API...")
    print(f"   User: boldoriole@ibuyspy.net")
    print(f"   Filter: Events starting from {start}")
    print()
    
    response = requests.get(
        'https://graph.microsoft.com/v1.0/users/boldoriole@ibuyspy.net/events',
        headers=headers,
        params={
            '$filter': filter_query,
            '$top': 10,
            '$select': 'id,subject,start,end,createdDateTime,lastModifiedDateTime',
            '$orderby': 'createdDateTime desc'
        },
        timeout=30
    )
    
    if response.status_code == 200:
        events = response.json().get('value', [])
        print(f'✅ Found {len(events)} events in calendar\n')
        
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['subject']}")
            print(f"   ID: {event['id'][:60]}...")
            print(f"   Start: {event['start']['dateTime']}")
            print(f"   Created: {event['createdDateTime']}")
            print(f"   Last Modified: {event['lastModifiedDateTime']}")
            print()
        
        return events
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None


if __name__ == "__main__":
    list_calendar_events()
