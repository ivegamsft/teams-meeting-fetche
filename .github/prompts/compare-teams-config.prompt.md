# Compare Teams Config — Prod vs Dev & Consistency Check

## Purpose

Compare Teams configurations across environments (prod vs dev/staging) to identify drift, inconsistencies, or missing configurations. Ensure all environments are aligned.

## Instructions

### Step 1: Select Environments to Compare

Ask which environments to compare:

- **Prod vs Dev**: Main vs development
- **Prod vs Staging**: Main vs staging
- **All three**: Comprehensive comparison
- **Custom**: Specify environment names

### Step 2: Export Configurations from Each Environment

For each environment, export the current configuration:

```bash
# Set environment-specific variables
# For production
export PROD_TENANT_ID=<prod-tenant>
export PROD_APP_ID=<prod-app>
export PROD_BOT_ID=<prod-bot>
export PROD_GROUP_ID=<prod-group>

# For development
export DEV_TENANT_ID=<dev-tenant>
export DEV_APP_ID=<dev-app>
export DEV_BOT_ID=<dev-bot>
export DEV_GROUP_ID=<dev-group>

# Export prod configs
az account set --subscription $PROD_SUBSCRIPTION_ID
az ad app show --id $PROD_APP_ID --output json > compare/prod-app-main.json
az ad app show --id $PROD_BOT_ID --output json > compare/prod-app-bot.json
az ad group member list --group-object-id $PROD_GROUP_ID --output json > compare/prod-group-members.json
python scripts/graph/check-subscriptions.py --env prod --export json > compare/prod-subscriptions.json

# Export dev configs
az account set --subscription $DEV_SUBSCRIPTION_ID
az ad app show --id $DEV_APP_ID --output json > compare/dev-app-main.json
az ad app show --id $DEV_BOT_ID --output json > compare/dev-app-bot.json
az ad group member list --group-object-id $DEV_GROUP_ID --output json > compare/dev-group-members.json
python scripts/graph/check-subscriptions.py --env dev --export json > compare/dev-subscriptions.json
```

### Step 3: Compare Azure AD Apps

Compare the main applications:

```bash
# Extract keys to compare
jq '{id, displayName, appId, web: .web, api: .api.exposedScopes}' compare/prod-app-main.json > compare/prod-app-main-keys.json
jq '{id, displayName, appId, web: .web, api: .api.exposedScopes}' compare/dev-app-main.json > compare/dev-app-main-keys.json

# Visual diff
diff -u compare/prod-app-main-keys.json compare/dev-app-main-keys.json | head -50
```

Document differences:

- ✅ **Display name**: Should match (or differ only by environment suffix)
- ✅ **API permissions**: Should be identical
- ✅ **Redirect URIs**: Should differ only if dev uses localhost
- ✅ **Certificates/Secrets**: Should have different values (expected), but same expiration policies
- ⚠️ **Service Principal owners**: Should be consistent roles

Compare bot apps similarly:

```bash
jq '{id, displayName, appId}' compare/prod-app-bot.json > compare/prod-app-bot-keys.json
jq '{id, displayName, appId}' compare/dev-app-bot.json > compare/dev-app-bot-keys.json

diff -u compare/prod-app-bot-keys.json compare/dev-app-bot-keys.json
```

### Step 4: Compare Security Groups

Compare group memberships:

```bash
# Count members
echo "Prod group members: $(jq 'length' compare/prod-group-members.json)"
echo "Dev group members: $(jq 'length' compare/dev-group-members.json)"

# Show differences
jq -r '.[] | .userPrincipalName' compare/prod-group-members.json | sort > compare/prod-members.txt
jq -r '.[] | .userPrincipalName' compare/dev-group-members.json | sort > compare/dev-members.txt

diff compare/prod-members.txt compare/dev-members.txt
```

Document findings:

- ✅ **Member count**: Should match or have intentional differences
- ✅ **Specific users**: Should be same roles/purposes
- ⚠️ **Test accounts**: Dev might have extra test users (acceptable)

### Step 5: Compare Webhook Subscriptions

Compare active subscriptions:

```bash
# Extract subscription details
jq '.[] | {resource, notificationUrl, expirationDateTime}' compare/prod-subscriptions.json > compare/prod-subs-summary.json
jq '.[] | {resource, notificationUrl, expirationDateTime}' compare/dev-subscriptions.json > compare/dev-subs-summary.json

# Show summary
echo "=== PROD SUBSCRIPTIONS ==="
cat compare/prod-subs-summary.json | jq '.'

echo "=== DEV SUBSCRIPTIONS ==="
cat compare/dev-subs-summary.json | jq '.'

# Compare
diff <(jq -r '.[] | .resource' compare/prod-subs-summary.json | sort) \
     <(jq -r '.[] | .resource' compare/dev-subs-summary.json | sort)
```

Document findings:

- ✅ **Resource types**: Should be identical (same meeting/transcript subscriptions)
- ✅ **Notification URLs**: Should differ (different API Gateway endpoints)
- ⚠️ **Expiration times**: Subscriptions expire at different times (acceptable)
- ❌ **Missing subscriptions**: Dev should have same resource subscriptions as prod

### Step 6: Compare Teams Admin Policies

Export policy assignments:

```powershell
# Connect to Teams PowerShell (for prod tenant)
Connect-MicrosoftTeams -TenantId $PROD_TENANT_ID

# Get policy assignments
Get-CsUserPolicyAssignment -PolicyType TeamsMeetingPolicy | ConvertTo-Json -Depth 3 > compare/prod-policy-assignment.json
Get-CsUserPolicyAssignment -PolicyType TeamsAppSetupPolicy | ConvertTo-Json -Depth 3 > compare/prod-appsetup-policy.json

# Disconnect and connect to dev
Disconnect-MicrosoftTeams
Connect-MicrosoftTeams -TenantId $DEV_TENANT_ID

Get-CsUserPolicyAssignment -PolicyType TeamsMeetingPolicy | ConvertTo-Json -Depth 3 > compare/dev-policy-assignment.json
Get-CsUserPolicyAssignment -PolicyType TeamsAppSetupPolicy | ConvertTo-Json -Depth 3 > compare/dev-appsetup-policy.json

# Compare policy names (not individual user assignments, but the policies themselves)
Disconnect-MicrosoftTeams
```

Document findings:

- ✅ **Policy names**: Should match (both using same corporate policy)
- ✅ **Policy settings**: Should be identical (same transcription rules, etc.)
- ⚠️ **Assignment scope**: Might differ (prod: all users vs dev: test group only) — accept if intentional

### Step 7: Compare Teams App Manifests

Compare the app manifests across environments:

```bash
# Extract key fields from manifests
jq '{id, name: .name.short, version, bots: .bots[].botId}' teams-app/manifest.json > compare/prod-manifest-keys.json
jq '{id, name: .name.short, version, bots: .bots[].botId}' teams-app/manifest-dev.json > compare/dev-manifest-keys.json

# Compare
diff compare/prod-manifest-keys.json compare/dev-manifest-keys.json
```

Document findings:

- ✅ **App ID**: Prod and dev should differ (different Azure AD app)
- ✅ **Bot ID**: Prod and dev should differ
- ✅ **Version**: Should be same (same codebase)
- ✅ **Permissions**: Should be identical

### Step 8: Compare Lambda/API Configuration

Compare compute and API configurations:

```bash
# Prod Lambda config
aws lambda get-function-configuration --function-name tmf-webhook-handler-prod --profile prod \
  --query '{Runtime, Handler, MemorySize, Timeout, EphemeralStorageSize}' > compare/prod-lambda-config.json

# Dev Lambda config
aws lambda get-function-configuration --function-name tmf-webhook-handler-dev --profile dev \
  --query '{Runtime, Handler, MemorySize, Timeout, EphemeralStorageSize}' > compare/dev-lambda-config.json

# Compare
diff compare/prod-lambda-config.json compare/dev-lambda-config.json
```

Document findings:

- ✅ **Runtime**: Should be identical (both Node.js 18)
- ✅ **Handler**: Should be identical
- ⚠️ **MemorySize/Timeout**: Might differ for testing (acceptable if dev has lower resources)

### Step 9: Generate Consistency Report

Create a markdown report summarizing all findings:

```markdown
# Teams Configuration Comparison Report

**Generated**: $(date)
**Environments**: Prod vs Dev

## Summary

- **Status**: ✅ Consistent / ⚠️ Minor Differences / ❌ Critical Issues

## Azure AD Apps

### Main Application

| Field           | Prod                  | Dev                         | Status                  |
| --------------- | --------------------- | --------------------------- | ----------------------- |
| Display Name    | Teams Meeting Fetcher | Teams Meeting Fetcher - Dev | ✅ OK (expected suffix) |
| API Permissions | [list]                | [list]                      | ✅ Identical            |
| Redirect URIs   | https://prod.com      | http://localhost:3000       | ✅ OK (expected)        |

### Bot Application

| Field        | Prod              | Dev                     | Status |
| ------------ | ----------------- | ----------------------- | ------ |
| Display Name | TMF Bot Framework | TMF Bot Framework - Dev | ✅ OK  |
| [...]        | [...]             | [...]                   | [...]  |

## Security Groups

| Metric        | Prod | Dev | Status                        |
| ------------- | ---- | --- | ----------------------------- |
| Member Count  | 45   | 12  | ⚠️ Dev is subset (acceptable) |
| Test Accounts | 0    | 5   | ✅ OK (dev-only)              |

## Webhook Subscriptions

| Resource                             | Prod      | Dev       | Status |
| ------------------------------------ | --------- | --------- | ------ |
| /communications/callRecords          | ✅ Active | ✅ Active | ✅ OK  |
| /teams/onlineMeetings/[]/transcripts | ✅ Active | ✅ Active | ✅ OK  |

## Teams Admin Policies

| Policy                | Prod                | Dev                 | Status |
| --------------------- | ------------------- | ------------------- | ------ |
| Meeting Policy        | Corporate Policy v2 | Corporate Policy v2 | ✅ OK  |
| Transcription Enabled | Yes                 | Yes                 | ✅ OK  |

## Lambda Configuration

| Setting | Prod       | Dev        | Status                    |
| ------- | ---------- | ---------- | ------------------------- |
| Runtime | Node.js 18 | Node.js 18 | ✅ OK                     |
| Memory  | 512 MB     | 256 MB     | ⚠️ Dev lower (acceptable) |

## Action Items

- [ ] None — configurations are consistent
- [ ] [If issues found]: ...

## Last Validated

$(date) — All environments aligned
```

### Step 10: Store Report

```bash
# Calculate diffs
git add compare/
git commit -m "docs: teams config comparison report (prod vs dev)"

# Or note in inventory
echo "Last comparison: $(date)" >> inventory/teams-config-inventory.md
```

### Rules

- **Different app IDs are expected** — prod and dev should use different Azure AD apps
- **Different user bases are acceptable** — dev might have fewer users or test accounts
- **Resource types should match** — same subscriptions across environments
- **Policy settings should match** — both environments should have same meeting rules
- **Infrastructure specs can differ** — dev might use less memory/timeout for cost savings
