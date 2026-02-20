"""
Create a test meeting for Event Hub testing - Non-interactive version
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from scripts.graph.03_create_test_meeting import create_calendar_event_with_teams_meeting

# Test user
user_email = "trustingboar@ibuyspy.net"

# Create meeting 1 hour from now with transcript enabled
start_time = datetime.utcnow() + timedelta(hours=1)
meeting = create_calendar_event_with_teams_meeting(
    user_email=user_email,
    subject="Test Meeting with Transcript - Event Hub Test",
    start_time=start_time,
    duration_minutes=60,
    attendees=None,
    enable_transcript=True
)

if meeting:
    print("\n" + "=" * 70)
    print("✅ MEETING CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\nMeeting Details:")
    print(f"  Event ID: {meeting['id']}")
    print(f"  Organizer: {user_email}")
    print(f"  Subject: {meeting['subject']}")
    print(f"  Start: {meeting['start']['dateTime']} UTC")
    print(f"  Join URL: {meeting.get('onlineMeetingUrl', 'N/A')}")
    print("\n📝 Next: Check Event Hub for incoming messages from Microsoft Graph")
    print("   (It may take 30 seconds to 1 minute for the notification to arrive)")
    sys.exit(0)
else:
    print("\n❌ Failed to create meeting")
    sys.exit(1)
