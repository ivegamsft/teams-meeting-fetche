# Tail Logs — Multi-Cloud Log Watcher

## Purpose

Launch and manage log streams from AWS CloudWatch, Azure Monitor, and local dev — all in background terminals for live debugging.

## Instructions

### Step 1: Ask What to Watch

Present options:

1. **AWS Lambda logs** (main handler)
2. **AWS Authorizer logs** (API Gateway authorizer)
3. **AWS API Gateway access logs**
4. **Azure App Service logs** (if deployed)
5. **All AWS logs** (combined)
6. **Local dev server** (`npm run dev`)

### Step 2: Launch Log Watchers

For each selected target, start a **background terminal**:

**AWS Lambda (main):**

```bash
aws logs tail /aws/lambda/<lambda_function_name> --follow --format short --profile tmf-dev
```

**AWS Authorizer:**

```bash
aws logs tail /aws/lambda/<authorizer_function_name> --follow --format short --profile tmf-dev
```

**AWS API Gateway:**

```bash
aws logs tail "API-Gateway-Execution-Logs_<api_id>/<stage>" --follow --format short --profile tmf-dev
```

**Azure (if applicable):**

```bash
az webapp log tail --name <app-name> --resource-group <rg-name>
```

Get the function/API names from Terraform output:

```bash
cd iac/aws && terraform output -json
```

### Step 3: Monitor & Filter

If I report an issue, help me search the logs:

```bash
aws logs filter-log-events --log-group-name /aws/lambda/<name> --filter-pattern "ERROR" --start-time <epoch-ms> --profile tmf-dev
```

Common filter patterns:

- `"ERROR"` — Errors
- `"WARN"` — Warnings
- `"validationToken"` — Subscription validation events
- `"callRecords"` — Meeting event webhooks
- `"transcript"` — Transcription events
- `"401"` or `"403"` — Auth failures

### Rules

- Always use `--profile tmf-dev` for AWS CLI.
- Launch log watchers as background processes so they don't block the terminal.
- Use `--format short` for readable output.
- If asked to check recent logs (not live), use `--since 1h` or `--since 30m` instead of `--follow`.
