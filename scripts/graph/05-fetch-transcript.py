#!/usr/bin/env python3
"""
Fetch transcript content from Microsoft Graph API.

This script demonstrates how to retrieve the full transcript content
after receiving a webhook notification with the transcript ID.

Usage:
    python 05-fetch-transcript.py <user_email> <meeting_id> <transcript_id>
    
Example (using data from webhook notification):
    python 05-fetch-transcript.py user@example.com MSo...__ MSM...
"""

import sys
import json
import argparse
import requests
from auth_helper import get_graph_headers


def fetch_transcript_metadata(user_email: str, meeting_id: str, transcript_id: str) -> dict:
    """Fetch transcript metadata (not content)."""
    headers = get_graph_headers()
    
    # For user-scoped transcripts from onlineMeetings
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}"
    
    print(f"📋 Fetching transcript metadata...")
    print(f"   URL: {url}")
    
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        metadata = response.json()
        print("\n✅ Transcript metadata retrieved:")
        print(f"   ID: {metadata.get('id')}")
        print(f"   Meeting ID: {metadata.get('meetingId')}")
        print(f"   Created: {metadata.get('createdDateTime')}")
        print(f"   Content URL: {metadata.get('transcriptContentUrl')}")
        return metadata
    else:
        print(f"\n❌ Failed to fetch metadata")
        print(f"Response: {response.text}")
        return None


def fetch_transcript_content(user_email: str, meeting_id: str, transcript_id: str) -> str:
    """Fetch the actual transcript content (VTT format)."""
    headers = get_graph_headers()
    
    # Note: Content endpoint returns VTT (WebVTT) format by default
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
    
    print(f"\n📄 Fetching transcript content...")
    print(f"   URL: {url}")
    
    # Content is returned as text/vtt by default
    response = requests.get(url, headers=headers, timeout=60)
    
    print(f"\nStatus: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        content = response.text
        print(f"\n✅ Transcript content retrieved ({len(content)} characters)")
        return content
    else:
        print(f"\n❌ Failed to fetch content")
        print(f"Response: {response.text}")
        return None


def parse_transcript_vtt(vtt_content: str) -> list:
    """Parse VTT format into structured transcript entries."""
    lines = vtt_content.split('\n')
    entries = []
    current_entry = {}
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip WEBVTT header and empty lines
        if line.startswith('WEBVTT') or not line:
            i += 1
            continue
        
        # Timestamp line (e.g., "00:00:01.234 --> 00:00:05.678")
        if '-->' in line:
            parts = line.split(' --> ')
            if len(parts) == 2:
                current_entry = {
                    'start': parts[0].strip(),
                    'end': parts[1].strip(),
                    'text': ''
                }
                
                # Next line(s) contain the text
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text_lines.append(lines[i].strip())
                    i += 1
                
                current_entry['text'] = ' '.join(text_lines)
                if current_entry['text']:
                    entries.append(current_entry)
                continue
        
        i += 1
    
    return entries


def display_transcript(entries: list, max_entries: int = None):
    """Display parsed transcript entries in a readable format."""
    print("\n" + "=" * 80)
    print("TRANSCRIPT CONTENT")
    print("=" * 80)
    
    display_count = len(entries) if max_entries is None else min(max_entries, len(entries))
    
    for idx, entry in enumerate(entries[:display_count], 1):
        print(f"\n[{entry['start']} --> {entry['end']}]")
        print(f"{entry['text']}")
    
    if max_entries and len(entries) > max_entries:
        print(f"\n... ({len(entries) - max_entries} more entries)")
    
    print("\n" + "=" * 80)


def save_transcript(content: str, filename: str):
    """Save transcript content to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n💾 Transcript saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch transcript content from Microsoft Graph API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch transcript using IDs from webhook notification
  python 05-fetch-transcript.py user@example.com MSo123...__ MSM456...
  
  # Save to file
  python 05-fetch-transcript.py user@domain.com meeting_id transcript_id --output transcript.vtt
  
  # Show only first 10 entries
  python 05-fetch-transcript.py user@domain.com meeting_id transcript_id --limit 10
        """
    )
    
    parser.add_argument('user_email', help='User email address (meeting organizer)')
    parser.add_argument('meeting_id', help='Online meeting ID (from webhook notification)')
    parser.add_argument('transcript_id', help='Transcript ID (from webhook notification)')
    parser.add_argument('--output', '-o', help='Save transcript to file')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of entries displayed')
    parser.add_argument('--metadata-only', action='store_true', help='Fetch metadata only, not content')
    
    args = parser.parse_args()
    
    print("🎯 Teams Meeting Transcript Fetcher")
    print("=" * 80)
    print(f"User: {args.user_email}")
    print(f"Meeting ID: {args.meeting_id}")
    print(f"Transcript ID: {args.transcript_id}")
    print("=" * 80)
    
    # Fetch metadata
    metadata = fetch_transcript_metadata(args.user_email, args.meeting_id, args.transcript_id)
    
    if not metadata:
        sys.exit(1)
    
    if args.metadata_only:
        print("\n✅ Metadata fetched (use without --metadata-only to fetch content)")
        sys.exit(0)
    
    # Fetch content
    content = fetch_transcript_content(args.user_email, args.meeting_id, args.transcript_id)
    
    if not content:
        sys.exit(1)
    
    # Save to file if requested
    if args.output:
        save_transcript(content, args.output)
    
    # Parse and display
    print("\n📝 Parsing transcript...")
    entries = parse_transcript_vtt(content)
    print(f"   Found {len(entries)} transcript entries")
    
    display_transcript(entries, max_entries=args.limit)
    
    print("\n✅ Done!")
    
    # Provide helpful next steps
    if not args.output:
        print("\n💡 Tip: Use --output to save the transcript to a file:")
        print(f"   python 05-fetch-transcript.py {args.user_email} {args.meeting_id} {args.transcript_id} --output transcript.vtt")


if __name__ == "__main__":
    main()
