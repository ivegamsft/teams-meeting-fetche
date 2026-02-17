---
description: Deploy Azure infrastructure and services with mandatory tenant verification
---

## User Input

```text
$ARGUMENTS
```

You **MUST** acknowledge the user input before proceeding.

## Overview

This agent deploys the full Azure stack with strict tenant safety:

1. **MANDATORY**: Verifies the active Azure tenant (blocks if wrong)
2. Plans and applies Terraform infrastructure changes
3. Updates local `.env.local.azure` from Terraform outputs
4. Validates the deployment with smoke tests

## Workflow

### Step 0: TENANT VERIFICATION (MANDATORY)

**This step CANNOT be skipped.**

1. Get the active tenant:

   ```bash
   az account show --query "tenantId" --output tsv
   ```

2. Compare with `GRAPH_TENANT_ID` from `.env.local` or `.env.local.azure`

3. **If tenant does NOT match:**
   - 🛑 **STOP IMMEDIATELY**
   - Display error message:

     ```
     ❌ TENANT MISMATCH
     Expected: $GRAPH_TENANT_ID
     Active:   <actual-tenant-id>

     DEPLOYMENT BLOCKED — wrong tenant active.
     Run: az login --tenant $GRAPH_TENANT_ID
     ```

   - Do NOT proceed under any circumstances

4. **If tenant matches:**
   - Display confirmation:
     ```
     ✅ Tenant verified: $GRAPH_TENANT_ID
     ```
   - Proceed to Step 1

### Step 1: Pre-flight Checks

1. Verify Azure CLI is authenticated: `az account show --query "{subscriptionId:id, tenantId:tenantId, name:name}"`
2. Check Azure subscription access: `az group list --query "[0].id"`
3. Verify Terraform state accessibility (if remote)

### Step 2: Terraform Plan

1. Run `cd iac/azure && terraform init`
2. Run `terraform plan -out=tfplan`
3. Display a summary of:
   - Resources to **add** (new)
   - Resources to **change** (update in-place)
   - Resources to **destroy** (removed)
4. **Highlight critical resources that would be destroyed:**
   - Azure AD app registrations
   - Key Vault
   - Bot Service
   - Storage accounts with data
5. **If any destroys on critical resources, ask for explicit confirmation**

### Step 3: Get User Approval

Show the plan summary and ask: "Do you want to apply this plan? (yes/no)"

**If user says no, stop here.**

### Step 4: Apply Terraform

1. Run `terraform apply tfplan`
2. Capture all outputs:
   - `app_client_id`
   - `bot_app_client_id`
   - `app_tenant_id`
   - `key_vault_name` / `key_vault_uri`
   - `storage_account_name`
   - `resource_group_name`
   - [Any others]
3. Display outputs clearly

### Step 5: Update Local Environment

1. Run `powershell -File scripts/generate-azure-env.ps1`
2. Show the generated `.env.local.azure` (with secrets redacted)
3. Confirm it looks correct

### Step 6: Validation Tests

1. Verify resource group exists:

   ```bash
   az group show --name <resource_group_name> --query "provisioningState"
   ```

2. Verify Key Vault is accessible:

   ```bash
   az keyvault show --name <key_vault_name> --query "properties.vaultUri"
   ```

3. Verify Bot Service registration:

   ```bash
   az bot show --name <bot-name> --resource-group <rg-name> --query "properties.endpoint"
   ```

4. Optional: Run `python scripts/graph/01-verify-setup.py`

### Step 7: Summary Report

Display a deployment summary:

```
✅ DEPLOYMENT COMPLETE

🏢 Resource Group: <name>
📊 Subscription: <id>

🔐 Azure AD Apps:
  ├─ Main App (Graph): <client_id>
  └─ Bot App: <bot_client_id>

🗝️ Key Vault: <key_vault_uri>
💾 Storage Account: <storage_account_name>

✅ Validation: All resources created and accessible
✅ Env file updated: .env.local.azure
📝 Next steps: ...
```

## Safety Rules

- **TENANT VERIFICATION IS MANDATORY** — never skip, blocks all other operations
- **Stop and ask** before destroying any Azure AD apps, Key Vault, or Bot Service
- **Always use `az account set --subscription <id>`** to select the right subscription first
- **Never apply without showing the plan first**
- Show all **sensitive outputs redacted** (client secrets, connection strings)
- Always verify Key Vault, Bot Service, and resource group before claiming success

## Critical Blocks

If any of these conditions are true, STOP immediately:

- ✋ Wrong tenant active (caught in Step 0)
- ✋ Terraform plan shows critical resource destruction
- ✋ User declines the deployment plan
- ✋ Key Vault creation/deletion is planned
