#!/usr/bin/env python3
"""
Fetch transcripts from recent meetings
"""
import sys
import requests
from auth_helper import get_graph_headers, get_config

config = get_config()
user_email = config.get('user_email', 'boldoriole@ibuyspy.net')

headers = get_graph_headers()

# Get user OID  
print("📋 Fetching user info...")
user_url = f'https://graph.microsoft.com/v1.0/users/{user_email}'
user_resp = requests.get(user_url, headers=headers, timeout=10)

if user_resp.status_code != 200:
    print(f"❌ Error getting user: {user_resp.status_code}")
    print(user_resp.text)
    sys.exit(1)

user_id = user_resp.json()['id']
print(f"✅ User: {user_email}")
print(f"   ID: {user_id}")

# Get transcripts
print("\n📝 Fetching transcripts...")
transcripts_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId=\'{user_id}\')'
trans_resp = requests.get(transcripts_url, headers=headers, timeout=10)

if trans_resp.status_code != 200:
    print(f"❌ Error getting transcripts: {trans_resp.status_code}")
    print(trans_resp.text[:500])
    sys.exit(1)

transcripts = trans_resp.json()
trans_list = transcripts.get('value', [])

if not trans_list:
    print("❌ No transcripts found")
    sys.exit(1)

print(f"✅ Found {len(trans_list)} transcript(s)\n")

# Show most recent
for i, t in enumerate(trans_list[:3]):
    meeting_id = t.get('id', '?')
    created = t.get('createdDateTime', '?')
    content_url = t.get('contentUrl', '')
    
    print(f"[{i+1}] Meeting ID: {meeting_id}")
    print(f"    Created: {created}")
    
    if content_url:
        print(f"    ✅ Content URL available")
        # Try to fetch content
        content_resp = requests.get(content_url, headers=headers, timeout=30)
        if content_resp.status_code == 200:
            print(f"    📄 Transcript content ({len(content_resp.text)} bytes):")
            print(f"    {content_resp.text[:200]}...")
        else:
            print(f"    ❌ Could not fetch content: {content_resp.status_code}")
    else:
        print(f"    ⏳ No content URL yet (still processing?)")
    print()
