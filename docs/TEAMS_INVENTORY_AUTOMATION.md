# Teams Configuration Inventory Automation

**Quick Start**: Run `python scripts/teams/inventory-teams-config.py` to audit and export your complete Teams bot setup.

---

## Overview

This guide explains how to use the inventory automation to create a complete, repeatable documentation of your Teams bot configuration.

**What Gets Exported**:

- ✅ Azure AD app registrations
- ✅ API permissions
- ✅ Service principals
- ✅ Security group memberships
- ✅ Teams app manifest
- ✅ Lambda/API configuration
- ⚠️ Teams admin policies (manual export via PowerShell)
- ⚠️ Webhook subscriptions (requires running subscription checks)

---

## Prerequisites

Before running the inventory:

```bash
# 1. Update .env.local with your actual values
cat .env.local | grep -E "TENANT|CLIENT|GROUP|ENDPOINT"

# Expected output (replace placeholders):
# GRAPH_TENANT_ID=<your-tenant-id>
# GRAPH_CLIENT_ID=<your-app-id>
# ENTRA_GROUP_ID=<your-group-id>
# AWS_WEBHOOK_ENDPOINT=<your-webhook-url>

# 2. Ensure Azure CLI is authenticated
az account show

# 3. Install Python dependencies
pip install python-dotenv

# 4. Understand your Teams setup (optional)
# Review: .github/prompts/bootstrap-teams-config.prompt.md
```

---

## Running the Inventory

### Option 1: Full Automated Inventory

```bash
# Run full audit
python scripts/teams/inventory-teams-config.py

# Output: inventory/teams-config-inventory.md + exported JSONs
```

This will:

1. ✅ Fetch Azure AD app registrations
2. ✅ Export API permissions
3. ✅ List security group members
4. ✅ Export Teams app manifest
5. ✅ List Lambda functions
6. 📄 Generate comprehensive markdown documentation
7. 📦 Create zip archive of all exports

### Option 2: Manual Step-by-Step

If automated script doesn't work, follow [inventory-teams-config.prompt.md](.github/prompts/inventory-teams-config.prompt.md):

```bash
# Step 1: Audit Teams Admin Policies (PowerShell)
powershell
Connect-MicrosoftTeams
Get-CsTeamsAppSetupPolicy | ConvertTo-Json | Out-File -Path "inventory/teams-app-setup-policy.json"
exit

# Step 2: Audit Security Groups
az ad group show --group-object-id $ENTRA_GROUP_ID --output json > inventory/entra-group-details.json

# Step 3: Audit subscriptions
python scripts/graph/check_latest_webhook.py

# Continue with remaining steps in prompt...
```

---

## Exported Files

After running inventory, you'll have:

```
inventory/
├── teams-config-inventory.md          # Main documentation (read this!)
├── app-registration-main.json         # Azure AD app details
├── app-permissions-main.json          # API permissions
├── sp-main.json                       # Service principal
├── entra-group-details.json           # Group metadata
├── entra-group-members.json           # Group member list
├── teams-app-manifest.json            # Teams app config
├── lambda-functions.json              # AWS Lambda list
├── teams-app-setup-policy.json        # (manual export) Teams policy
├── teams-meeting-policy.json          # (manual export) Meeting policy
├── teams-policy-assignments.json      # (manual export) Policy assignments
└── teams-config-inventory-YYYYMMDD_HHMMSS.zip  # Archive for backup
```

---

## Understanding the Inventory Output

### teams-config-inventory.md

This is the **primary documentation** for your Teams bot setup. It includes:

1. **Quick Reference Table** — All important IDs and endpoints
2. **Azure AD App Registrations** — App IDs, permissions, creation date
3. **Security Groups** — Group ID and member list
4. **Teams App Configuration** — Bot IDs, valid domains, permissions
5. **Webhook Configuration** — Notification endpoint
6. **Lambda/API Configuration** — Function names, endpoints
7. **Teams Admin Policies** — Policy assignments (fill in manually)
8. **Reproduction Steps** — Complete walkthrough to recreate setup
9. **Validation Checklist** — Verify all components are exported

---

## Using Inventory to Reproduce Setup

### Scenario 1: New Developer Joining Project

```bash
# Give new developer this checklist:

1. Read inventory/teams-config-inventory.md
2. Follow "How to Reproduce This Setup" section:
   a. Create Azure AD apps (use inventory IDs as reference)
   b. Configure permissions (see app-permissions-main.json)
   c. Create security group (see entra-group-members.json for model)
   d. Create Teams policies (see teams-app-setup-policy.json)
   e. Deploy Lambda (see lambda-functions.json)
   f. Create webhook subscription
   g. Upload Teams app

3. Compare your setup against inventory using:
   python scripts/graph/01-verify-setup.py
```

### Scenario 2: Disaster Recovery - Recreate Entire Setup

```bash
# Use inventory as reference manual:

# 1. Restore Azure AD apps from inventory
app_id=$(cat inventory/app-registration-main.json | jq -r '.appId')

# 2. Restore security group
group_id=$(cat inventory/entra-group-details.json | jq -r '.id')
# Recreate members from entra-group-members.json

# 3. Restore Teams policies
# Open inventory/teams-app-setup-policy.json
# Manually recreate using Teams PowerShell (policies cannot be exported/imported directly)

# 4. Restore Teams app
# Use inventory/teams-app-manifest.json as source for manifest.json

# 5. Restore webhook
# Use inventory/subscriptions.json to recreate subscriptions
```

### Scenario 3: Audit Changes Over Time

```bash
# Compare inventory from different dates:

git log --oneline inventory/teams-config-inventory.md
# Output:
# abc1234 docs: update Teams inventory after policy change
# def5678 docs: export Teams bot configuration inventory

# View differences
git diff HEAD~1 inventory/teams-config-inventory.md

# This shows what changed:
# - Users added/removed from group
# - Policies modified
# - App permissions updated
# - Webhook subscriptions changed
```

---

## Keeping Inventory Current

### After Any Teams Configuration Change

```bash
# 1. Run inventory audit again
python scripts/teams/inventory-teams-config.py

# 2. Review changes
git diff inventory/teams-config-inventory.md

# 3. Commit with descriptive message
git add inventory/
git commit -m "docs: update Teams inventory after [describe change]"
git push
```

### Recommended Update Schedule

- **Weekly**: Automated version control check (GitHub Actions)
- **After Any Change**: Manual run + commit
- **Monthly**: Full review and validation

---

## Using Inventory in GitHub Actions

### Scheduled Inventory Update (Optional Workflow)

```yaml
name: Weekly Inventory Update

on:
  schedule:
    - cron: '0 8 * * 1' # Monday 8 AM UTC

jobs:
  inventory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0 # Full history

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install python-dotenv azure-cli
          az login --service-principal \
            -u ${{ secrets.AZURE_CLIENT_ID }} \
            -p ${{ secrets.AZURE_CLIENT_SECRET }} \
            --tenant ${{ secrets.AZURE_TENANT_ID }}

      - name: Run inventory
        env:
          GRAPH_TENANT_ID: ${{ secrets.GRAPH_TENANT_ID }}
          GRAPH_CLIENT_ID: ${{ secrets.GRAPH_CLIENT_ID }}
          ENTRA_GROUP_ID: ${{ secrets.ENTRA_GROUP_ID }}
          AWS_WEBHOOK_ENDPOINT: ${{ secrets.AWS_WEBHOOK_ENDPOINT }}
        run: python scripts/teams/inventory-teams-config.py

      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add inventory/
          git commit -m "chore: automated Teams inventory update" || true
          git push
```

### Scheduled Inventory Validation (Drift Detection)

Combine `inventory-teams-config.py` with `compare-teams-config.prompt.md` to detect drift:

```bash
# Script to run weekly:
python scripts/teams/inventory-teams-config.py  # Current state
python -c "from scripts.teams import compare; compare.validate_consistency()"  # Check for drift
```

---

## Troubleshooting Inventory Export

### "Command failed: Insufficient permissions"

```bash
# Verify Azure AD permissions
az ad app show --id <GRAPH_CLIENT_ID>

# If failed, you need:
# - Application Administrator role in Azure AD
# - Access to the application's tenant
# - Read permissions on security groups
```

### "Invalid .env.local values"

```bash
# Verify each required value
echo "GRAPH_TENANT_ID=${GRAPH_TENANT_ID:-NOT SET}"
echo "GRAPH_CLIENT_ID=${GRAPH_CLIENT_ID:-NOT SET}"
echo "ENTRA_GROUP_ID=${ENTRA_GROUP_ID:-NOT SET}"
echo "AWS_WEBHOOK_ENDPOINT=${AWS_WEBHOOK_ENDPOINT:-NOT SET}"

# If not set, update .env.local manually
cat >> .env.local << 'EOF'
GRAPH_TENANT_ID=<your-tenant-id>
GRAPH_CLIENT_ID=<your-app-id>
ENTRA_GROUP_ID=<your-group-id>
AWS_WEBHOOK_ENDPOINT=<your-webhook-url>
EOF
```

### "No files exported to inventory/"

```bash
# Create inventory directory
mkdir -p inventory/

# Check if Python script ran successfully
python scripts/teams/inventory-teams-config.py -v

# Verify Azure CLI works
az account show
```

### "JSON parsing error"

```bash
# Some outputs might not be valid JSON
# Check raw command output:
az ad group member list --group-object-id <ID> --output json | head -20

# If malformed, the script will skip and continue
# Check logs in terminal output for warnings
```

---

## Best Practices

### 1. Version Control Your Inventory

```bash
# Keep inventory in git (but not secrets)
git add inventory/teams-config-inventory.md
git commit -m "docs: export Teams configuration"

# Exclude secrets from version control
# .gitignore should have:
echo ".env.local" >> .gitignore
echo "*.key" >> .gitignore
```

### 2. Protect Sensitive Data

The inventory script **never exports**:

- ❌ Application secrets/passwords
- ❌ Access keys
- ❌ Webhook authentication tokens
- ❌ User email addresses (only UPNs)

But it **does export**:

- ✅ App IDs and object IDs (needed for reproduction)
- ✅ Webhook endpoint URL (needed for validation)
- ✅ User principal names (UPN format, like user@contoso.com)

### 3. Keep Inventory Updated

Stale inventory causes issues. Update whenever:

- Users added/removed from security group
- Teams app is updated
- Policies are modified
- Lambda functions change
- Webhook subscriptions are renewed

---

## Next Steps After Inventory

1. **Document Current State**: Commit `inventory/teams-config-inventory.md`
2. **Enable Drift Detection**: Use `compare-teams-config.prompt.md` for validation
3. **Schedule Updates**: Set up GitHub Actions to run weekly
4. **Test Reproduction**: Follow "How to Reproduce" in inventory to verify steps are accurate
5. **Distribute Documentation**: Share inventory with team for onboarding

---

## See Also

- [bootstrap-teams-config.prompt.md](.github/prompts/bootstrap-teams-config.prompt.md) — Initial setup (all steps)
- [inventory-teams-config.prompt.md](.github/prompts/inventory-teams-config.prompt.md) — Manual audit steps
- [compare-teams-config.prompt.md](.github/prompts/compare-teams-config.prompt.md) — Drift detection between environments
- [validate-teams-config-repeatability.prompt.md](.github/prompts/validate-teams-config-repeatability.prompt.md) — Test reproduction steps

---

## Command Reference

```bash
# Run full inventory
python scripts/teams/inventory-teams-config.py

# View inventory documentation
cat inventory/teams-config-inventory.md

# Check what's exported
ls -lah inventory/

# Create new archive
zip -r teams-config-inventory-backup-$(date +%Y%m%d).zip inventory/

# Compare to previous version
git diff HEAD~1 inventory/teams-config-inventory.md

# Remove inventory (when starting fresh)
rm -rf inventory/
```

---

**Last Updated**: February 16, 2026
