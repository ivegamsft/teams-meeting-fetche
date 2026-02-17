---
description: Create a comprehensive inventory of Teams bot configuration for repeatability
---

## User Input

```text
$ARGUMENTS
```

You **MUST** acknowledge the user input before proceeding.

## Overview

This agent audits and documents your complete Teams bot configuration:

1. Exports Azure AD app registrations and permissions
2. Documents Teams admin policies and assignments
3. Lists security group memberships
4. Captures webhook subscriptions
5. Records Lambda and API Gateway configuration
6. Generates a `teams-config-inventory.md` file for repeatability

## Workflow

### Step 1: Verify Prerequisites

- Check `az` CLI is installed and authenticated
- Verify `GRAPH_CLIENT_ID`, `GRAPH_TENANT_ID`, `ENTRA_GROUP_ID` are set in `.env.local`
- Verify Python scripts are available in `scripts/graph/`

### Step 2: Create Inventory Directory

```bash
mkdir -p inventory/
```

### Step 3: Export Azure AD Configurations

1. Export main app:

   ```bash
   az ad app show --id $GRAPH_CLIENT_ID --output json > inventory/app-registration-main.json
   ```

2. Export bot app:

   ```bash
   az ad app show --id $BOT_APP_ID --output json > inventory/app-registration-bot.json
   ```

3. Export API permissions:

   ```bash
   az ad app permission list --id $GRAPH_CLIENT_ID --output json > inventory/app-permissions-main.json
   az ad app permission list --id $BOT_APP_ID --output json > inventory/app-permissions-bot.json
   ```

4. Export service principals:
   ```bash
   az ad sp show --id $GRAPH_CLIENT_ID --output json > inventory/sp-main.json
   az ad sp show --id $BOT_APP_ID --output json > inventory/sp-bot.json
   ```

### Step 4: Export Security Group

```bash
az ad group show --group-object-id $ENTRA_GROUP_ID > inventory/group-info.json
az ad group member list --group-object-id $ENTRA_GROUP_ID --output json > inventory/group-members.json
```

Report:

- Group name and description
- Member count
- Member types (users, service principals)

### Step 5: Export Webhook Subscriptions

```bash
python scripts/graph/list-subscriptions.py > inventory/subscriptions-list.txt
python scripts/graph/check-subscriptions.py --export json > inventory/subscriptions.json
```

For each subscription, document:

- Resource monitored
- Webhook URL
- Expiration date
- Current state (active/expired)

### Step 6: Export Lambda/API Configuration

```bash
# Lambda config (without env variables containing secrets)
aws lambda get-function-configuration --function-name <function-name> \
  --profile tmf-dev --query '{Runtime:Runtime, Handler:Handler, MemorySize:MemorySize, Timeout:Timeout}' \
  > inventory/lambda-config.json

# API Gateway
aws apigateway get-rest-apis --profile tmf-dev \
  --query "items[?contains(name, 'tmf')]" \
  > inventory/api-gateway-config.json
```

### Step 7: Copy Teams App Manifest

```bash
cp teams-app/manifest.json inventory/manifest-main.json
if [ -f "teams-app/manifest-dev.json" ]; then
  cp teams-app/manifest-dev.json inventory/manifest-dev.json
fi
```

### Step 8: Generate Inventory Markdown Document

Create `inventory/teams-config-inventory.md` with:

- Project and date
- Azure AD app info (IDs, permissions)
- Security group details
- Teams admin policies
- Webhook configuration
- Teams app manifest summary
- Lambda/API endpoint info
- Step-by-step reproduction instructions

### Step 9: Create Reproducibility Checklist

Generate a checklist showing:

- ✅ What has been exported
- ✅ What is documented
- ✅ What can be reproduced from this inventory

```text
✅ Azure AD app registrations
✅ API permissions documented
✅ Security group and members
✅ Webhook subscriptions
✅ Lambda configuration
✅ Teams app manifest
✅ Reproduction instructions
```

### Step 10: Archive & Commit

```bash
# Optional: zip for backup
zip -r inventory-$(date +%Y%m%d-%H%M%S).zip inventory/

# Commit inventory
git add inventory/teams-config-inventory.md
git commit -m "docs: teams config inventory snapshot"
```

## Output Example

```
📋 TEAMS CONFIGURATION INVENTORY
Generated: 2026-02-16 @ 14:30 UTC

📱 Azure AD Apps
  ├─ Main App: d1234567-89ab-cdef-0123-456789abcdef
  │  ├─ Permissions: 12 (Delegated: 8, Application: 4)
  │  └─ Secrets expire: 2026-08-16
  └─ Bot App: b1234567-89ab-cdef-0123-456789abcdef

👥 Security Group
  ├─ Name: Teams Meeting Fetcher - Bot Access
  ├─ Members: 45 users
  └─ Object ID: g1234567-89ab-cdef-0123-456789abcdef

🔔 Webhook Subscriptions (Active)
  ├─ /communications/callRecords (expires: 2026-02-24)
  └─ /teams/onlineMeetings/[id]/transcripts (expires: 2026-02-23)

⚙️ Lambda Function
  ├─ Function: tmf-webhook-handler
  ├─ Runtime: Node.js 18
  ├─ Memory: 512 MB
  └─ Endpoint: https://api.example.com/webhook

📝 Inventory files created:
  - inventory/teams-config-inventory.md
  - inventory/app-registration-main.json
  - inventory/app-registration-bot.json
  - inventory/group-members.json
  - inventory/subscriptions.json
  - [others...]

✅ Inventory complete — ready for backup and reproducibility testing
```

## Rules

- **Never export secrets** — filter them out before saving
- **Always set GRAPH_CLIENT_ID, GRAPH_TENANT_ID, ENTRA_GROUP_ID** before running
- **Document everything** — this inventory should be your single source of truth
- **Keep inventory in Git** (though `.json` files with secrets should be gitignored)
- **Update the inventory** every time you change Teams configuration
- **Use the inventory to test reproducibility** (see `validate-teams-config-repeatability` agent)
