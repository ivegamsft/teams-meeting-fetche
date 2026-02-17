# Deploy Azure — Infrastructure + Services

## Purpose

Deploy or update the Azure stack: Terraform infrastructure (Azure AD apps, Bot Service, Key Vault, Storage, Monitoring). Update local env files when done.

## Instructions

### Step 1: Verify Azure Tenant

```bash
az account show --query "tenantId" --output tsv
```

Compare with `GRAPH_TENANT_ID` from `.env.local` or `.env.local.azure`. If the tenant does **NOT** match:

- **STOP immediately**
- Tell me the wrong tenant is active
- Ask me to run: `az login --tenant <correct-tenant-id>`

Do NOT proceed on the wrong tenant.

### Step 2: Terraform Init & Plan

```bash
cd iac/azure
terraform init
terraform plan -out=tfplan
```

Display a summary of changes:

- Resources to **add** (new)
- Resources to **change** (update in-place)
- Resources to **destroy** (removed)

Pay special attention to:

- Azure AD app registration changes (could break auth)
- Key Vault changes (could lose secrets)
- Bot Service changes (could disconnect Teams integration)

If there are any **destroys** on critical resources, highlight them and ask for explicit confirmation.

### Step 3: Apply Infrastructure

After I approve:

```bash
terraform apply tfplan
```

Capture and display key outputs:

- `app_client_id`
- `bot_app_client_id`
- `app_tenant_id`
- `key_vault_name` / `key_vault_uri`
- `storage_account_name`
- `resource_group_name`

### Step 4: Update Local Environment

Run the env generator to sync `.env.local.azure` with the latest Terraform outputs:

```powershell
powershell -File scripts/generate-azure-env.ps1
```

Show me the generated file (redacting secrets like client secrets) and confirm it looks correct.

### Step 5: Post-Deploy Validation

1. Verify the resource group exists:

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

4. Run the Graph API verification: `python scripts/graph/01-verify-setup.py`

### Step 6: Summary

Display a deployment summary:

- Resource group and region
- Azure AD app registrations (client IDs)
- Bot Service endpoint
- Key Vault URI
- Storage account
- `.env.local.azure` updated: yes/no
- Any warnings or follow-up actions

### Rules

- **ALWAYS** verify the Azure tenant before ANY operation (Step 1 is mandatory, never skip).
- **Never** deploy without showing the plan first.
- If plan shows no changes, report "Infrastructure up to date" and skip apply.
- Do not modify `terraform.tfvars` — only `terraform.tfvars.example` is committed.
- Sensitive outputs should be fetched from Key Vault, not printed to screen.
