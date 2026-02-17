# Clean Up Teams Environment — Policies, Groups, App Registration

## Purpose

Help me safely remove the Teams bot from an organization: unassign policies, remove security groups, delete test data, and clean up Azure AD app registration.

## Instructions

### Step 1: Audit Current State

Check what's currently deployed:

```bash
# Teams admin policies
python scripts/teams/check-admin-policies.py  # (or similar if it exists)

# Security group memberships
az ad group member list --group-object-id $ENTRA_GROUP_ID

# Test meetings/recordings
python scripts/graph/check_recordings.py
python scripts/graph/check_calendar.py

# Webhook subscriptions
python scripts/graph/check-subscriptions.py

# Teams app installation
python scripts/teams/check-app-installation.py  # (or similar)
```

Report what is currently active:

- Which users/teams have the Teams Setup Policy assigned
- Which users have the Meeting Policy assigned
- How many test meetings exist (and their dates)
- How many recordings exist
- Which webhook subscriptions are active

### Step 2: Remove Webhook Subscriptions

Webhook subscriptions need to be cleaned up first (to prevent stale notifications):

```bash
python scripts/graph/delete-subscriptions.py
# OR manually list and delete via Azure Portal > App registrations > <app> > API permissions
```

Verify all subscriptions are removed:

```bash
python scripts/graph/check-subscriptions.py
```

### Step 3: Remove Teams Admin Policies

Ask which scope to remove policies from:

- **All users** (org-wide unassignment)
- **Specific security group** (if you assigned policies to a group)

Then run the removal script:

```powershell
powershell -File scripts/setup-teams-policies.ps1 -Action Remove -GroupId $ENTRA_GROUP_ID
```

Or manually in Teams Admin Center:

1. Navigate to **Meetings** > **Meeting policies** → Remove policy assignment
2. Navigate to **Teams apps** > **Setup policies** → Remove policy assignment
3. Navigate to **Org-wide settings** > **Teams settings** → Disable/reset bot configuration

### Step 4: Remove Security Group Membership

If you created a test security group or added users to `$ENTRA_GROUP_ID`, remove them:

```bash
# List current members
az ad group member list --group-object-id $ENTRA_GROUP_ID

# Remove each member (or delete the group if it was test-only)
az ad group member remove --group-object-id $ENTRA_GROUP_ID --member-object-id <user-object-id>
```

### Step 5: Clean Up Test Meetings & Recordings

Delete test meetings and associated recordings:

```bash
# List test meetings and recordings
python scripts/graph/check_recordings.py
python scripts/graph/check_calendar.py

# Delete recordings (if they exist)
python scripts/graph/delete-recordings.py  # (or script you use for cleanup)

# Delete test meetings from calendar (via Outlook or Teams UI)
```

### Step 6: Deregister Bot from Teams App Catalog (Optional)

If you published the bot to the Teams App Catalog:

1. Go to **Teams Admin Center** > **Teams apps** > **Manage apps**
2. Search for your bot
3. Click **Delete** to remove it from the org catalog

### Step 7: Clean Up Azure AD App Registration

Decide what to do with the Azure AD app:

**Option A: Delete entirely** (full cleanup)

```bash
az ad app delete --id $GRAPH_CLIENT_ID
```

**Option B: Deactivate** (keep for later reactivation)

```bash
az ad app delete --id $GRAPH_CLIENT_ID --force  # Or disable in Portal
```

**Option C: Archive** (if policy requires)

- Document the app ID, client ID, and client secret in a backup file
- Store securely (e.g., in a private wiki or encrypted backup)

### Step 8: Verify Cleanup

Confirm everything is removed:

```bash
# No active subscriptions
python scripts/graph/check-subscriptions.py  # Should return empty

# No policies assigned
# (Manual check in Teams Admin Center)

# Security group members removed or group deleted
az ad group show --group-object-id $ENTRA_GROUP_ID  # Should fail or show no members

# Test meetings deleted
python scripts/graph/check_calendar.py  # Should show no test meetings
```

### Step 9: Document Removal

Report what was cleaned up:

- Webhook subscriptions deleted: YES/NO
- Teams admin policies removed: YES/NO
- Security group membership cleaned: YES/NO
- Test meetings/recordings deleted: YES/NO
- Azure AD app deleted/disabled: YES/NO

### Rules

- **Always verify tenant** before running Azure CLI commands: `az account show --query "tenantId"`
- Unsubscribe webhooks BEFORE deleting the app (so you don't leave dangling subscriptions).
- If you want to keep a backup of the app registration, document the app ID and client ID before deleting.
- Be careful with security group deletion — make sure it wasn't used for other purposes.
