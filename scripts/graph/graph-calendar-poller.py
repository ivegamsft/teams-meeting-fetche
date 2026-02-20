#!/usr/bin/env python3
"""
Poll Graph API directly for calendar changes instead of relying on change notifications.
This is more reliable than Event Hub or webhook delivery.

This function will:
1. Query the user's calendar events from the last poll
2. Compare with stored state to detect new/modified events
3. Send to Event Hub for processing
"""

import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import requests
import logging

load_dotenv('.env.local.azure')
load_dotenv('nobots-eventhub/.env')

logger = logging.getLogger(__name__)

class GraphCalendarPoller:
    def __init__(self):
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.user_id = "boldoriole@ibuyspy.net"
        # Load credentials from environment
        self.client_id = os.getenv('GRAPH_CLIENT_ID')
        self.client_secret = os.getenv('GRAPH_CLIENT_SECRET')
        self.tenant_id = os.getenv('GRAPH_TENANT_ID')
        self.access_token = None
        
    def get_access_token(self):
        """Get Microsoft Graph access token"""
        if self.access_token:
            return self.access_token
            
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(token_url, data=payload, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.text}")
            
        self.access_token = response.json()['access_token']
        return self.access_token
    
    def get_headers(self):
        """Get request headers with authorization"""
        return {
            'Authorization': f'Bearer {self.get_access_token()}',
            'Content-Type': 'application/json'
        }
    
    def get_calendar_events(self, minutes_back=60):
        """
        Get calendar events from the last N minutes
        
        Args:
            minutes_back: How many minutes to look back (default: 60)
            
        Returns:
            list: Calendar events
        """
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes_back)
        
        # Format for Graph API
        start_str = start_time.isoformat()
        end_str = end_time.isoformat()
        
        # Query events modified in the time range
        url = f"{self.graph_endpoint}/users/{self.user_id}/calendarview"
        
        params = {
            'startDateTime': start_str,
            'endDateTime': end_str,
            '$orderby': 'start/dateTime desc'
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to get calendar events: {response.status_code} - {response.text}")
            return []
        
        events = response.json().get('value', [])
        logger.info(f"✅ Found {len(events)} events in last {minutes_back} minutes")
        return events
    
    def get_recently_modified_events(self, minutes_back=60):
        """
        Get events that were MODIFIED in the last N minutes
        (not just scheduled during that time)
        
        Args:
            minutes_back: How many minutes to look back
            
        Returns:
            list: Recently modified events
        """
        # Get all future events first
        url = f"{self.graph_endpoint}/users/{self.user_id}/events"
        
        response = requests.get(
            url,
            headers=self.get_headers(),
            params={
                '$filter': f"lastModifiedDateTime ge {(datetime.now(timezone.utc) - timedelta(minutes=minutes_back)).isoformat()}",
                '$orderby': 'lastModifiedDateTime desc',
                '$top': 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get modified events: {response.status_code}")
            return []
        
        events = response.json().get('value', [])
        logger.info(f"✅ Found {len(events)} recently MODIFIED events")
        return events

def lambda_handler(event, context):
    """
    AWS Lambda handler for polling Graph API calendar changes
    """
    poller = GraphCalendarPoller()
    
    try:
        # Get recently modified events (more reliable than calendarview)
        events = poller.get_recently_modified_events(minutes_back=15)
        
        if not events:
            logger.info("No recent changes detected")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No changes', 'events_checked': 0})
            }
        
        logger.info(f"📝 Processing {len(events)} events...")
        
        # TODO: Send events to Event Hub for downstream processing
        # For now, just return the events
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Events polled successfully',
                'events': [
                    {
                        'id': e.get('id'),
                        'subject': e.get('subject'),
                        'modified': e.get('lastModifiedDateTime'),
                        'start': e.get('start', {}).get('dateTime'),
                        'isOnlineMeeting': e.get('isOnlineMeeting', False),
                        'onlineMeetingUrl': e.get('onlineMeetingUrl')
                    }
                    for e in events
                ]
            })
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

if __name__ == '__main__':
    # Test locally
    logging.basicConfig(level=logging.INFO)
    poller = GraphCalendarPoller()
    
    print("\n🔍 Polling recent calendar changes...")
    events = poller.get_recently_modified_events(minutes_back=120)
    
    for event in events[:5]:
        print(f"\n  📅 {event.get('subject')}")
        print(f"     Modified: {event.get('lastModifiedDateTime')}")
        print(f"     ID: {event.get('id')[:40]}...")
