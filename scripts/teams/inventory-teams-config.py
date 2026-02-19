#!/usr/bin/env python3
"""
Inventory Teams Bot Configuration

Audits and documents:
- Azure AD app registrations
- Teams admin policies
- Security groups and memberships
- Webhook subscriptions
- Teams app manifest
- Lambda/API configuration

Export: teams-config-inventory.md
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env.local"
load_dotenv(ENV_FILE)

TENANT_ID = os.getenv("GRAPH_TENANT_ID")
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID")
BOT_APP_ID = os.getenv("GRAPH_CLIENT_ID")  # Same as graph client in this setup
ENTRA_GROUP_ID = os.getenv("ENTRA_GROUP_ID")
AWS_WEBHOOK_ENDPOINT = os.getenv("AWS_WEBHOOK_ENDPOINT")
AWS_PROFILE = os.getenv("AWS_PROFILE", "tmf-dev")
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


def infer_aws_region(endpoint):
    if not endpoint:
        return None
    try:
        host = endpoint.split("/")[2]
        parts = host.split(".")
        if "execute-api" in parts:
            idx = parts.index("execute-api")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    except Exception:
        return None
    return None


if not AWS_REGION:
    AWS_REGION = infer_aws_region(AWS_WEBHOOK_ENDPOINT) or "us-east-1"

INVENTORY_DIR = REPO_ROOT / "inventory"
INVENTORY_DIR.mkdir(exist_ok=True)

LOGS_DIR = INVENTORY_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("TEAMS BOT CONFIGURATION INVENTORY")
print("=" * 80)
print(f"\nTimestamp: {datetime.now().isoformat()}")
print(f"Tenant ID: {TENANT_ID}")
print(f"Environment: {AWS_PROFILE}")

# ============================================================================
# Helper Functions
# ============================================================================

def run_command(cmd, description, output_file=None):
    """Run CLI command and optionally save output"""
    print(f"\n[INFO] {description}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"  [WARN] Command failed: {result.stderr[:200]}")
            return None
        
        if output_file and result.stdout:
            output_path = LOGS_DIR / output_file
            output_path.write_text(result.stdout, encoding="utf-8")
            print(f"  [OK] Exported to: logs/{output_file}")
            try:
                # Validate JSON if applicable
                if output_file.endswith('.json'):
                    json.loads(result.stdout)
                    print(f"  [OK] Valid JSON")
            except:
                pass
        
        return result.stdout
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

# ============================================================================
# Step 1: Audit Azure AD App Registrations
# ============================================================================

print("\n" + "=" * 80)
print("STEP 1: AUDIT AZURE AD APP REGISTRATIONS")
print("=" * 80)

if not GRAPH_CLIENT_ID or GRAPH_CLIENT_ID == "<REPLACE_ME>":
    print("[WARN] GRAPH_CLIENT_ID not configured in .env.local")
    print("  Skipping Azure AD audit. Configure .env.local first.")
else:
    run_command(
        f'az ad app show --id {GRAPH_CLIENT_ID} --output json',
        "Fetch Main App Registration",
        "app-registration-main.json"
    )
    
    run_command(
        f'az ad app permission list --id {GRAPH_CLIENT_ID} --output json',
        "Fetch API Permissions (Main App)",
        "app-permissions-main.json"
    )
    
    run_command(
        f'az ad sp show --id {GRAPH_CLIENT_ID} --output json',
        "Fetch Service Principal (Main App)",
        "sp-main.json"
    )

# ============================================================================
# Step 2: Audit Security Groups
# ============================================================================

print("\n" + "=" * 80)
print("STEP 2: AUDIT SECURITY GROUPS")
print("=" * 80)

if not ENTRA_GROUP_ID or ENTRA_GROUP_ID == "<REPLACE_ME>":
    print("[WARN] ENTRA_GROUP_ID not configured in .env.local")
    print("  Skipping security group audit. Configure .env.local first.")
else:
    run_command(
        f'az ad group show --group {ENTRA_GROUP_ID} --output json',
        "Fetch Security Group Details",
        "entra-group-details.json"
    )
    
    run_command(
        f'az ad group member list --group {ENTRA_GROUP_ID} --query "[].{{displayName:displayName, userPrincipalName:userPrincipalName, objectId:id}}" --output json',
        "Fetch Security Group Members",
        "entra-group-members.json"
    )

# ============================================================================
# Step 3: Audit Teams Admin Policies
# ============================================================================

print("\n" + "=" * 80)
print("STEP 3: AUDIT TEAMS ADMIN POLICIES")
print("=" * 80)

print("\n[WARN] Teams PowerShell required. Run these commands manually:")
print("""
# Connect to Teams
Connect-MicrosoftTeams

# Get Setup Policy
Get-CsTeamsAppSetupPolicy | ConvertTo-Json | Out-File -Path "inventory/teams-app-setup-policy.json"

# Get Meeting Policy
Get-CsTeamsMeetingPolicy | ConvertTo-Json | Out-File -Path "inventory/teams-meeting-policy.json"

# Get policy assignments for group
Get-CsUserPolicyAssignment -PolicyType TeamsMeetingPolicy | Export-Csv -Path "inventory/teams-policy-assignments.csv"
""")

# ============================================================================
# Step 4: Audit Webhook Subscriptions
# ============================================================================

print("\n" + "=" * 80)
print("STEP 4: AUDIT WEBHOOK SUBSCRIPTIONS")
print("=" * 80)

webhook_script = REPO_ROOT / "scripts" / "graph" / "check_latest_webhook.py"
run_command(
    f'"{sys.executable}" "{webhook_script}"',
    "Check Latest Webhook Subscription"
)

# ============================================================================
# Step 5: Audit Teams App Manifest
# ============================================================================

print("\n" + "=" * 80)
print("STEP 5: AUDIT TEAMS APP MANIFEST")
print("=" * 80)

manifest_path = REPO_ROOT / "teams-app" / "manifest.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    
    # Extract relevant fields
    manifest_config = {
        "id": manifest.get("id"),
        "version": manifest.get("version"),
        "shortName": manifest.get("shortName"),
        "fullName": manifest.get("fullName"),
        "description": manifest.get("description"),
        "bots": manifest.get("bots", []),
        "validDomains": manifest.get("validDomains", []),
        "permissions": manifest.get("permissions", []),
        "developer": manifest.get("developer", {}),
    }
    
    manifest_file = LOGS_DIR / "teams-app-manifest.json"
    manifest_file.write_text(json.dumps(manifest_config, indent=2), encoding="utf-8")
    print("[OK] Teams app manifest exported to: logs/teams-app-manifest.json")
else:
    print("[WARN] teams-app/manifest.json not found")

# ============================================================================
# Step 6: Audit Lambda/API Configuration
# ============================================================================

print("\n" + "=" * 80)
print("STEP 6: AUDIT LAMBDA/API CONFIGURATION")
print("=" * 80)

if not AWS_WEBHOOK_ENDPOINT or AWS_WEBHOOK_ENDPOINT == "<REPLACE_ME>":
    print("[WARN] AWS_WEBHOOK_ENDPOINT not configured")
else:
    # Extract Lambda function name from endpoint
    # Format: https://<api-id>.execute-api.<region>.<domain>/<stage>/<path>
    parts = AWS_WEBHOOK_ENDPOINT.split('/')
    api_id = parts[2].split('.')[0]
    stage = parts[-2]
    
    print(f"  API Gateway ID: {api_id}")
    print(f"  Stage: {stage}")
    
    # Try to get Lambda info
    run_command(
        f'aws lambda list-functions --profile {AWS_PROFILE} --region {AWS_REGION} --query "Functions[?contains(FunctionName, \'teams\') || contains(FunctionName, \'meeting\')].{{FunctionName:FunctionName, Runtime:Runtime, MemorySize:MemorySize, Timeout:Timeout}}" --output json',
        "List Lambda Functions",
        "lambda-functions.json"
    )

# ============================================================================
# Step 7: Generate Inventory Markdown
# ============================================================================

print("\n" + "=" * 80)
print("STEP 7: GENERATE INVENTORY MARKDOWN")
print("=" * 80)

# Load exported JSONs for markdown generation
inventory_md = f"""# Teams Bot Configuration Inventory

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Tenant ID**: `{TENANT_ID}`
**Environment**: {AWS_PROFILE}

## Quick Reference

| Item | Value |
|------|-------|
| **Tenant ID** | `{TENANT_ID}` |
| **Graph Client ID** | `{GRAPH_CLIENT_ID}` |
| **Entra Group ID** | `{ENTRA_GROUP_ID}` |
| **Webhook Endpoint** | `{AWS_WEBHOOK_ENDPOINT}` |
| **Created** | {datetime.now().isoformat()} |

---

## Azure AD App Registrations

### Main App (Graph Access)

**File**: `inventory/logs/app-registration-main.json`

"""

app_reg_file = LOGS_DIR / "app-registration-main.json"
if app_reg_file.exists():
    app_reg = json.loads(app_reg_file.read_text())
    inventory_md += f"""
- **Application ID**: `{app_reg.get('appId')}`
- **Display Name**: `{app_reg.get('displayName')}`
- **Description**: {app_reg.get('description', 'N/A')}
- **Publisher Domain**: {app_reg.get('publisherDomain', 'N/A')}
- **Created**: {app_reg.get('metadata', {}).get('created', 'N/A')}

**API Permissions**: See `inventory/logs/app-permissions-main.json`
"""
else:
    inventory_md += "\n*(Not yet exported. Run audit to populate)*\n"

inventory_md += f"""
---

## Security Groups

### Bot Access Group

**File**: `inventory/logs/entra-group-details.json` | `inventory/logs/entra-group-members.json`

- **Object ID**: `{ENTRA_GROUP_ID}`

"""

group_file = LOGS_DIR / "entra-group-members.json"
if group_file.exists():
    members = json.loads(group_file.read_text())
    inventory_md += f"""
- **Member Count**: {len(members)}
- **Members**:

| Display Name | UPN | Type |
|--------------|-----|------|
"""
    for member in members[:10]:  # Show first 10
        upn = member.get('userPrincipalName', 'N/A')
        name = member.get('displayName', 'Unknown')
        inventory_md += f"| {name} | {upn} | User |\n"
    
    if len(members) > 10:
        inventory_md += f"| ... | ... | ... ({len(members)-10} more) |\n"

inventory_md += f"""
---

## Teams App Configuration

**File**: `inventory/logs/teams-app-manifest.json`

"""

manifest_file = LOGS_DIR / "teams-app-manifest.json"
if manifest_file.exists():
    manifest_cfg = json.loads(manifest_file.read_text())
    inventory_md += f"""
- **App ID**: `{manifest_cfg.get('id')}`
- **Version**: `{manifest_cfg.get('version')}`
- **Short Name**: `{manifest_cfg.get('shortName')}`
- **Full Name**: `{manifest_cfg.get('fullName')}`
- **Description**: {manifest_cfg.get('description', 'N/A')}
- **Valid Domains**: {', '.join(manifest_cfg.get('validDomains', []))}
- **Permissions**: {', '.join(manifest_cfg.get('permissions', []))}

**Bots**:
"""
    for bot in manifest_cfg.get('bots', []):
        inventory_md += f"""
- ID: `{bot.get('botId')}`
  - Scopes: {', '.join(bot.get('scopes', []))}
  - Supported Channels: {', '.join(bot.get('supportedChannelTypes', []))}
"""

inventory_md += f"""
---

## Webhook Configuration

**Endpoint**: `{AWS_WEBHOOK_ENDPOINT}`

Check `inventory/` directory for subscription details:
- `subscriptions.json` - Active webhook subscriptions

---

## Lambda/API Configuration

**Files**: 
- `inventory/lambda-functions.json` - AWS Lambda functions
- `inventory/api-gateway-config.json` - API Gateway (if exported)

See files for current configuration.

---

## Teams Admin Policies

**Manual Export Required** (Teams PowerShell):

Run the following commands and save outputs:

```powershell
Connect-MicrosoftTeams

# Export policies
Get-CsTeamsAppSetupPolicy | ConvertTo-Json | Out-File -Path "inventory/teams-app-setup-policy.json"
Get-CsTeamsMeetingPolicy | ConvertTo-Json | Out-File -Path "inventory/teams-meeting-policy.json"

# Export assignments
Get-CsUserPolicyAssignment -PolicyType TeamsMeetingPolicy | Export-Csv -Path "inventory/teams-policy-assignments.csv"
```

Files:
- `teams-app-setup-policy.json` - Current setup policy config
- `teams-meeting-policy.json` - Current meeting policy config
- `teams-policy-assignments.csv` - Policy assignments to users/groups

---

## How to Reproduce This Setup

### Prerequisites
1. Azure AD Tenant with admin access
2. AWS Account with IAM permissions
3. Teams Admin rights

### Steps

1. **Create Azure AD Applications**
   ```bash
   # Main app for Graph access
   az ad app create --display-name "Teams Meeting Fetcher"
   
   # Get the app ID and save as GRAPH_CLIENT_ID
   ```

2. **Configure API Permissions**
   ```bash
    # Add permissions for Teams/meetings access
    # See: inventory/logs/app-permissions-main.json for required permissions
   ```

3. **Create Security Group**
   ```bash
   az ad group create --display-name "Teams Meeting Fetcher Users" \\
     --mail-nickname "teams-meeting-fetcher-users"
   
   # Add members
   az ad group member add --group-object-id <GROUP_ID> \\
     --member-id <USER_ID>
   ```

4. **Create Teams Admin Policy**
   ```powershell
   Connect-MicrosoftTeams
   
   New-CsTeamsAppSetupPolicy -Identity "AllowTeamsMeetingFetcher"
   Grant-CsTeamsAppSetupPolicy -PolicyName "AllowTeamsMeetingFetcher" \\
     -GroupId "<GROUP_ID>"
   ```

5. **Deploy Lambda & API Gateway**
   ```bash
   # See .github/prompts/bootstrap-aws-iam.prompt.md
   # and .github/prompts/bootstrap-dev-env.prompt.md
   ```

6. **Create Webhook Subscription**
   ```bash
   python scripts/graph/02-create-webhook-subscription.py
   ```

7. **Upload Teams App**
   ```bash
   npm run package:teams-app
   # Upload teams-app/teams-meeting-fetcher.zip to Teams Admin Center
   ```

---

## Validation Checklist

- [{'x' if app_reg_file.exists() else ' '}] Azure AD app registrations exported
- [{'x' if (LOGS_DIR / 'app-permissions-main.json').exists() else ' '}] API permissions documented
- [{'x' if group_file.exists() else ' '}] Security group memberships exported
- [{'x' if manifest_file.exists() else ' '}] Teams app manifest current
- [ ] Teams admin policies exported (manual - see section above)
- [ ] Webhook subscriptions active and documented
- [ ] Lambda/API configuration compatible with manifest webhook URL
- [ ] All configs stored in `inventory/logs/`

---

## Notes

**Last Updated**: {datetime.now().isoformat()}

**Files in this Inventory**:
"""

for f in sorted(LOGS_DIR.glob("*")):
    if f.is_file():
        size = f.stat().st_size
        inventory_md += f"\n- `{f.name}` ({size} bytes)"

inventory_md += """

**Update Frequency**: Update this inventory whenever you:
- Create/modify Azure AD apps
- Change Teams admin policies
- Add/remove users from security groups
- Create new webhook subscriptions
- Update Teams app manifest

**For Repeatable Documentation**: Keep this inventory in version control.
Reference this file when setting up a new environment.
"""

# Write inventory markdown
inventory_file = LOGS_DIR / "teams-config-inventory.md"
inventory_file.write_text(inventory_md, encoding="utf-8")
print(f"\n[OK] Inventory markdown created: inventory/logs/teams-config-inventory.md")

# ============================================================================
# Step 8: Create Archive
# ============================================================================

print("\n" + "=" * 80)
print("STEP 8: CREATE BACKUP ARCHIVE")
print("=" * 80)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
archive_name = f"teams-config-inventory-{timestamp}.zip"
archive_path = REPO_ROOT / archive_name

try:
    import zipfile
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in LOGS_DIR.glob("*"):
            if f.is_file():
                zf.write(f, arcname=f.name)
    
    size = archive_path.stat().st_size
    print(f"[OK] Archive created: {archive_path.name} ({size} bytes)")
except Exception as e:
    print(f"[WARN] Could not create archive: {e}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("INVENTORY COMPLETE")
print("=" * 80)

print(f"""
Exported Files (in inventory/logs/):
""")

for f in sorted(LOGS_DIR.glob("*")):
    if f.is_file():
        print(f"  [OK] {f.name}")

print(f"""
Main Documentation: inventory/logs/teams-config-inventory.md

[WARN] NEXT STEPS:
1. Review inventory/logs/teams-config-inventory.md
2. Fill in Teams PowerShell sections manually:
   - Run Teams PowerShell commands (see markdown)
    - Export policy configs to inventory/logs/
3. Commit to version control:
    git add inventory/logs/teams-config-inventory.md
    git commit -m "docs: export Teams bot configuration inventory"

[WARN] REMEMBER:
- Keep .env.local values updated
- Never commit secrets to git (already in .gitignore)
- Update inventory when making configuration changes
- Use this inventory to recreate setup in new environments
""")

print("=" * 80)
