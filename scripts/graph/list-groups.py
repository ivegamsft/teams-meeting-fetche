#!/usr/bin/env python3
"""List all groups in the tenant"""
import requests
import sys
sys.path.append("scripts/graph")
from auth_helper import get_graph_headers

headers = get_graph_headers()

resp = requests.get(
    'https://graph.microsoft.com/v1.0/groups',
    headers=headers,
    timeout=10,
    params={'$top': 20}
)

if resp.status_code != 200:
    print(f"Error: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

groups = resp.json().get('value', [])
print(f"📋 Found {len(groups)} groups:\n")

for group in groups:
    print(f"ID: {group['id']}")
    print(f"   Name: {group.get('displayName', 'N/A')}")
    print(f"   Type: {group.get('groupTypes', [])}")
    print()
