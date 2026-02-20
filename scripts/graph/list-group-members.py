#!/usr/bin/env python3
"""Get members of a group"""
import requests
import sys
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

group_id = "5e7708f8-b0d2-467d-97f9-d9da4818084a"

headers = get_graph_headers()

resp = requests.get(
    f'https://graph.microsoft.com/v1.0/groups/{group_id}/members',
    headers=headers,
    timeout=10,
    params={'$top': 100}
)

if resp.status_code != 200:
    print(f"Error: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

members = resp.json().get('value', [])
print(f"📋 Group members ({len(members)}):\n")

for member in members:
    print(f"ID: {member['id']}")
    print(f"   Name: {member.get('displayName', 'N/A')}")
    print(f"   Email: {member.get('userPrincipalName', 'N/A')}")
    print()
