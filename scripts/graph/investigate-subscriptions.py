#!/usr/bin/env python3
"""
Investigate which Graph subscription resources are supported
"""
import sys
import requests
from datetime import datetime, timedelta, timezone

sys.path.append("scripts/graph")
from auth_helper import get_graph_headers, get_config

config = get_config()
webhook_url = config.get("bot_meeting_started_url") or "https://example.com/webhook"
client_state = config.get("webhook_secret", "test")[:255]
headers = get_graph_headers()
expiration = datetime.now(timezone.utc) + timedelta(hours=24)

# Try different resource paths for meeting/call subscriptions
test_resources = [
    # Original (failed)
    "communications/onlineMeetings",
    
    # Variations that might work
    "/communications/onlineMeetings",
    "communications/calls",
    "/communications/calls",
    
    # Different format - specific meeting
    "users/<YOUR_EMAIL>/onlineMeetings",
    
    # Call records (might exist)
    "communications/callRecords",
    "/communications/callRecords",
    
    # Presence (simpler resource to test)
    "me/presence",
]

print("🔍 Testing subscription resources...\n")
print(f"❗ NOTE: Testing with app-only auth (may have limitations)")
print(f"   Bot App ID: {config.get('GRAPH_CLIENT_ID', '?')[:8]}...")
print(f"   Webhook URL: {webhook_url}\n")

results = []

for resource in test_resources:
    subscription_data = {
        "changeType": "created",
        "notificationUrl": webhook_url,
        "resource": resource,
        "expirationDateTime": expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        "clientState": client_state,
    }
    
    print(f"📤 Testing: {resource}")
    
    response = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=subscription_data,
        timeout=10,
    )
    
    status = response.status_code
    
    if status == 201:
        result = response.json()
        print(f"   ✅ SUCCESS (201) - Created!")
        print(f"      Sub ID: {result['id'][:30]}...")
        results.append((resource, "SUCCESS", status))
        
        # Clean it up
        del_resp = requests.delete(
            f"https://graph.microsoft.com/v1.0/subscriptions/{result['id']}",
            headers=headers,
            timeout=10
        )
        if del_resp.status_code == 204:
            print(f"      Cleaned up test subscription")
    else:
        error_info = ""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "")
            error_code = error_data.get("error", {}).get("code", "")
            if error_msg:
                error_info = f": {error_code} - {error_msg[:80]}"
        except:
            error_info = f": {response.text[:100]}"
        
        print(f"   ❌ FAILED ({status}){error_info}")
        results.append((resource, "FAILED", status, error_info))
    print()

print("\n" + "="*80)
print("📊 SUMMARY:")
print("="*80)
for r in results:
    resource = r[0]
    status_str = "✅" if r[1] == "SUCCESS" else "❌"
    code = r[2]
    msg = r[3] if len(r) > 3 else ""
    print(f"{status_str} {code}  {resource:40s} {msg}")

print("\n🔍 INVESTIGATION NOTES:")
print("-" * 80)
print("""
If communications/onlineMeetings returns 400 "Unsupported workload":
  - This resource may require delegated auth (user context), not app-only
  - Or Microsoft Graph may not support subscriptions for this resource type
  
If communications/calls works:
  - We can use this instead for call tracking
  
If all fail with permission errors:
  - Check bot app has correct permissions assigned in Azure AD
  - Current permissions should include: Calls.JoinGroupCall.All, Calls.Initiate.All
  
Recommended alternative:
  - Use existing users/{id}/events subscription (already working)
  - Parse onlineMeeting data from calendar events
  - Manually poll getAllTranscripts() at intervals instead of webhook
""")
