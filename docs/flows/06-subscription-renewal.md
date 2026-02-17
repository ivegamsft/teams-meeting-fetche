# Flow 6: Subscription Renewal

Microsoft Graph webhook subscriptions expire after a maximum of 29 days (for calendar events). This flow shows the automated renewal process to maintain continuous webhook notifications.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant EventBridge as EventBridge Rule
    participant Lambda as Renewal Lambda
    participant DDB as DynamoDB
    participant AAD as Azure AD
    participant Graph as Microsoft Graph API
    participant SNS as SNS Topic

    Note over EventBridge,SNS: Daily Scheduled Renewal Check

    EventBridge->>Lambda: Trigger (cron: daily at 00:00 UTC)
    activate Lambda

    Lambda->>DDB: Query expiring subscriptions
    activate DDB
    Note right of Lambda: WHERE expiration_date < NOW() + 3 days
    DDB-->>Lambda: Subscriptions list
    deactivate DDB

    loop For each expiring subscription
        Lambda->>AAD: POST /oauth2/v2.0/token
        activate AAD
        Note right of Lambda: grant_type=client_credentials<br/>client_id, client_secret
        AAD-->>Lambda: Access token
        deactivate AAD

        Lambda->>Graph: PATCH /subscriptions/{id}
        activate Graph
        Note right of Lambda: Authorization: Bearer token<br/>Body: expirationDateTime: +29 days

        alt Subscription Still Valid
            Graph-->>Lambda: 200 OK + updated subscription
            Note over Graph,Lambda: New expiration date in response
            deactivate Graph

            Lambda->>DDB: Update subscription record
            activate DDB
            Note right of Lambda: SET expiration_date<br/>last_renewed_at = NOW()
            DDB-->>Lambda: Update confirmed
            deactivate DDB

        else Subscription Deleted/Invalid
            Graph-->>Lambda: 404 Not Found
            deactivate Graph

            Note over Lambda,Graph: Recreate Subscription

            Lambda->>Graph: POST /subscriptions
            activate Graph
            Note right of Lambda: changeType: created,updated<br/>notificationUrl, resource,<br/>clientState, expirationDateTime
            Graph-->>Lambda: 201 Created + new subscription
            deactivate Graph

            Lambda->>DDB: Update with new subscription ID
            activate DDB
            Note right of Lambda: SET subscription_id<br/>client_state<br/>expiration_date
            DDB-->>Lambda: Update confirmed
            deactivate DDB
        end
    end

    Lambda->>Lambda: Calculate renewal summary
    Note right of Lambda: renewed_count, failed_count,<br/>recreated_count

    alt Failures Detected
        Lambda->>SNS: Publish failure alert
        activate SNS
        Note right of Lambda: Subject: Subscription Renewal Failures<br/>Body: Details of failed renewals
        SNS-->>Lambda: Published
        deactivate SNS
    end

    Lambda->>DDB: Log renewal run
    activate DDB
    Note right of Lambda: INSERT renewal_log<br/>timestamp, summary statistics
    DDB-->>Lambda: Logged
    deactivate DDB

    Lambda-->>EventBridge: Execution complete
    deactivate Lambda

    Note over EventBridge,SNS: Next run in 24 hours
```

## Sample Payloads

### DynamoDB Subscriptions Table Schema

**Table Name**: `subscriptions-{environment}`

**Item Example**:

```json
{
  "subscription_id": "7f103c7e-4e2e-4d1b-8e0f-7c12345abcde",
  "user_email": "john.doe@contoso.com",
  "user_id": "87654321-4321-4321-4321-cba987654321",
  "resource": "/users/john.doe@contoso.com/events",
  "change_types": ["created", "updated"],
  "notification_url": "https://abc123def456.execute-api.us-east-1.amazonaws.com/dev/graph",
  "client_state": "550e8400-e29b-41d4-a716-446655440000",
  "expiration_date": "2026-03-19T18:23:45.935Z",
  "created_at": "2026-02-17T18:23:45.935Z",
  "last_renewed_at": "2026-03-12T00:05:12.123Z",
  "renewal_count": 3,
  "status": "active"
}
```

### Renew Subscription Request

```http
PATCH https://graph.microsoft.com/v1.0/subscriptions/7f103c7e-4e2e-4d1b-8e0f-7c12345abcde HTTP/1.1
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJub25jZSI6IjEyMzQ1Njc4OTAi...
Content-Type: application/json

{
  "expirationDateTime": "2026-04-17T18:23:45.935Z"
}
```

### Successful Renewal Response

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#subscriptions/$entity",
  "id": "7f103c7e-4e2e-4d1b-8e0f-7c12345abcde",
  "resource": "/users/john.doe@contoso.com/events",
  "changeType": "created,updated",
  "clientState": "550e8400-e29b-41d4-a716-446655440000",
  "notificationUrl": "https://abc123def456.execute-api.us-east-1.amazonaws.com/dev/graph",
  "expirationDateTime": "2026-04-17T18:23:45.935Z",
  "creatorId": "87654321-4321-4321-4321-cba987654321"
}
```

### Subscription Not Found (404 Response)

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "ResourceNotFound",
    "message": "Resource 'subscriptions/7f103c7e-4e2e-4d1b-8e0f-7c12345abcde' does not exist.",
    "innerError": {
      "date": "2026-03-19T00:05:12",
      "request-id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  }
}
```

### SNS Failure Alert

**Subject**: `[Teams Meeting Fetcher] Subscription Renewal Failures - dev`

**Body**:

```
Subscription renewal failures detected:

Environment: dev
Run timestamp: 2026-03-19T00:05:12.123Z

Summary:
- Total subscriptions checked: 15
- Successfully renewed: 13
- Failed renewals: 2
- Recreated subscriptions: 2

Failed Subscriptions:
1. john.doe@contoso.com (7f103c7e-4e2e-4d1b-8e0f-7c12345abcde)
   - Error: 404 Not Found
   - Action: Recreated with new ID 9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d

2. jane.smith@contoso.com (3c2b1a09-8d7e-6f5a-4b3c-2d1e0f9a8b7c)
   - Error: 404 Not Found
   - Action: Recreated with new ID 5f4e3d2c-1b0a-9f8e-7d6c-5b4a3f2e1d0c

Please review the CloudWatch logs for details:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Ftmf-subscription-renewal-dev
```

### CloudWatch Log Event

```json
{
  "timestamp": "2026-03-19T00:05:12.123Z",
  "level": "INFO",
  "requestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Renewal summary",
  "environment": "dev",
  "total_subscriptions": 15,
  "renewed": 13,
  "recreated": 2,
  "failed": 0,
  "duration_ms": 4567,
  "subscriptions": [
    {
      "user_email": "john.doe@contoso.com",
      "subscription_id": "7f103c7e-4e2e-4d1b-8e0f-7c12345abcde",
      "action": "recreated",
      "new_subscription_id": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
      "new_expiration": "2026-04-17T00:05:14.456Z"
    }
  ]
}
```

## Infrastructure Components

### AWS Resources (Terraform)

**1. EventBridge Rule**

- Module: [`modules/subscription-renewal`](../../iac/aws/modules/subscription-renewal/)
- Resource: `aws_cloudwatch_event_rule.subscription_renewal_schedule`
- Configuration:
  - Schedule: `cron(0 0 * * ? *)` - Daily at midnight UTC
  - Can be customized via `renewal_schedule_expression` variable
- Target: Lambda function

**2. Renewal Lambda Function**

- Module: [`modules/subscription-renewal`](../../iac/aws/modules/subscription-renewal/)
- Resource: `aws_lambda_function.subscription_renewal`
- Purpose: Renew or recreate expiring Graph subscriptions
- Code: [`lambda/renewal-function.py`](../../lambda/renewal-function.py)
- Configuration:
  - Runtime: `python3.11`
  - Handler: `renewal-function.handler`
  - Timeout: 300 seconds (5 minutes)
  - Memory: 256 MB
  - Environment Variables:
    - `SUBSCRIPTIONS_TABLE_NAME`
    - `GRAPH_TENANT_ID`
    - `GRAPH_CLIENT_ID`
    - `GRAPH_CLIENT_SECRET`
    - `SNS_TOPIC_ARN`
    - `ENVIRONMENT`

**3. DyamoDB Subscriptions Table**

- Module: [`modules/storage`](../../iac/aws/modules/storage/)
- Resource: `aws_dynamodb_table.subscriptions`
- Purpose: Track all active Graph subscriptions
- Configuration:
  - Partition Key: `subscription_id` (String)
  - GSI: `user_email-index` for querying by user
  - Billing: Pay-per-request (on-demand)
  - Point-in-time recovery: Enabled

**4. SNS Topic for Alerts**

- Module: [`modules/notifications`](../../iac/aws/modules/notifications/)
- Resource: `aws_sns_topic.notifications`
- Purpose: Send email alerts on renewal failures
- Configuration:
  - Topic Name: `tmf-notifications-{environment}`
  - Subscriber: Email from `notification_email` variable

**5. IAM Role for Lambda**

- Module: [`modules/subscription-renewal`](../../iac/aws/modules/subscription-renewal/)
- Resource: `aws_iam_role.renewal_lambda_role`
- Permissions:
  - `dynamodb:Query`, `dynamodb:UpdateItem` on subscriptions table
  - `sns:Publish` on notifications topic
  - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

**6. CloudWatch Alarms**

- Module: [`modules/subscription-renewal`](../../iac/aws/modules/subscription-renewal/)
- Resources:
  - `aws_cloudwatch_metric_alarm.renewal_errors` - Triggers on Lambda errors
  - `aws_cloudwatch_metric_alarm.renewal_duration` - Triggers on slow execution
- Actions: Publishes to SNS topic

### Terraform Configuration

**Required Variables** ([`iac/aws/terraform.tfvars`](../../iac/aws/terraform.tfvars.example)):

```hcl
# Renewal schedule (cron expression)
renewal_schedule_expression = "cron(0 0 * * ? *)"  # Daily at midnight UTC

# Azure Graph credentials for renewal
azure_graph_tenant_id     = "12345678-1234-1234-1234-123456789abc"
azure_graph_client_id     = "87654321-4321-4321-4321-cba987654321"
azure_graph_client_secret = "your-secret-here"  # Secure with AWS Secrets Manager

# Notification email
notification_email = "alerts@contoso.com"
```

**Outputs**:

```hcl
output "renewal_function_arn" {
  description = "ARN of subscription renewal Lambda function"
  value       = module.subscription_renewal.function_arn
}

output "subscriptions_table_name" {
  description = "DynamoDB table name for subscriptions"
  value       = module.storage.subscriptions_table_name
}
```

## Source Code References

### Renewal Lambda Function (Primary)

**Python Lambda Handler** (production code)

- File: [`lambda/renewal-function.py`](../../lambda/renewal-function.py)
  - Gets fresh OAuth token (lines 23-43: `get_graph_token()`)
  - Renews expiring subscriptions via PATCH (lines 46-62: `renew_subscription()`)
  - Recreates 404 subscriptions (error handling)
  - Updates DynamoDB with renewal status
  - Publishes SNS failures on errors
  - Environment variables: `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `SUBSCRIPTIONS_TABLE`

### Manual Subscription Management (Secondary)

**Interactive Subscription Script** (used for manual operations)

- File: [`scripts/graph/02-create-webhook-subscription.py`](../../scripts/graph/02-create-webhook-subscription.py)
  - `renew_subscription()` (lines 121-144) - Manually renew via PATCH
  - `delete_subscription()` (lines 104-118) - Manually delete subscriptions
  - `list_subscriptions()` (lines 11-36) - List active subscriptions
  - **Purpose**: Interactive testing and manual renewal
    ':exp': new_sub['expirationDateTime'],
    ':now': datetime.utcnow().isoformat()
    }
    )
    stats['recreated'] += 1

        except Exception as e:
            stats['failed'] += 1
            failures.append({
                'subscription_id': sub['subscription_id'],
                'user_email': sub['user_email'],
                'error': str(e)
            })

    # Send alert if failures

    if stats['failed'] > 0:
    send_failure_alert(stats, failures)

    # Log summary

    print(json.dumps(stats))

    return {
    'statusCode': 200,
    'body': json.dumps(stats)
    }

````

## Deployment

### Initial Setup

1. **Create DynamoDB table**:

   ```bash
   cd iac/aws
   terraform apply -target=module.storage.aws_dynamodb_table.subscriptions
````

2. **Deploy renewal Lambda**:

   ```bash
   terraform apply -target=module.subscription_renewal
   ```

3. **Populate subscriptions table**:
   ```python
   # Run after creating subscriptions
   # Script should insert records into DynamoDB
   python scripts/graph/populate-subscriptions-db.py
   ```

### Manual Trigger

Test the renewal function manually:

```bash
# Invoke Lambda directly
aws lambda invoke \
  --function-name tmf-subscription-renewal-dev \
  --profile tmf-dev \
  response.json

# Check response
cat response.json
```

### Monitoring

```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/tmf-subscription-renewal-dev --follow --profile tmf-dev

# View DynamoDB items
aws dynamodb scan --table-name subscriptions-dev --profile tmf-dev
```

## Best Practices

### Renewal Timing

- **Check daily**: Run renewal check every 24 hours
- **3-day buffer**: Renew subscriptions expiring within 3 days
- **29-day max**: Graph limits subscription duration to 4230 hours (~6 months) for some resources, but calendar events max at 29 days
- **Error handling**: Always recreate if subscription not found (404)

### Error Scenarios

| Error                 | Cause                                     | Resolution                         |
| --------------------- | ----------------------------------------- | ---------------------------------- |
| 404 Not Found         | Subscription deleted by Graph or manually | Recreate subscription              |
| 401 Unauthorized      | Token expired or invalid                  | Refresh OAuth token                |
| 403 Forbidden         | Permission revoked                        | Check app registration permissions |
| 429 Too Many Requests | Rate limit exceeded                       | Implement exponential backoff      |
| 5xx Server Error      | Graph API issue                           | Retry with exponential backoff     |

### Security

- **Secrets Management**: Store `GRAPH_CLIENT_SECRET` in AWS Secrets Manager, not environment variables
- **IAM Least Privilege**: Renewal Lambda should only have DynamoDB + SNS permissions
- **Audit Logging**: Log all renewal attempts to CloudWatch
- **Alerting**: Set up SNS alerts for repeated failures

## Troubleshooting

### Subscription Not Renewing

1. **Check Lambda logs**:

   ```bash
   aws logs tail /aws/lambda/tmf-subscription-renewal-dev --since 1h --profile tmf-dev
   ```

2. **Verify DynamoDB data**:

   ```bash
   aws dynamodb get-item \
     --table-name subscriptions-dev \
     --key '{"subscription_id": {"S": "7f103c7e-4e2e-4d1b-8e0f-7c12345abcde"}}' \
     --profile tmf-dev
   ```

3. **Test Graph API manually**:
   ```bash
   python scripts/graph/02-create-webhook-subscription.py
   # Choose option to list/renew subscriptions
   ```

### Repeated 404 Errors

If subscriptions are repeatedly not found:

- Graph may be automatically deleting invalid subscriptions
- Check that notification URL is still accessible
- Verify clientState hasn't changed
- Ensure app permissions are still granted

## Next Steps

After subscription renewal is configured:

1. ✅ Renewal Lambda deployed
2. ✅ EventBridge rule scheduled
3. ✅ DynamoDB table tracking subscriptions
4. ✅ SNS alerts configured
5. ✅ Continuous webhook notifications maintained

**Complete**: All communication flows documented!

---

[Back to Flows Index](README.md)
