# Azure IaC

Terraform deployment for the full Azure infrastructure (Container Apps, VNet, ACR, Key Vault, Storage, Event Grid, App Insights).

Spec reference: [specs/infrastructure-terraform-spec.md](../../specs/infrastructure-terraform-spec.md)

## Prerequisites

1. **Azure Service Principal** - You need SPN credentials with Contributor role:
   - Subscription ID
   - Tenant ID  
   - Client ID (Application ID)
   - Client Secret

2. **Terraform** >= 1.0

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
