# Manage Graph Subscriptions — Webhook Lifecycle

## Purpose

Help me create, check, renew, and troubleshoot Microsoft Graph webhook subscriptions for Teams meeting events.

## Instructions

### Step 1: Check Current State

1. Verify Graph API credentials: `python scripts/graph/01-verify-setup.py`
2. List active subscriptions: `python scripts/graph/list-subscriptions.py`
3. For each subscription, report:
   - Resource (e.g., `/communications/callRecords`)
   - Expiration date/time
   - Notification URL (should match deployed webhook)
   - Whether it expires within 24 hours (**warn** if so)

### Step 2: Determine Action

Based on the results, suggest the appropriate action:

- **No subscriptions exist**: Offer to create one via `python scripts/graph/02-create-webhook-subscription.py`
- **Subscription expiring soon**: Offer to renew via the renewal Lambda or manually
- **Subscription URL mismatched**: The webhook URL has changed (new deployment?) — offer to delete and recreate
- **Subscription healthy**: Report "All good" and suggest a test meeting

### Step 3: Troubleshoot (if needed)

If subscriptions aren't receiving notifications:

1. Check the webhook endpoint is reachable: `curl -s <api_webhook_url>`
2. Verify the Lambda is running: `aws logs tail /aws/lambda/<function> --since 1h --profile tmf-dev`
3. Check Graph subscription status via `python scripts/graph/check-subscriptions.py`
4. Review recent webhook deliveries: `python scripts/graph/check_latest_webhook.py`

### Step 4: Test

1. Create a test meeting: `python scripts/graph/03-create-test-meeting.py`
2. Send a manual webhook test: `python scripts/graph/06-test-webhook.py`
3. Poll for transcription: `python scripts/graph/04-poll-transcription.py`

### Rules

- Always verify Graph setup before creating subscriptions.
- The webhook URL must match the currently deployed API Gateway URL.
- Subscriptions expire — always check expiration.
- Use `--profile tmf-dev` for any AWS CLI commands.
