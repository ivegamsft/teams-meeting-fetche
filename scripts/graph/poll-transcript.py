#!/usr/bin/env python3
"""
Poll for transcript content and test the transcript fetch pipeline
"""
import sys
import time
import requests
from auth_helper import get_graph_headers, get_config

config = get_config()
user_email = config.get('user_email', 'boldoriole@ibuyspy.net')
headers = get_graph_headers()

# Get user
print("👤 Getting user ID...")
user_resp = requests.get(f'https://graph.microsoft.com/v1.0/users/{user_email}', headers=headers, timeout=10)
user_id = user_resp.json()['id']

# Poll for transcript content
max_polls = 20  # 20 * 10 = 200 seconds = ~3 minutes
poll_interval = 10

for poll_num in range(1, max_polls + 1):
    print(f"\n[{poll_num}/{max_polls}] Checking for transcript content...")
    
    transcripts_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId=\'{user_id}\')'
    trans_resp = requests.get(transcripts_url, headers=headers, timeout=10)
    trans_list = trans_resp.json().get('value', [])
    
    if not trans_list:
        print("❌ No transcripts found")
        break
    
    # Check most recent
    most_recent = trans_list[0]
    meeting_id = most_recent.get('id', '?')
    content_url = most_recent.get('contentUrl', '')
    created = most_recent.get('createdDateTime', '?')
    
    print(f"📅 Created: {created[:19]}")
    
    if content_url:
        print(f"✅ Content URL available! Fetching...")
        content_resp = requests.get(content_url, headers=headers, timeout=30)
        
        if content_resp.status_code == 200:
            print(f"📄 Transcript content ({len(content_resp.text)} bytes):")
            print(f"\n{content_resp.text}\n")
            print(f"✨ Successfully fetched transcript!")
            sys.exit(0)
        else:
            print(f"⚠️  Content URL exists but fetch failed: {content_resp.status_code}")
            print(f"   Response: {content_resp.text[:200]}")
    else:
        elapsed = poll_num * poll_interval
        print(f"⏳ Still processing... ({elapsed}s elapsed)")
        
        if poll_num < max_polls:
            print(f"   Waiting {poll_interval}s before next check...")
            time.sleep(poll_interval)
        else:
            print(f"❌ Timeout: Transcript not ready after {elapsed}s")
            sys.exit(1)

print("❌ Failed to get transcript content")
sys.exit(1)
