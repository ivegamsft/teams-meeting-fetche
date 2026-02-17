# Run End-to-End — Test, Deploy & Validate

## Purpose

Run the full end-to-end workflow: lint, test, deploy latest code, launch log watchers, and prompt with next steps.

## Instructions

### Step 1: Pre-flight — Ensure Code Is Clean

1. Run lint: `npm run lint`
2. Run type check: `npm run type-check`
3. Fix any errors before proceeding. If lint/type errors exist, show them and offer to auto-fix (`npm run lint:fix`).

### Step 2: Run Unit Tests

1. Run `npm test` and ensure all tests pass.
2. If any tests fail, show the failures and ask whether to proceed or fix first.
3. Report coverage summary if available.

### Step 3: Build & Package

1. Run `npm run build`
2. Package the Lambda deployment artifact:
   - On Windows: `powershell -File apps/aws-lambda/package.ps1`
   - On macOS/Linux: `bash apps/aws-lambda/package.sh`
3. Confirm the `lambda.zip` was created in `apps/aws-lambda/`.

### Step 4: Deploy Infrastructure (if needed)

Ask me which target to deploy to (AWS, Azure, or both), then:

**For AWS:**

1. Verify AWS profile: `aws sts get-caller-identity --profile tmf-dev`
2. `cd iac/aws && terraform init && terraform plan -out=tfplan`
3. Show the plan summary and ask for approval
4. `terraform apply tfplan`
5. Update local env: `powershell -File scripts/generate-aws-env.ps1`

**For Azure:**

1. Verify tenant: `az account show --query "tenantId" --output tsv` (must match `GRAPH_TENANT_ID`)
2. `cd iac/azure && terraform init && terraform plan -out=tfplan`
3. Show the plan summary and ask for approval
4. `terraform apply tfplan`
5. Update local env: `powershell -File scripts/generate-azure-env.ps1`

### Step 5: Deploy Lambda Code

1. Upload the Lambda zip:
   ```
   aws lambda update-function-code --function-name <from terraform output> --zip-file fileb://apps/aws-lambda/lambda.zip --profile tmf-dev
   ```
2. Wait for the update to complete:
   ```
   aws lambda wait function-updated --function-name <name> --profile tmf-dev
   ```

### Step 6: Launch Log Watchers (Background)

Start log tailing in background terminals:

```bash
# AWS CloudWatch Logs
aws logs tail /aws/lambda/<function-name> --follow --profile tmf-dev

# If Azure is deployed, also tail Azure logs
az webapp log tail --name <app-name> --resource-group <rg-name>
```

### Step 7: Smoke Test

1. Run the Graph API verification script: `python scripts/graph/01-verify-setup.py`
2. If webhook subscription exists, check it: `python scripts/graph/check-subscriptions.py`
3. Report results and suggest next steps:
   - Create a test meeting: `python scripts/graph/03-create-test-meeting.py`
   - Send a test webhook: `python scripts/graph/06-test-webhook.py`
   - Check for transcripts: `python scripts/graph/check-transcripts.py`

### Step 8: Next Steps Prompt

Present a menu of next actions:

- **Create webhook subscription**: `python scripts/graph/02-create-webhook-subscription.py`
- **Create test meeting**: `python scripts/graph/03-create-test-meeting.py`
- **Poll for transcription**: `python scripts/graph/04-poll-transcription.py`
- **Check CloudWatch logs**: Already tailing in background
- **Run integration tests**: `cd test/integration && ...`
- **Tear down**: `terraform destroy`

### Rules

- Always use `--profile tmf-dev` for AWS CLI commands.
- Always verify Azure tenant before any Azure operations.
- Keep log watchers running in background terminals — do not block on them.
- If any step fails, stop and ask before continuing.
