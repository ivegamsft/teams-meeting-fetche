#!/usr/bin/env python3
"""Add a user to the monitored group"""
import requests
import sys
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

group_id = "5e7708f8-b0d2-467d-97f9-d9da4818084a"  # TMF Monitored Meetings group
user_email = "boldoriole@ibuyspy.net"

headers = get_graph_headers()

# Get user ID by email
user_resp = requests.get(
    f'https://graph.microsoft.com/v1.0/users/{user_email}',
    headers=headers,
    timeout=10
)

if user_resp.status_code != 200:
    print(f"Failed to get user: {user_resp.status_code}")
    print(user_resp.text)
    sys.exit(1)

user = user_resp.json()
user_id = user['id']

print(f"👤 Adding {user_email} ({user_id})")
print(f"📋 To group {group_id}")
print()

# Add user to group
add_resp = requests.post(
    f'https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref',
    headers=headers,
    json={"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"},
    timeout=10
)

if add_resp.status_code not in [200, 204]:
    print(f"❌ Failed: {add_resp.status_code}")
    print(add_resp.text)
    sys.exit(1)

print("✅ User added to group successfully!")
