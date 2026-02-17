# Validate Teams Config Repeatability — Step-by-Step Reproduction

## Purpose

Verify that your Teams configuration is fully documented and repeatable. Follow the step-by-step guide to recreate the setup from scratch in a new tenant or environment.

## Instructions

### Step 1: Prepare Test Environment

Set up a fresh environment to test repeatability:

```bash
# Create a new directory structure or a test tenant
# For testing locally, create a new .env file
cp .env.local .env.local.test

# Update placeholders to point to a test/staging environment
# Edit .env.local.test and set:
# GRAPH_TENANT_ID=<test-tenant-id>
# GRAPH_CLIENT_ID=<test-app-id>
# BOT_APP_ID=<test-bot-id>
# (These should be test/staging registrations, not prod)

export TEST_ENV_FILE=.env.local.test
```

### Step 2: Verify Azure AD App Registration Steps

Follow the documented process to recreate the Azure AD apps:

```bash
# From inventory/teams-config-inventory.md, extract the required API permissions
# For each permission listed, run:

az ad app create \
  --display-name "Teams Meeting Fetcher (TEST)" \
  --sign-in-audience AzureADMultiTenant \
  --web-redirect-uris "http://localhost:3000"

# Capture the app ID
TEST_APP_ID=$(az ad app list --display-name "Teams Meeting Fetcher (TEST)" --query "[0].appId" -o tsv)

# Add API permissions (based on inventory)
az ad app permission add --id $TEST_APP_ID --api 00000002-0000-0000-c000-000000000000 --api-permissions 86cc644c-6a59-43b5-b233-1ca0027f446f=Role

# Create bot app following the same pattern
# Document each step
```

Verify:

- ✅ App created with correct display name
- ✅ All required API permissions added
- ✅ Admin consent granted
- ✅ Client secrets generated and stored securely
- ✅ App IDs match inventory

### Step 3: Verify Security Group Reproduction

Recreate the security group:

```bash
# From inventory/entra-group-members.json, extract the group info
# Create test group
az ad group create \
  --display-name "Teams Meeting Fetcher - Test Access" \
  --mail-nickname tmf-test-access

TEST_GROUP_ID=$(az ad group show --group-object-id tmf-test-access --query "objectId" -o tsv)

# Add members from inventory
# For each member in entra-group-members.json:
az ad group member add --group-object-id $TEST_GROUP_ID --member-id <member-object-id>
```

Verify:

- ✅ Group created with correct name
- ✅ All members added (compare count with inventory)
- ✅ Group is accessible and query-able via Azure AD

### Step 4: Verify Teams Admin Policy Steps

Based on inventory, recreate or verify policy assignments:

```powershell
Connect-MicrosoftTeams

# If policies were custom-created, recreate them:
# (Example - adjust based on your inventory)
Set-CsTeamsMeetingPolicy -Identity <policy-id> \
  -TranscriptionEnabled $true \
  -AllowRecording $true

# Verify the policy is assigned to the test group
Get-CsUserPolicyAssignment -PolicyType TeamsMeetingPolicy | Where-Object GroupId -eq $TEST_GROUP_ID
```

Verify:

- ✅ Policy exists with same settings as inventory
- ✅ Policy is assigned to the test group
- ✅ Settings match documentation (transcription enabled, etc.)

### Step 5: Verify Teams App Manifest Reproduction

Test the Teams app manifest against the test environment:

```bash
# Use inventory/teams-app-config.json as the template
# Update the manifest IDs:
# - id: should match TEST_APP_ID
# - bots[0].botId: should match TEST_BOT_APP_ID

jq --arg app_id "$TEST_APP_ID" \
   --arg bot_id "$TEST_BOT_APP_ID" \
   '.id = $app_id | .bots[0].botId = $bot_id' \
   inventory/teams-app-config.json > teams-app/manifest-test.json

# Validate the manifest
jq . teams-app/manifest-test.json > /dev/null && echo "✅ Valid JSON"

# Check required fields
jq 'has("id") and has("name") and has("bots") and has("version")' teams-app/manifest-test.json
```

Verify:

- ✅ Manifest JSON is valid
- ✅ App ID matches test app registration
- ✅ Bot ID matches test bot app
- ✅ Valid domains include the test webhook URL

### Step 6: Verify Lambda/API Deployment Steps

Recreate the infrastructure for the test environment:

```bash
# Use iac/aws/terraform.tfvars as template
# Create test version: iac/aws/terraform.tfvars.test

cp iac/aws/terraform.tfvars iac/aws/terraform.tfvars.test

# Update with test environment settings
# (Change bucket names, function names, etc. to have -test suffix)

# Plan infrastructure for test environment
cd iac/aws
terraform plan -var-file=terraform.tfvars.test -out=tfplan.test

# Review plan (don't apply yet, just validate)
echo "Terraform plan is valid ✅"
cd ../..
```

Verify:

- ✅ Terraform plan succeeds without errors
- ✅ All expected resources are planned (API Gateway, Lambda, S3, etc.)
- ✅ Variables match values from inventory

### Step 7: Verify Webhook Subscription Steps

Based on inventory, document the subscription creation process:

```bash
# From inventory/subscriptions.json, extract resource and webhook URL
# Recreate the subscription:

python scripts/graph/02-create-webhook-subscription.py \
  --resource "/communications/callRecords" \
  --webhook-url "https://<test-api-gateway-url>/webhook"

# Verify subscription was created
python scripts/graph/check-subscriptions.py

# Expected output should match inventory:
# Resource: /communications/callRecords
# Notification URL: matches TEST_WEBHOOK_ENDPOINT
# State: active
```

Verify:

- ✅ Subscription created successfully
- ✅ Notification URL matches test environment
- ✅ Subscription is active (not in validation or expired state)
- ✅ Expiration is 29+ hours away (subscriptions are 43,200 seconds by default)

### Step 8: Validate End-to-End Repeatability

Run the full setup procedure one more time:

```bash
# Clean up test environment
# Delete test app, group, subscriptions, Lambda

# Recreate from scratch using inventory documentation
# Step by step:
# 1. Create Azure AD apps
# 2. Configure API permissions
# 3. Create security group
# 4. Assign policies
# 5. Deploy infrastructure
# 6. Create subscriptions
# 7. Verify everything works

# Run verification script
python scripts/graph/01-verify-setup.py
```

Verify:

- ✅ All steps completed without manual intervention
- ✅ Verification script reports success
- ✅ No missing configuration steps

### Step 9: Document Findings & Update Inventory

If issues were found during repeatability testing:

1. **Missing step?** Add it to the inventory markdown with clear instructions
2. **Outdated setting?** Update the inventory with current values
3. **Unclear procedure?** Add more detail or break into smaller steps
4. **New dependency?** Document it in the prerequisites section

Update inventory:

```bash
# After addressing findings
git add inventory/teams-config-inventory.md
git commit -m "docs: update teams config inventory with repeatability findings"
```

### Step 10: Create Repeatability Checklist

Generate a final checklist for future reproductions:

```markdown
# Teams Configuration Reproduction Checklist

- [ ] All app registrations created with correct display names
- [ ] All API permissions granted and admin-consented
- [ ] Client secrets/certificates generated
- [ ] Security group created and members added
- [ ] Teams admin policies applied to group
- [ ] Lambda function deployed with correct environment variables
- [ ] API Gateway configured with correct authorizer
- [ ] Webhook URL matches API Gateway endpoint in Teams app
- [ ] Teams app manifest verified (IDs match, valid domains set)
- [ ] Webhook subscriptions created and active
- [ ] Graph API verification script passes
- [ ] End-to-end test successful (meeting events received)

Time to complete: approximately X hours
```

### Rules

- **Test in an isolated environment first** — never reproduce in production without testing.
- **Document each step** — if you need to manually do something, add it to the inventory.
- **Automate where possible** — use CLI commands and scripts, not UI clicks.
- **Verify credentials** — always check tenant ID and app IDs before proceeding.
- **Keep timestamps** — track when the setup was last validated as reproducible.
