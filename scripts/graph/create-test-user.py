#!/usr/bin/env python3
"""
Create test user and add to monitored group
Uses interactive login to get user context
"""

import sys
import json
import random
import string
import subprocess

def run_command(cmd):
    """Run an Azure CLI command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None

def main():
    print("=" * 60)
    print("Create Test User and Add to Monitored Group")
    print("=" * 60)
    print()
    
    # Get current user
    print("Checking Azure CLI login...")
    user_info = run_command('az account show --query "displayName" -o tsv')
    if not user_info:
        print("❌ Not logged in to Azure")
        print("Please run: az login")
        return 1
    
    print(f"✅ Logged in as: {user_info}")
    print()
    
    # Get tenant info
    tenant_id = run_command('az account show --query "tenantId" -o tsv')
    default_domain = "ibuyspy.net"  # Hardcoded for now
    
    print(f"Tenant ID: {tenant_id}")
    print(f"Default domain: {default_domain}")
    print()
    
    # Generate random pet name for test user
    animals = ["cat", "dog", "fox", "bear", "eagle", "shark", "wolf", "deer"]
    adjectives = ["happy", "quick", "clever", "bright", "swift", "bold", "calm", "eager"]
    
    random.seed()
    animal = random.choice(animals)
    adjective = random.choice(adjectives)
    test_user_name = f"{adjective}{animal}"
    test_user_upn = f"{test_user_name}@{default_domain}"
    test_user_display_name = f"TMF {test_user_name.capitalize()}"
    
    # Generate random password
    password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choices(password_chars, k=24))
    
    print(f"Test User Details:")
    print(f"  UPN: {test_user_upn}")
    print(f"  Display Name: {test_user_display_name}")
    print(f"  Password: (generated, {len(password)} chars)")
    print()
    
    # Create user
    print("Creating test user...")
    create_cmd = f"""
az ad user create \\
  --user-principal-name {test_user_upn} \\
  --display-name "{test_user_display_name}" \\
  --mail-nickname {test_user_name} \\
  --password "{password}" \\
  --force-change-password-next-logon false \\
  --query 'id' -o tsv
"""
    
    user_id = run_command(create_cmd.strip().replace('\n', ' ').replace('  ', ' '))
    
    if not user_id or user_id == "":
        print("⚠️  Could not create user. It may already exist.")
        print("Looking up existing user...")
        user_lookup = run_command(f"az ad user show --id {test_user_upn} --query 'id' -o tsv")
        if user_lookup:
            user_id = user_lookup
            print(f"✅ Found existing user: {user_id}")
        else:
            print("❌ Failed to find or create user")
            return 1
    else:
        print(f"✅ User created: {user_id}")
    
    print()
    
    # Get monitored group
    print("Looking up monitored group...")
    group_lookup = run_command("""
az ad group list --query "[?displayName=='Teams Meeting Fetcher Monitored Meetings (dev)'].id" -o tsv
""")
    
    if not group_lookup:
        print("❌ Could not find monitored group")
        return 1
    
    group_id = group_lookup.split('\n')[0]  # Get first result if multiple
    print(f"✅ Found monitored group: {group_id}")
    print()
    
    # Add user to group
    print(f"Adding user to group...")
    add_cmd = f"az ad group member add --group {group_id} --member-id {user_id}"
    
    result = run_command(add_cmd)
    if result is None:
        print(f"❌ Failed to add user to group")
        return 1
    
    print(f"✅ User added to monitored group")
    print()
    
    # Verify group membership
    print("Verifying group membership...")
    members = run_command(f"az ad group member list --group {group_id} --query 'length(@)' -o tsv")
    if members and int(members) > 0:
        print(f"✅ Group now has {members} member(s)")
    
    print()
    print("=" * 60)
    print("Test User Setup Complete! 🎉")
    print("=" * 60)
    print()
    print(f"Test user credentials:")
    print(f"  Username: {test_user_upn}")
    print(f"  Password: {password}")
    print(f"  Display Name: {test_user_display_name}")
    print()
    print("The user has been added to the monitored group and can now")
    print("create Teams meetings that will be captured by Event Hub.")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
