# Copilot Instructions for Teams Meeting Fetcher

## Tenant Validation Rule

**Before running ANY Azure CLI (`az`), Azure PowerShell, or Terraform command that modifies Azure resources, ALWAYS verify the active tenant:**

```bash
az account show --query "tenantId" --output tsv
```

The expected tenant ID is `<YOUR_TENANT_ID>` (set in GRAPH_TENANT_ID env var).

- If the tenant does NOT match, **STOP** and ask the user to log in to the correct tenant.
- Do NOT proceed with any Azure modifications on the wrong tenant.
- The AWS profile for this project is `tmf-dev` (us-east-1).

## Key Resource IDs

These are placeholders — refer to `.env.local` or Terraform state for actual values:

- **Bot App ID**: Set in `BOT_APP_ID` env var
- **Tenant ID**: Set in `GRAPH_TENANT_ID` env var
- **Allowed Group ID**: Set in `ALLOWED_GROUP_ID` env var

## Architecture

- **Runtime**: AWS Lambda (Node.js 18) behind API Gateway (REST)
- **Bot Framework**: Azure Bot Service (Multi-Tenant) → Lambda webhook
- **Teams Admin Policies**: App Setup Policy + Meeting Policy assigned to security group
- **No ACS**: This project does NOT use Azure Communication Services
