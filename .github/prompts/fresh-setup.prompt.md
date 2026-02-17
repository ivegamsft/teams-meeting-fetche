# Fresh Setup — Bootstrap Dev Environment

## Purpose

Set up a fresh development environment from scratch — install dependencies, configure env files, verify credentials, and validate everything works.

## Instructions

### Step 1: Prerequisites Check

Verify required tools are installed:

```bash
node --version          # Need 18+
npm --version           # Need 9+
python --version        # Need 3.10+
terraform --version     # Need 1.5+
aws --version           # AWS CLI v2
az --version            # Azure CLI
```

If any are missing, list what needs to be installed.

### Step 2: Install Dependencies

```bash
# Node.js dependencies (root)
npm install

# Lambda handler dependencies
cd apps/aws-lambda && npm install && cd ../..

# Lambda authorizer dependencies
cd apps/aws-lambda-authorizer && npm install && cd ../..

# Meeting bot dependencies
cd lambda/meeting-bot && npm install && cd ../..

# Python dependencies (for scripts)
pip install -r scripts/requirements.txt
pip install -r test/requirements.txt
```

### Step 3: Configure Environment Files

1. Copy example env files:

   ```bash
   cp .env.example .env.local
   cp .env.local.azure.template .env.local.azure
   cp iac/aws/terraform.tfvars.example iac/aws/terraform.tfvars
   cp iac/azure/terraform.tfvars.example iac/azure/terraform.tfvars
   ```

2. Walk me through each required value:
   - `GRAPH_TENANT_ID` — Azure AD tenant ID
   - `GRAPH_CLIENT_ID` — Azure AD app registration client ID
   - `GRAPH_CLIENT_SECRET` — Azure AD app secret (from Azure Portal)
   - `BOT_APP_ID` — Bot Framework app ID
   - `WEBHOOK_AUTH_SECRET` — Shared secret for webhook auth
   - `ALLOWED_GROUP_ID` / `ENTRA_GROUP_ID` — Security group for access control
   - AWS-specific: region, S3 bucket name, notification email

### Step 4: Verify Credentials

```bash
# AWS
aws sts get-caller-identity --profile tmf-dev

# Azure
az account show --query "{tenantId:tenantId, name:name}"

# Graph API
python scripts/graph/01-verify-setup.py
```

### Step 5: Initialize Terraform

```bash
cd iac/aws && terraform init && cd ../..
cd iac/azure && terraform init && cd ../..
```

### Step 6: Run Tests

```bash
npm test
npm run lint
npm run type-check
```

### Step 7: Summary

Report:

- Tools installed & versions
- Dependencies installed
- Env files configured (list which values still need `<REPLACE_ME>`)
- Credentials verified
- Terraform initialized
- Tests passing

### Rules

- Never store real secrets in example/template files.
- The `.env.local` and `terraform.tfvars` files are gitignored — good.
- AWS profile is `tmf-dev` (us-east-1).
- Verify Azure tenant before any Azure operations.
