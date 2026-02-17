# Validate Terraform — Lint, Plan & Drift Detection

## Purpose

Validate Terraform configurations for both AWS and Azure stacks — check formatting, validate syntax, detect drift, and ensure consistency.

## Instructions

### Step 1: Select Stack

Ask which stack(s) to validate:

- `iac/aws/` — AWS infrastructure
- `iac/azure/` — Azure infrastructure
- **Both**

### Step 2: Format & Validate

For each selected stack:

```bash
cd iac/<stack>
terraform fmt -check -recursive -diff
terraform init -backend=false
terraform validate
```

If formatting issues are found, offer to auto-fix: `terraform fmt -recursive`

### Step 3: Plan (Drift Detection)

```bash
terraform plan -detailed-exitcode
```

Exit codes:

- **0** = No changes (in sync)
- **1** = Error
- **2** = Changes detected (drift!)

If drift is detected:

1. Show what changed
2. Determine if it's:
   - **Expected**: Manual change in console that should be imported
   - **Unexpected**: Someone/something modified resources outside Terraform
3. Suggest resolution: `terraform apply` to reconcile or `terraform import` for new resources

### Step 4: Cross-Stack Consistency

Check that shared values are consistent:

- `GRAPH_TENANT_ID` matches between AWS and Azure outputs
- Webhook URLs are correctly referenced
- Environment names match (`dev`, `staging`, `prod`)

### Step 5: Module Audit

List all Terraform modules and their sources:

**AWS modules**: `iac/aws/modules/` — api-gateway, authorizer, bot-api, lambda, meeting-bot, notifications, storage, subscription-renewal

**Azure modules**: `iac/azure/modules/` — azure-ad, bot-service, key-vault, monitoring, storage

For each module, verify:

- `variables.tf` has descriptions for all variables
- `outputs.tf` exposes needed values
- No hardcoded values that should be variables

### Rules

- For Azure, always verify tenant first (see copilot-instructions.md).
- For AWS, always use `--profile tmf-dev`.
- Never run `terraform apply` without explicit approval.
- Report `terraform.tfvars` status but never display its contents.
