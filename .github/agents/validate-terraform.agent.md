---
description: Validate Terraform configurations across AWS and Azure stacks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** acknowledge the user input before proceeding.

## Overview

This agent validates all Terraform configurations:

1. Lint and format checks
2. Syntax validation
3. Drift detection
4. Cross-stack consistency
5. Module audit
6. Dependency analysis

## Workflow

### Step 1: Select Stack(s)

Ask which stack(s) to validate:

- **AWS only** (`iac/aws/`)
- **Azure only** (`iac/azure/`)
- **Both** (comprehensive validation)

### Step 2: Format & Lint

For each selected stack:

1. Check formatting:

   ```bash
   cd iac/<stack>
   terraform fmt -check -recursive -diff
   ```

   - If formatting issues found, offer to auto-fix: `terraform fmt -recursive`

2. Initialize (without backend):

   ```bash
   terraform init -backend=false
   ```

3. Validate syntax:
   ```bash
   terraform validate
   ```

   - Report any syntax errors

### Step 3: Drift Detection

For each stack, run:

```bash
terraform plan -detailed-exitcode
```

Exit codes:

- **0** = No changes (in sync ✅)
- **1** = Error ❌
- **2** = Changes detected (drift ⚠️)

**If drift is detected:**

- Show what changed: `terraform plan | grep -E "~|+|-"`
- Ask: Is this **expected drift** (manual changes to reconcile) or **unexpected** (someone changed resources outside Terraform)?
- Suggest: `terraform apply` to reconcile or `terraform import` for new resources

### Step 4: Resource Matrix

Build a matrix showing all planned resources:

```
AWS Stack (.iac/aws):
  ├─ API Gateway REST API (1)
  ├─ Lambda Functions (2)
  │  ├─ Main handler
  │  └─ Authorizer
  ├─ IAM Roles & Policies (3)
  ├─ S3 Buckets (1)
  ├─ DynamoDB Tables (1)
  ├─ SNS Topics (1)
  └─ CloudWatch Logs (2)

Azure Stack (iac/azure):
  ├─ Resource Group (1)
  ├─ Azure AD Apps (2)
  ├─ Key Vault (1)
  ├─ Storage Account (1)
  ├─ Bot Service (1)
  ├─ Application Insights (1)
  └─ Service Principal (1)
```

### Step 5: Cross-Stack Consistency Check

If validating both stacks, verify consistency:

1. **Tenant ID**:
   - AWS outputs: Check for any hardcoded tenant references
   - Azure outputs: Extract `app_tenant_id`
   - Verify they match expected `GRAPH_TENANT_ID`

2. **App Registration IDs**:
   - AWS should reference Azure app IDs in outputs or docs
   - Verify consistency between stacks

3. **Webhook URL**:
   - AWS API Gateway URL should be referenced in Azure (if documented)
   - Azure should have this URL in Team App manifest

4. **Environment naming**:
   - Both stacks should use same environment suffix (`-dev`, `-prod`, etc.)

Display consistency report:

```
✅ Consistency Check:
  ├─ Tenant ID: AWS & Azure aligned
  ├─ App IDs: Cross-referenced
  ├─ Environment: Both using -dev suffix
  └─ Webhook URL: Correctly referenced in Azure
```

### Step 6: Module Audit

For each stack, audit modules:

**AWS modules** (`iac/aws/modules/`):

- [ ] api-gateway — Check API Gateway configuration
- [ ] authorizer — Verify Lambda authorizer setup
- [ ] bot-api — Check bot API endpoint
- [ ] lambda — Verify handler and role
- [ ] meeting-bot — Check bot service
- [ ] notifications — Verify SNS/SES
- [ ] storage — Check S3 and DynamoDB
- [ ] subscription-renewal — Check renewal logic

**Azure modules** (`iac/azure/modules/`):

- [ ] azure-ad — Check app registrations
- [ ] bot-service — Verify Bot Framework setup
- [ ] key-vault — Check Key Vault access
- [ ] monitoring — Check Application Insights
- [ ] storage — Check Storage accounts

For each module, verify:

1. `variables.tf` has descriptions for all variables
2. `outputs.tf` exposes needed values
3. No hardcoded values that should be variables
4. No sensitive data in outputs (or marked `sensitive = true`)

### Step 7: Dependency Analysis

Check for circular dependencies or missing dependencies:

```bash
terraform graph | grep -i error
```

If dependencies look complex, display a summary of critical paths:

- Output → Lambda role → IAM policy
- Storage → Lambda execution → API Gateway
- etc.

### Step 8: Validation Report

Generate a comprehensive report:

```
✅ TERRAFORM VALIDATION REPORT

📋 Stacks Validated: AWS, Azure

✅ Format & Syntax:
  ├─ iac/aws: Valid ✅
  └─ iac/azure: Valid ✅

🔄 Drift Detection:
  ├─ iac/aws: No changes (in sync)
  └─ iac/azure: No changes (in sync)

📦 Resources:
  ├─ AWS: 12 resources (0 new, 0 changes)
  └─ Azure: 8 resources (0 new, 0 changes)

🔗 Consistency:
  ├─ Tenant ID: ✅ Aligned
  ├─ App IDs: ✅ Aligned
  └─ Environment: ✅ Consistent

🧩 Modules:
  ├─ AWS: 8 modules valid
  └─ Azure: 5 modules valid

📊 Dependencies: OK (no circular references)

✅ Validation Complete — Infrastructure is consistent
```

### Step 9: Save Report

Optionally save the report:

```bash
# Generate detailed report file
terraform show -json > validation-report-$(date +%Y%m%d-%H%M%S).json
```

## Rules

- **Always init without backend** for validation (don't modify state)
- **Never apply** during validation — this is read-only
- **Show formatting diffs** before auto-fixing
- **Highlight drift** — something changed outside Terraform
- **Verify tenant ID** matches expected value
- **Module audit** should find no hardcoded secrets or IDs
- Report any **circular dependencies** as an error

## Output Validation Checklist

- ✅ No format errors
- ✅ No syntax errors
- ✅ No drift (or drift explained)
- ✅ All resources accounted for
- ✅ Consistency across stacks
- ✅ Modules audit passed
- ✅ No circular dependencies
