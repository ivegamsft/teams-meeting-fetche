# Inventory Teams Config — Audit & Document Current Setup

## Purpose

Create a complete inventory of the Teams bot configuration: policies, groups, app registration, subscriptions, and permissions. Export as documentation to make the setup repeatable.

## Instructions

### Step 1: Audit Teams Admin Policies

Check what policies are currently assigned:

```powershell
# Connect to Teams PowerShell
Connect-MicrosoftTeams

# List all users with the Teams Setup Policy
Get-CsUserPolicyAssignment -PolicyType TeamsMeetingBroadcastPolicy | Export-Csv -Path "teams-setup-policy-users.csv"

# List all users with the Meeting Policy
Get-CsUserPolicyAssignment -PolicyType TeamsMeetingPolicy | Export-Csv -Path "teams-meeting-policy-users.csv"

# Get the actual policy configurations
Get-CsTeamsAppSetupPolicy | ConvertTo-Json | Out-File -Path "teams-app-setup-policy.json"
Get-CsTeamsMeetingPolicy | ConvertTo-Json | Out-File -Path "teams-meeting-policy.json"
```

Or via Azure CLI (if scoped to a security group):

```bash
# List group assignments
az ad group show --group-object-id $ENTRA_GROUP_ID --query "members" > group-members.json

# List who has the policy
az ad group member list --group-object-id $ENTRA_GROUP_ID --output json > group-members-detail.json
```

Document findings:

- Which policy object is assigned? (Default, custom, etc.)
- How many users/groups are assigned?
- What are the key settings? (e.g., allow transcription, disable recording, etc.)

### Step 2: Audit Security Groups

List security groups and their memberships:

```bash
# Audit the main allowed group
az ad group show --group-object-id $ENTRA_GROUP_ID

# Get all members
az ad group member list --group-object-id $ENTRA_GROUP_ID --query "[].{displayName:displayName, userPrincipalName:userPrincipalName, objectId:id}" --output table

# Export to CSV for backup
az ad group member list --group-object-id $ENTRA_GROUP_ID --query "[].{displayName:displayName, userPrincipalName:userPrincipalName, objectId:id}" --output json > entra-group-members.json
```

Document:

- Group name and object ID
- Number of members
- Member types (users, service principals, etc.)
- Group description and purpose

### Step 3: Audit Azure AD App Registrations

Export the complete app registration configurations:

```bash
# Main app registration
az ad app show --id $GRAPH_CLIENT_ID --output json > app-registration-main.json

# Bot app registration
az ad app show --id $BOT_APP_ID --output json > app-registration-bot.json

# Get API permissions for each
az ad app permission list --id $GRAPH_CLIENT_ID --output json > app-permissions-main.json
az ad app permission list --id $BOT_APP_ID --output json > app-permissions-bot.json

# Get service principals
az ad sp show --id $GRAPH_CLIENT_ID --output json > sp-main.json
az ad sp show --id $BOT_APP_ID --output json > sp-bot.json
```

Document for each app:

- Application (client) ID
- Display name and description
- API permissions granted (delegated, application)
- Redirect URIs (if configured)
- Certificate/Secret expiration dates
- Owner(s)

### Step 4: Audit Webhook Subscriptions

List and document all active subscriptions:

```bash
python scripts/graph/list-subscriptions.py > subscriptions-inventory.txt

# Or manually via Graph API
python scripts/graph/check-subscriptions.py --export json > subscriptions.json
```

For each subscription, document:

- Resource being monitored (e.g., `/communications/callRecords`)
- Notification URL (webhook endpoint)
- Expiration date/time
- When subscription was created
- Current state (active, expired, etc.)

### Step 5: Audit Teams App Configuration

Export the app manifests and configuration:

```bash
# Copy manifests to inventory
cp teams-app/manifest.json teams-app/manifest-dev.json inventory/

# Archive old versions if any
if [ -f "teams-app/manifest-backup.json" ]; then
  cp teams-app/manifest-backup.json inventory/manifest-backup.json
fi

# Document manifest contents
jq '{id, version, name, description, bots, composeExtensions, permissions, validDomains}' teams-app/manifest.json > inventory/teams-app-config.json
```

Document:

- App ID (must match Azure AD app)
- App name and version
- Bot ID (must match bot app registration)
- Configured bots and their endpoints
- Compose extensions (if any)
- Permissions requested
- Valid domains for the webhook

### Step 6: Audit Lambda/API Configuration

Export the webhook endpoint configuration:

```bash
# Get Lambda environment variables (without secrets)
aws lambda get-function-configuration --function-name <function-name> --profile tmf-dev \
  --query '{Runtime:Runtime, Handler:Handler, MemorySize:MemorySize, Timeout:Timeout, Environment:Environment.Variables}' \
  > inventory/lambda-config.json

# Get API Gateway configuration
aws apigateway get-rest-apis --profile tmf-dev \
  --query 'items[?name==`<api-name>`]' \
  > inventory/api-gateway-config.json

# Get authorizer configuration
aws apigateway get-authorizer --rest-api-id <api-id> --authorizer-id <authorizer-id> --profile tmf-dev \
  > inventory/api-authorizer-config.json
```

Document:

- Lambda function name and ARN
- Lambda role and permissions
- Memory and timeout settings
- API Gateway endpoint URL
- Authorizer configuration (if any)
- Environment variables (names only, no values)

### Step 7: Create Inventory Document

Generate a markdown file that documents the entire setup:

```markdown
# Teams Bot Configuration Inventory

**Generated**: $(date)
**Environment**: dev/staging/prod

## Azure AD App Registrations

### Main App (Graph Access)

- **ID**: $GRAPH_CLIENT_ID
- **Name**: [from app-registration-main.json]
- **API Permissions**: [list from app-permissions-main.json]
- **Secrets expiring**: [dates]

### Bot App

- **ID**: $BOT_APP_ID
- **Name**: [from app-registration-bot.json]
- **Secrets expiring**: [dates]

## Teams Admin Policies

- **Setup Policy**: [policy name and settings]
- **Meeting Policy**: [policy name and settings]
- **Assigned to**: [group name with X members]
  - Last updated: [date]

## Security Groups

### $ENTRA_GROUP_ID (Bot access group)

- **Name**: [from Azure AD]
- **Members**: X users
- **Last audited**: $(date)

## Webhook Configuration

### Active Subscriptions

- Resource: `/communications/callRecords` (expires: [date])
- Resource: `/teams/onlineMeetings/[id]/transcripts` (expires: [date])
- Notification URL: `$AWS_WEBHOOK_ENDPOINT`

## Teams App

- **App ID**: [from manifest]
- **Version**: [from manifest]
- **Valid Domains**: [from manifest]
- **Bot ID**: [matches $BOT_APP_ID]

## Lambda/API Gateway

- **Function**: [function-name]
- **Endpoint**: `$AWS_WEBHOOK_ENDPOINT`
- **Memory**: [from config]
- **Timeout**: [from config]
- **Authorizer**: [enabled/disabled]

## How to Reproduce

1. Create Azure AD apps (main + bot)
2. Configure API permissions (see section above)
3. Create security group and add members
4. Assign Teams admin policies to group
5. Deploy Lambda and API Gateway
6. Create webhook subscriptions
7. Upload Teams app to tenant
8. Assign Teams app to users/group
```

### Step 8: Export & Store

```bash
# Create inventory directory
mkdir -p inventory/
cd inventory/

# Already exported above:
# - app-registration-main.json
# - app-registration-bot.json
# - app-permissions-main.json
# - team-setup-policy-users.csv
# - subscriptions.json
# - teams-app-config.json
# - lambda-config.json
# - teams-config-inventory.md

# Archive everything
zip -r teams-config-inventory-$(date +%Y%m%d).zip *.json *.csv *.md

# Keep the markdown as-is for documentation
git add teams-config-inventory.md
```

### Step 9: Validation Checklist

Present a checklist to verify everything is documented:

- ✅ Azure AD app registrations exported
- ✅ API permissions documented
- ✅ Teams admin policies listed and assigned users counted
- ✅ Security group memberships exported
- ✅ Webhook subscriptions active and documented
- ✅ Teams app manifest current
- ✅ Lambda/API configuration compatible with manifest webhook URL
- ✅ Inventory markdown created
- ✅ All configs stored in `inventory/`
- ✅ Archive ready for backup

### Rules

- **Never export secrets** — only names, IDs, and non-sensitive configuration.
- Use `--query` to filter sensitive fields from AWS/Azure CLI output.
- Document expiration dates for secrets and subscriptions.
- Update the inventory **every time you make a change** to the Teams bot setup.
- Keep `teams-config-inventory.md` in the repo root or `docs/` for easy reference.
