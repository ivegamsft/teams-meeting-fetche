# Teams Inventory Automation — Reference Guide

This document connects the manual [inventory-teams-config.prompt.md](.github/prompts/inventory-teams-config.prompt.md) with the automated Python/PowerShell scripts.

---

## Quick Start

### Windows Users

```powershell
# Run inventory with pre-flight checks
.\scripts\teams\run-inventory.ps1

# Check only, don't run
.\scripts\teams\run-inventory.ps1 -CheckOnly

# Archive existing inventory
.\scripts\teams\run-inventory.ps1 -ArchiveOnly
```

### macOS/Linux Users

```bash
# Run inventory with pre-flight checks
python scripts/teams/run-inventory.py

# Check only
python scripts/teams/run-inventory.py --check-only

# Archive existing
python scripts/teams/run-inventory.py --archive-only
```

---

## Architecture

```
User Request
    ↓
.github/prompts/inventory-teams-config.prompt.md
    ↓
    ├─→ Manual Execution? → Follow steps in prompt
    │
    └─→ Automated? → Use one of:
        ├─ scripts/teams/inventory-teams-config.py (core logic)
        ├─ scripts/teams/run-inventory.ps1 (Windows wrapper)
        └─ scripts/teams/run-inventory.py (wrapper with checks)

    ↓
    Outputs:
    ├─ inventory/teams-config-inventory.md (main documentation)
    ├─ inventory/*.json (exported configurations)
    ├─ inventory/*.csv (exported data)
    └─ inventory/*.zip (backup archive)
```

---

## What Each Script Does

### 1. inventory-teams-config.py

**Core automation logic**

Performs all audit steps:

- Azure AD app registrations
- API permissions
- Security groups
- Teams app manifest
- Lambda/API configuration
- Generates markdown documentation
- Creates zip archive

**Handles missing values gracefully** — Skips sections if env vars aren't configured, continues with what it can export.

### 2. run-inventory.ps1 (Windows)

**Pre-flight check wrapper for PowerShell**

Before running audit:

1. Checks if Python 3.8+ installed
2. Checks if Azure CLI installed
3. Checks if .env.local exists
4. Validates all required env vars are set
5. Checks if inventory script exists

Includes colored output for better readability and prompts before proceeding if checks fail.

### 3. run-inventory.py (Unix/Windows)

**Pre-flight check wrapper for Python**

Same checks as PowerShell but portable to all platforms. Uses Python's `subprocess` to run the core script.

---

## Mapping: Prompt → Scripts

| Prompt Step                   | Automated By                       | Location                         |
| ----------------------------- | ---------------------------------- | -------------------------------- |
| Step 1: Teams Admin Policies  | **Manual** (Teams PowerShell)      | Script shows command template    |
| Step 2: Audit Security Groups | inventory-teams-config.py          | Uses `az ad group member list`   |
| Step 3: Azure AD Apps         | inventory-teams-config.py          | Uses `az ad app show`            |
| Step 4: Webhook Subscriptions | inventory-teams-config.py          | Calls `check_latest_webhook.py`  |
| Step 5: Teams App Manifest    | inventory-teams-config.py          | Reads `teams-app/manifest.json`  |
| Step 6: Lambda/API Config     | inventory-teams-config.py          | Uses `aws lambda list-functions` |
| Step 7: Generate Markdown     | inventory-teams-config.py          | Builds teams-config-inventory.md |
| Step 8: Export & Archive      | inventory-teams-config.py          | Creates .zip file                |
| Step 9: Validation Checklist  | run-inventory.ps1/run-inventory.py | Shows summary of exports         |

---

## Detailed Script Behavior

### inventory-teams-config.py

**Entry Point**: `python scripts/teams/inventory-teams-config.py`

**Flow**:

1. Load .env.local environment variables
2. Create `inventory/` directory if missing
3. For each audit step:
   a. Check if required env vars are set
   b. Run Azure CLI / AWS CLI command
   c. Save output to `inventory/` directory
   d. Print status (✓ success, ⚠️ warning, ❌ error)
4. Parse exported JSONs
5. Generate `teams-config-inventory.md` with:
   - Quick reference table
   - App registration details
   - Security group members
   - Teams app config
   - Lambda/API info
   - Reproduction steps
   - Validation checklist
6. Create zip archive
7. Print summary and next steps

**Error Handling**:

- ✅ If env var missing → Skip that section, continue with others
- ✅ If Azure CLI fails → Print warning, continue
- ✅ If export fails → Still generate markdown with note "Not yet exported"
- ✅ Archives everything exported, even if some steps failed

### run-inventory.ps1 (Windows)

**Entry Point**: `.\scripts\teams\run-inventory.ps1`

**Parameters**:

- `-CheckOnly` — Only check prerequisites, don't run audit
- `-SkipChecks` — Skip prerequisite checks
- `-ArchiveOnly` — Only create archive of existing inventory

**Flow**:

1. Load environment variables from command output
2. Test Python, Azure CLI, files
3. Test each required env var
4. Prompt user if checks fail
5. Call the Python script
6. Create zip archive
7. Show export summary
8. Display next steps

**Output**:

- Colored console output (Green ✓, Red ✗, Yellow ⚠️)
- Prints prerequisites as they're checked
- Shows env var values (masked for security)
- Lists exported files with sizes

### run-inventory.py (Unix/Windows)

**Entry Point**: `python scripts/teams/run-inventory.py`

**Parameters**:

- `--check-only` — Only check prerequisites
- `--skip-checks` — Skip prerequisite checks
- `--archive-only` — Only archive existing inventory

**Flow**:

1. Same as PowerShell but using Python
2. Runs subprocess calls to test commands
3. Portable to macOS, Linux, Windows

---

## Example Workflows

### Workflow 1: New Developer Onboarding

```bash
# 1. Developer joins team, gets .env.local from SecureOps
# 2. Developer clones repo
cd teams-meeting-fetcher

# 3. Update .env.local with actual values (from team documentation)
nano .env.local  # Edit real values, not placeholders

# 4. Run inventory to understand current setup
python scripts/teams/run-inventory.py

# 5. Read generated documentation
cat inventory/teams-config-inventory.md

# 6. Follow "How to Reproduce" section to understand setup
# 7. Compare against actual environment
python scripts/graph/01-verify-setup.py
```

### Workflow 2: Disaster Recovery

```bash
# 1. All Teams bot configuration lost
# 2. But we have inventory backup in git

# 3. Restore from git history
git log --oneline -- inventory/teams-config-inventory.md
git checkout <commit-hash> -- inventory/

# 4. Read inventory to understand what was configured
cat inventory/teams-config-inventory.md

# 5. Follow "How to Reproduce" section to recreate:
# - Create apps
# - Assign policies
# - Deploy Lambda
# - Create subscriptions
```

### Workflow 3: Configuration Drift Detection

```bash
# 1. Team suspects Teams config has drifted
# 2. Re-run inventory to get current state

python scripts/teams/run-inventory.py

# 3. Compare against previous version
git diff HEAD -- inventory/teams-config-inventory.md

# 4. Identify what changed:
# - App permissions added/removed?
# - Group members added/removed?
# - Policies changed?

# 5. Take corrective action
# 6. Commit updated inventory
git add inventory/
git commit -m "docs: reconcile Teams config drift"
```

### Workflow 4: Regular Audit (Monthly)

```bash
# 1. Scheduled job or manual run
python scripts/teams/run-inventory.py

# 2. Review what changed
git diff HEAD~1 -- inventory/teams-config-inventory.md

# 3. If changes expected (team added users, policies updated):
git add inventory/
git commit -m "docs: monthly Teams inventory update"

# 4. If unexpected changes (drift):
# Alert team that configuration changed
# Review changes manually
# Update actual config back to desired state
```

---

## Understanding the Output

### Console Output During Run

```
================================================================================
TEAMS BOT CONFIGURATION INVENTORY
================================================================================

Timestamp: 2026-02-16T14:30:45.123456
Tenant ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Environment: tmf-dev

================================================================================
STEP 1: AUDIT AZURE AD APP REGISTRATIONS
================================================================================

📋 Fetch Main App Registration
  ✓ Exported to: app-registration-main.json
  ✓ Valid JSON

📋 Fetch API Permissions (Main App)
  ✓ Exported to: app-permissions-main.json
  ✓ Valid JSON

... (more steps)

================================================================================
STEP 7: GENERATE INVENTORY MARKDOWN
================================================================================

✓ Inventory markdown created: inventory/teams-config-inventory.md

================================================================================
INVENTORY COMPLETE
================================================================================

📂 Exported Files (in inventory/):
  ✓ app-registration-main.json
  ✓ app-permissions-main.json
  ✓ entra-group-details.json
  ... (more files)

📄 Main Documentation: inventory/teams-config-inventory.md

⚠️  NEXT STEPS:
1. Review inventory/teams-config-inventory.md
2. Fill in Teams PowerShell sections manually
3. Commit to version control
4. Use inventory for environment reproducibility
```

### Generated Markdown Example

```markdown
# Teams Bot Configuration Inventory

**Generated**: 2026-02-16 14:30:45
**Tenant ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
**Environment**: tmf-dev

## 📋 Quick Reference

| Item                 | Value                                  |
| -------------------- | -------------------------------------- |
| **Tenant ID**        | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| **Graph Client ID**  | `yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy` |
| **Entra Group ID**   | `zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz` |
| **Webhook Endpoint** | `https://api.example.com/webhook`      |
| **Created**          | 2026-02-16T14:30:45.123456             |

...

## How to Reproduce This Setup

### Prerequisites

1. Azure AD Tenant with admin access
2. AWS Account with IAM permissions
3. Teams Admin rights

### Steps

1. Create Azure AD Applications
2. Configure API Permissions
3. Create Security Group
   ... (continues with full reproduction steps)
```

---

## Troubleshooting

### "Script not found" Error

```bash
# Verify scripts exist
ls -la scripts/teams/inventory-teams-config.py
ls -la scripts/teams/run-inventory.ps1
ls -la scripts/teams/run-inventory.py

# If missing, you may need to create them
# Copy from this guide
```

### "Permission denied" on PowerShell Script

```powershell
# Windows: Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run
.\scripts\teams\run-inventory.ps1
```

### "Azure CLI not found"

```bash
# Install Azure CLI
# macOS:
brew install azure-cli

# Windows:
# Download from https://aka.ms/azurecli
# Or: winget install Microsoft.AzureCLI

# Verify:
az --version
```

### "Python not found"

```bash
# Install Python 3.8+
# From https://www.python.org/

# Verify:
python --version
# Should show 3.8 or higher
```

### ".env.local not found"

```bash
# Create from template
cp .env.example .env.local
# Edit with actual values
nano .env.local
```

### "No files exported to inventory/"

```bash
# Possible causes:
# 1. .env.local has placeholder values (still exports what it can)
# 2. .env.local doesn't exist (creates but skips exports)
# 3. Azure CLI not authenticated (run: az login)

# Debug:
python scripts/teams/run-inventory.py --skip-checks
# This will show detailed error messages from each command
```

---

## Integration with CI/CD

### GitHub Actions: Weekly Inventory Update

```yaml
name: Weekly Configuration Inventory

on:
  schedule:
    - cron: '0 8 * * 1' # Monday 8 AM UTC
  workflow_dispatch:

jobs:
  inventory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install python-dotenv
          az --version

      - name: Create .env.local from secrets
        run: |
          cat > .env.local << 'EOF'
          GRAPH_TENANT_ID=${{ secrets.GRAPH_TENANT_ID }}
          GRAPH_CLIENT_ID=${{ secrets.GRAPH_CLIENT_ID }}
          ENTRA_GROUP_ID=${{ secrets.ENTRA_GROUP_ID }}
          AWS_WEBHOOK_ENDPOINT=${{ secrets.AWS_WEBHOOK_ENDPOINT }}
          EOF

      - name: Run inventory
        run: python scripts/teams/run-inventory.py

      - name: Commit changes
        run: |
          if [[ -n $(git status inventory/ -s) ]]; then
            git config user.name "GitHub Actions"
            git config user.email "actions@github.com"
            git add inventory/
            git commit -m "chore: automated Teams inventory update"
            git push
          fi
```

---

## See Also

- **Prompt Version**: [.github/prompts/inventory-teams-config.prompt.md](.github/prompts/inventory-teams-config.prompt.md)
- **Automation Guide**: [docs/TEAMS_INVENTORY_AUTOMATION.md](./TEAMS_INVENTORY_AUTOMATION.md)
- **Validation**: [.github/prompts/validate-teams-config-repeatability.prompt.md](.github/prompts/validate-teams-config-repeatability.prompt.md)
- **Drift Detection**: [.github/prompts/compare-teams-config.prompt.md](.github/prompts/compare-teams-config.prompt.md)

---

**Version**: 1.0  
**Last Updated**: February 16, 2026
