"""
Create a test meeting directly - simplified version
"""
import sys
import json
import requests
from datetime import datetime, timedelta
from auth_helper import get_graph_headers

def create_meeting():
    """Create meeting for trustingboar@ibuyspy.net with transcript enabled"""
    
    user_email = "trustingboar@ibuyspy.net"
    subject = "Test Meeting with Transcript - Event Hub Test"
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(minutes=60)
    
    print(f"\n📅 Creating Teams meeting...")
    print(f"   Organizer: {user_email}")
    print(f"   Subject: {subject}")
    print(f"   Start: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Duration: 60 minutes")
    print(f"   Transcript: Enabled")
    print()
    
    headers = get_graph_headers()
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/events"
    
    payload = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": "This is a test Teams meeting for Event Hub notification testing.<br><br><b>Transcription is enabled.</b>"
        },
        "start": {
            "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "UTC"
        },
        "location": {
            "displayName": "Microsoft Teams Meeting"
        },
        "attendees": [],
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 201:
            event = response.json()
            print(f"✅ Meeting created successfully!")
            print(f"\nEvent Details:")
            print(f"  Event ID: {event['id']}")
            print(f"  iCalUId: {event['iCalUId']}")
            
            if 'onlineMeetingUrl' in event:
                print(f"  Join URL: {event['onlineMeetingUrl']}")
            
            if 'onlineMeeting' in event:
                online_meeting_id = event['onlineMeeting'].get('id')
                if online_meeting_id:
                    print(f"  Online Meeting ID: {online_meeting_id}")
                    # Try to enable transcript
                    enable_transcript_for_meeting(online_meeting_id, headers)
            
            print(f"\n📝 Created by: {user_email}")
            print(f"📅 Start time: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"⏱️  Duration: 60 minutes")
            
            return event
        else:
            print(f"❌ Failed to create meeting: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def enable_transcript_for_meeting(online_meeting_id, headers):
    """Enable transcript for the meeting"""
    print(f"\n📝 Enabling transcript for meeting...")
    url = f"https://graph.microsoft.com/v1.0/communications/onlineMeetings/{online_meeting_id}"
    
    payload = {
        "allowTranscription": True,
        "recordAutomatically": True
    }
    
    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Transcript enabled")
            print("   ✅ Auto-record enabled")
        elif response.status_code == 403:
            print("   ⚠️  Insufficient permissions to enable transcript (but meeting still created)")
        else:
            print(f"   ⚠️  Could not enable transcript: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Error enabling transcript: {e}")


if __name__ == "__main__":
    create_meeting()
