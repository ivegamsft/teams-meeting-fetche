# Azure IaC

Terraform deployment for the full Azure infrastructure (Container Apps, VNet, ACR, Key Vault, Storage, Event Grid, App Insights).

Spec reference: [specs/infrastructure-terraform-spec.md](../../specs/infrastructure-terraform-spec.md)

## Prerequisites

1. **Azure Service Principal** - You need SPN credentials with the following roles:
   - Subscription ID
   - Tenant ID
   - Client ID (Application ID)
   - Client Secret

2. **Terraform** >= 1.0

## Resource Naming Convention

Resources are named using the pattern: `{base}-{resource-type}-{region}-{suffix}`

- **Base name**: `tmf` (Teams Meeting Fetcher)
- **Resource type**: `rg`, `kv`, `st`, etc.
- **Region**: Short code (e.g., `eus` for East US, `wus2` for West US 2)
- **Suffix**: 6-character random alphanumeric string (generated once, stored in Terraform state)

### Examples:
- Resource Group: `tmf-rg-eus-a1b2c3`
- Key Vault: `tmf-kv-eus-a1b2c3`
- Storage Account: `tmfsteus a1b2c3` (no hyphens due to Azure restrictions)

**Note**: The suffix is generated on first deployment and remains consistent for the lifetime of the deployment. This ensures globally unique names while keeping resources identifiable.

## Required Azure Permissions

Your service principal must have these RBAC roles on the target subscription:

- **Contributor** - Create and manage Azure resources
- **Reader** - Read subscription metadata and list resource providers

### Grant Permissions

If you have Owner or User Access Administrator rights on the subscription, grant the required roles:

```bash
# Replace <service-principal-client-id> with your SPN client ID
# Replace <subscription-id> with your target subscription

# Grant Contributor role
az role assignment create \
  --assignee <service-principal-client-id> \
  --role "Contributor" \
  --scope /subscriptions/<subscription-id>

# Grant Reader role (required for Terraform to list providers)
az role assignment create \
  --assignee <service-principal-client-id> \
  --role "Reader" \
  --scope /subscriptions/<subscription-id>
```

**Verify permissions:**

```bash
az role assignment list \
  --assignee <service-principal-client-id> \
  --scope /subscriptions/<subscription-id> \
  --output table
```

## Setup

### 1. Configure Credentials

Copy the example file and fill in your service principal credentials:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Deploy Infrastructure

```bash
terraform plan
terraform apply
```

### 4. Generate Environment File

After deployment, generate your local `.env.local.azure` file:

```powershell
../../scripts/generate-azure-env.ps1
```

```bash
../../scripts/generate-azure-env.sh
```

## Authentication Options

Terraform can authenticate in two ways:

**Option 1: terraform.tfvars** (Recommended for CI/CD)

```hcl
azure_subscription_id = "xxx"
azure_tenant_id       = "xxx"
azure_client_id       = "xxx"
azure_client_secret   = "xxx"
```

**Option 2: Environment Variables** (Recommended for local development)

```bash
export ARM_SUBSCRIPTION_ID="xxx"
export ARM_TENANT_ID="xxx"
export ARM_CLIENT_ID="xxx"
export ARM_CLIENT_SECRET="xxx"
```

## Planned Resources

- main.tf - Main resource definitions
- variables.tf - Input variables
- outputs.tf - Output values
- providers.tf - Provider configuration
- modules/ - Reusable Terraform modules
