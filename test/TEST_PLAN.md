# Test Plan - Teams Meeting Fetcher

## Overview

Comprehensive testing strategy for infrastructure, backend services, and integration points.

## Testing Strategy

### Current Phase: Infrastructure & Backend Services

**Playwright NOT needed** - No UI implemented yet. Focus on:

- Infrastructure validation (Terraform)
- API/webhook integration tests
- Script validation (PowerShell/Bash)
- Lambda function unit/integration tests

### Future Phase: UI Dashboard (when implemented)

Consider Playwright for:

- Browser-based UI testing
- End-to-end user workflows
- Cross-browser compatibility

---

## Test Categories

### 1. Unit Tests

#### 1.1 AWS Lambda Handler Tests

**Location**: `test/unit/aws-lambda/`  
**Framework**: Jest (Node.js)  
**Coverage**:

- Request parsing and validation
- S3 write operations (mocked)
- Error handling
- Response formatting
- Environment variable handling

**Files**:

- `handler.test.js` - Lambda handler logic
- `payload-validation.test.js` - Graph webhook payload validation

**Run**:

```bash
cd apps/aws-lambda
npm test
```

#### 1.2 Script Unit Tests

**Location**: `test/unit/scripts/`  
**Framework**: Pester (PowerShell), pytest (Python equivalent)  
**Coverage**:

- Environment file generation logic
- Terraform output parsing
- Error handling for missing values
- File write operations

**Files**:

- `generate-env.tests.ps1` - Test environment generation scripts
- `terraform-helpers.tests.ps1` - Test Terraform interaction helpers

**Run**:

```powershell
Invoke-Pester test/unit/scripts/
```

---

### 2. Integration Tests

#### 2.1 AWS Webhook Integration

**Location**: `test/integration/aws/`  
**Framework**: Python (pytest) or PowerShell  
**Coverage**:

- POST to API Gateway webhook endpoint
- Verify payload stored in S3
- Lambda CloudWatch logs validation
- Error scenarios (invalid payloads, auth failures)

**Files**:

- `webhook-delivery.test.py` - End-to-end webhook delivery
- `s3-storage.test.py` - Verify S3 storage operations
- `lambda-execution.test.py` - Lambda invocation and logs

**Run**:

```bash
pytest test/integration/aws/ -v
```

#### 2.2 Azure Integration

**Location**: `test/integration/azure/`  
**Framework**: Python (pytest) + Azure SDK  
**Coverage**:

- App registration exists and has correct permissions
- Key Vault secret retrieval with RBAC
- Storage account RBAC access (no key-based auth)
- Event Grid topic configuration
- Application Insights telemetry

**Files**:

- `app-registration.test.py` - Verify Azure AD app configuration
- `keyvault-access.test.py` - Test RBAC secret retrieval
- `storage-rbac.test.py` - Verify storage RBAC-only access
- `eventgrid.test.py` - Test Event Grid topic operations
- `appinsights.test.py` - Verify Application Insights connectivity

**Run**:

```bash
pytest test/integration/azure/ -v
```

#### 2.3 Microsoft Graph API Integration

**Location**: `test/integration/graph/`  
**Framework**: Python (pytest) + msal library  
**Coverage**:

- OAuth authentication flow
- Calendar event retrieval
- Online meeting details
- Group membership verification
- Webhook subscription creation/renewal

**Files**:

- `auth.test.py` - Test OAuth token acquisition
- `calendar-api.test.py` - Test calendar event retrieval
- `meeting-api.test.py` - Test online meeting API calls
- `webhook-subscription.test.py` - Test subscription lifecycle

**Run**:

```bash
pytest test/integration/graph/ -v
```

---

### 3. Infrastructure Tests

#### 3.1 Terraform Validation

**Location**: `test/infrastructure/terraform/`  
**Framework**: Terratest (Go) or Python  
**Coverage**:

- `terraform validate` passes
- `terraform plan` succeeds
- Resource naming conventions
- RBAC-only configuration (no keys)
- Required tags present
- Security best practices (no public access where not needed)

**Files**:

- `aws-validation.test.py` - Validate AWS Terraform
- `azure-validation.test.py` - Validate Azure Terraform
- `security-compliance.test.py` - Security configuration checks

**Run**:

```bash
pytest test/infrastructure/terraform/ -v
```

#### 3.2 Infrastructure Compliance

**Location**: `test/infrastructure/compliance/`  
**Framework**: Python with Azure SDK / boto3  
**Coverage**:

- No storage account keys enabled (Azure)
- RBAC assignments correct
- Key Vault access policies vs RBAC
- Public network access restrictions
- Encryption at rest enabled

**Files**:

- `azure-compliance.test.py` - Azure security compliance
- `aws-compliance.test.py` - AWS security compliance

**Run**:

```bash
pytest test/infrastructure/compliance/ -v
```

---

### 4. End-to-End Tests

#### 4.1 Webhook Flow (AWS)

**Location**: `test/e2e/aws/`  
**Coverage**:

- Simulate Graph webhook notification
- POST to API Gateway
- Verify Lambda execution
- Check S3 payload storage
- Validate CloudWatch logs

**Files**:

- `webhook-flow.test.py` - Complete webhook processing flow

#### 4.2 Webhook Flow (Azure) - Future

**Location**: `test/e2e/azure/`  
**Coverage**:

- POST webhook to Azure service
- Event Grid event publishing
- Storage account write
- Application Insights telemetry

---

### 5. Script Tests

#### 5.1 Environment Generation

**Location**: `test/scripts/`  
**Framework**: Pester (PowerShell) + Bash Test Framework  
**Coverage**:

- AWS environment file generation
- Azure environment file generation
- Error handling for missing Terraform outputs
- File format validation

**Files**:

- `generate-aws-env.tests.ps1` - Test AWS env generation
- `generate-azure-env.tests.ps1` - Test Azure env generation
- `generate-aws-env.test.sh` - Bash version tests

**Run**:

```powershell
Invoke-Pester test/scripts/
```

---

## Test Data

### Location: `test/fixtures/`

**Sample payloads**:

- `graph-webhook-created.json` - Meeting created notification
- `graph-webhook-updated.json` - Meeting updated notification
- `graph-meeting-details.json` - Meeting details from Graph API
- `graph-transcription.json` - Transcription data
- `invalid-webhook.json` - Invalid payload for negative tests

**Terraform outputs**:

- `terraform-output-aws.json` - Sample AWS outputs
- `terraform-output-azure.json` - Sample Azure outputs

---

## Test Utilities

### Location: `test/utils/`

**Common test helpers**:

- `aws-helpers.py` - AWS SDK helpers (S3, Lambda, API Gateway)
- `azure-helpers.py` - Azure SDK helpers (Key Vault, Storage, Event Grid)
- `graph-helpers.py` - Graph API mocking and helpers
- `http-client.py` - HTTP request utilities
- `terraform-helpers.py` - Terraform output parsing

---

## Continuous Integration

### GitHub Actions Workflows

#### `.github/workflows/test-infrastructure.yml`

**Trigger**: PR to main, changes in `iac/**`  
**Jobs**:

1. Terraform validation (AWS + Azure)
2. Security compliance checks
3. Infrastructure tests

#### `.github/workflows/test-lambda.yml`

**Trigger**: PR to main, changes in `apps/aws-lambda/**`  
**Jobs**:

1. Unit tests (Jest)
2. Package Lambda
3. Deploy to test environment
4. Integration tests
5. Cleanup

#### `.github/workflows/test-scripts.yml`

**Trigger**: PR to main, changes in `scripts/**`  
**Jobs**:

1. PowerShell Pester tests
2. Bash script tests
3. Cross-platform validation

---

## Prerequisites

### Python Testing

```bash
pip install pytest pytest-cov pytest-mock
pip install azure-identity azure-keyvault-secrets azure-storage-blob azure-mgmt-storage
pip install boto3 moto  # Mock AWS services
pip install requests msal
```

### PowerShell Testing

```powershell
Install-Module -Name Pester -Force -SkipPublisherCheck
Install-Module -Name Az -AllowClobber -Force
```

### Node.js Testing (Lambda)

```bash
cd apps/aws-lambda
npm install --save-dev jest @types/jest aws-sdk-mock
```

---

## Test Execution Order

### Local Development

1. Unit tests (fast feedback)
2. Script tests
3. Infrastructure validation
4. Integration tests (requires deployed resources)
5. E2E tests

### CI/CD Pipeline

1. Terraform validation
2. Unit tests (parallel)
3. Deploy to test environment
4. Integration tests
5. E2E tests
6. Cleanup test resources

---

## Coverage Goals

- **Unit Tests**: > 80% code coverage
- **Integration Tests**: All critical paths covered
- **Infrastructure Tests**: 100% of Terraform modules validated
- **E2E Tests**: All user workflows covered

---

## Playwright Decision

### Not Needed Currently ❌

**Reasons**:

1. No UI implemented yet - only backend services and infrastructure
2. Current testing needs are API/webhook/infrastructure focused
3. Python/PowerShell sufficient for current scope
4. Adds unnecessary complexity and dependencies

### When to Revisit Playwright ✅

Add Playwright when:

1. UI Dashboard is implemented (`external-app/public/`)
2. Need to test browser-based interactions
3. Testing Teams app integration (if browser-based)
4. Cross-browser compatibility testing needed

**Estimated**: After backend service and API implementation complete

---

## Quick Start

### Run All Tests

```bash
# Python tests
pytest test/ -v --cov

# PowerShell tests
Invoke-Pester test/ -Output Detailed

# Lambda tests
cd apps/aws-lambda && npm test
```

### Run Specific Test Category

```bash
# Unit tests only
pytest test/unit/ -v

# Integration tests (requires deployed infrastructure)
pytest test/integration/ -v

# Infrastructure validation
pytest test/infrastructure/ -v
```

### Run Tests for Specific Cloud

```bash
# AWS tests only
pytest test/ -k aws -v

# Azure tests only
pytest test/ -k azure -v
```

---

## Next Steps

1. ✅ Create folder structure
2. ⬜ Implement Lambda unit tests (Jest)
3. ⬜ Create AWS webhook integration tests (Python)
4. ⬜ Create Azure integration tests (Python)
5. ⬜ Add Terraform validation tests
6. ⬜ Create script tests (Pester)
7. ⬜ Set up CI/CD workflows
8. ⬜ Add test fixtures and sample data
9. ⬜ Create Graph API integration tests (after backend implementation)
10. ⬜ **Future**: Add Playwright tests when UI is implemented
