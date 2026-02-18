# Flow 3: Meeting Notification Flow

This flow shows the real-time webhook delivery when a Teams meeting is created or updated. Microsoft Graph sends a POST request to the configured AWS endpoint with notification details.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User as Teams User
    participant Teams as Microsoft Teams
    participant Graph as Microsoft Graph API
    participant APIGW as API Gateway
    participant Auth as Lambda Authorizer
    participant Lambda as Webhook Handler
    participant S3 as S3 Bucket

    Note over User,S3: Phase 1 - Meeting Creation

    User->>Teams: Schedule Meeting with Recording
    Teams->>Graph: POST /users/userId/events
    activate Graph
    Note right of Teams: isOnlineMeeting: true<br/>onlineMeetingProvider: teams
    Graph-->>Teams: Event Created
    deactivate Graph

    Note over User,S3: Phase 2 - Webhook Notification

    Graph->>APIGW: POST /dev/graph
    activate APIGW
    Note right of Graph: Body: subscriptionId, changeType,<br/>clientState, resource, resourceData

    APIGW->>Auth: Invoke Authorizer
    activate Auth
    Auth->>Auth: Check httpMethod == POST
    Auth-->>APIGW: Generate Allow Policy
    deactivate Auth

    APIGW->>Lambda: Forward Request with Body
    activate Lambda
    Lambda->>Lambda: Parse JSON body
    Lambda->>Lambda: Extract notifications array
    Lambda->>Lambda: Validate clientState match
    Note over Lambda: Compare body.value[0].clientState<br/>against env.CLIENT_STATE

    alt clientState matches
        Lambda->>S3: PutObject
        activate S3
        Note right of Lambda: Key: webhooks/timestamp-requestId.json<br/>Body: full notification payload
        S3-->>Lambda: Success
        deactivate S3

        Lambda-->>APIGW: 202 Accepted
        Note over Lambda: 202 Accepted<br/>Body: {status: "ok", key: "webhooks/..."}
        deactivate Lambda

        APIGW-->>Graph: 202 Accepted
        deactivate APIGW
    else clientState mismatch
        Lambda-->>APIGW: 403 Forbidden
        Note over Lambda: 403 Forbidden<br/>Body: {error: "Invalid clientState"}
        deactivate Lambda
        APIGW-->>Graph: 403 Forbidden
        deactivate APIGW
    end

    Note over User,S3: Notification Stored in S3
```

## Sample Payloads

### Incoming Webhook POST (from Graph)

**HTTP Request:**

```http
POST /dev/graph HTTP/1.1
Host: abc123def456.execute-api.us-east-1.amazonaws.com
Content-Type: application/json
Content-Length: 458

{
  "value": [
    {
      "subscriptionId": "7f103c7e-4e2e-4d1b-8e0f-7c12345abcde",
      "changeType": "created",
      "resource": "users/john.doe@contoso.com/events/AAMkAGI3NDHLNTI5LWNlYjYtNGRhZi1iZWM2LTJmYWQ0M2I1ZTVkNwBGAAAAAACYvMZa4jn-TqSEr1e6vwNyBwBLu4zY6ow0TJvUaOg0sxXEAAAAAAENAABLu4zY6ow0TJvUaOg0sxXEAAEL7gaSAAA=",
      "clientState": "550e8400-e29b-41d4-a716-446655440000",
      "resourceData": {
        "@odata.type": "#Microsoft.Graph.Event",
        "@odata.id": "users/john.doe@contoso.com/events/AAMkAGI3NDHLNTI5LWNlYjYtNGRhZi1iZWM2...",
        "@odata.etag": "W/\"S7uM2OqMNEyb1GjoNLMVxAABDCjydg==\"",
        "id": "AAMkAGI3NDHLNTI5LWNlYjYtNGRhZi1iZWM2..."
      },
      "subscriptionExpirationDateTime": "2026-03-19T18:23:45.935Z",
      "tenantId": "12345678-1234-1234-1234-123456789abc"
    }
  ]
}
```

### API Gateway Event to Lambda

```json
{
  "resource": "/graph",
  "path": "/dev/graph",
  "httpMethod": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Host": "abc123def456.execute-api.us-east-1.amazonaws.com",
    "User-Agent": "Microsoft.Graph/1.0"
  },
  "queryStringParameters": null,
  "body": "{\"value\":[{\"subscriptionId\":\"7f103c7e-4e2e-4d1b-8e0f-7c12345abcde\",\"changeType\":\"created\",\"resource\":\"users/john.doe@contoso.com/events/AAMkAGI3...\",\"clientState\":\"550e8400-e29b-41d4-a716-446655440000\",\"resourceData\":{\"@odata.type\":\"#Microsoft.Graph.Event\",\"@odata.id\":\"users/john.doe@contoso.com/events/AAMkAGI3...\",\"@odata.etag\":\"W/\\\"S7uM2OqMNEyb1GjoNLMVxAABDCjydg==\\\"\",\"id\":\"AAMkAGI3...\"},\"subscriptionExpirationDateTime\":\"2026-03-19T18:23:45.935Z\",\"tenantId\":\"12345678-1234-1234-1234-123456789abc\"}]}",
  "isBase64Encoded": false,
  "requestContext": {
    "requestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "stage": "dev",
    "requestTime": "17/Feb/2026:12:34:56 +0000",
    "requestTimeEpoch": 1739792096000
  }
}
```

### S3 Stored Payload

**Object Key**: `webhooks/2026-02-17T12-34-56-789Z-a1b2c3d4-e5f6-7890-abcd-ef1234567890.json`

**Object Content**:

```json
{
  "value": [
    {
      "subscriptionId": "7f103c7e-4e2e-4d1b-8e0f-7c12345abcde",
      "changeType": "created",
      "resource": "users/john.doe@contoso.com/events/AAMkAGI3NDHLNTI5LWNlYjYtNGRhZi1iZWM2LTJmYWQ0M2I1ZTVkNwBGAAAAAACYvMZa4jn-TqSEr1e6vwNyBwBLu4zY6ow0TJvUaOg0sxXEAAAAAAENAABLu4zY6ow0TJvUaOg0sxXEAAEL7gaSAAA=",
      "clientState": "550e8400-e29b-41d4-a716-446655440000",
      "resourceData": {
        "@odata.type": "#Microsoft.Graph.Event",
        "@odata.id": "users/john.doe@contoso.com/events/AAMkAGI3NDHLNTI5LWNlYjYtNGRhZi1iZWM2LTJmYWQ0M2I1ZTVkNwBGAAAAAACYvMZa4jn-TqSEr1e6vwNyBwBLu4zY6ow0TJvUaOg0sxXEAAAAAAENAABLu4zY6ow0TJvUaOg0sxXEAAEL7gaSAAA=",
        "@odata.etag": "W/\"S7uM2OqMNEyb1GjoNLMVxAABDCjydg==\"",
        "id": "AAMkAGI3NDHLNTI5LWNlYjYtNGRhZi1iZWM2LTJmYWQ0M2I1ZTVkNwBGAAAAAACYvMZa4jn-TqSEr1e6vwNyBwBLu4zY6ow0TJvUaOg0sxXEAAAAAAENAABLu4zY6ow0TJvUaOg0sxXEAAEL7gaSAAA="
      },
      "subscriptionExpirationDateTime": "2026-03-19T18:23:45.935Z",
      "tenantId": "12345678-1234-1234-1234-123456789abc"
    }
  ]
}
```

### Lambda Response (Success)

```json
{
  "statusCode": 202,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"status\":\"ok\",\"key\":\"webhooks/2026-02-17T12-34-56-789Z-a1b2c3d4-e5f6-7890-abcd-ef1234567890.json\"}"
}
```

### Lambda Response (clientState Mismatch)

```json
{
  "statusCode": 403,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"error\":\"Invalid clientState\"}"
}
```

## Infrastructure Components

### AWS Resources (Terraform)

**1. Lambda Authorizer**

- Module: [../../iac/aws/modules/authorizer/](../../iac/aws/modules/authorizer/)
- Resource: `aws_lambda_function.authorizer`
- Purpose: Allows POST requests to proceed to handler
- Code: [../../apps/aws-lambda-authorizer/authorizer.js](../../apps/aws-lambda-authorizer/authorizer.js) lines 28-31

```javascript
if (event.httpMethod === 'POST') {
  return generatePolicy('user', 'Allow', event.methodArn);
}
```

- Note: clientState validation happens in handler, not authorizer

**2. Webhook Handler Lambda**

- Module: [../../iac/aws/modules/lambda/](../../iac/aws/modules/lambda/)
- Resource: `aws_lambda_function.webhook_handler`
- Code: [../../apps/aws-lambda/handler.js](../../apps/aws-lambda/handler.js)
- Purpose: Validates clientState and stores notification to S3
- Key Operations:
  - Parse JSON body (lines 21-37)
  - Validate clientState (lines 44-48)
  - Generate S3 key with timestamp (line 59)
  - Store to S3 (lines 59-75)
  - Return 202 Accepted (lines 77-82)

**3. S3 Bucket**

- Module: [../../iac/aws/modules/storage/](../../iac/aws/modules/storage/)
- Resource: `aws_s3_bucket.webhook_storage`
- Purpose: Persistent storage for webhook notifications
- Key Format: `webhooks/{ISO-timestamp}-{requestId}.json`
- Access: Lambda has `s3:PutObject` permission via IAM role

**4. IAM Role for Lambda**

- Module: [../../iac/aws/modules/lambda/](../../iac/aws/modules/lambda/)
- Resource: `aws_iam_role.lambda_role`
- Managed Policies:
  - `AWSLambdaBasicExecutionRole` - CloudWatch Logs
  - Custom policy for `s3:PutObject` on webhook bucket

**5. CloudWatch Logs**

- Log Group: `/aws/lambda/tmf-webhook-writer-{environment}`
- Retention: 14 days
- Contains: Request IDs, clientState validation results, S3 put confirmations

## Source Code References

### IaC Definition (Primary)

- Authorizer module: [../../iac/aws/modules/authorizer/](../../iac/aws/modules/authorizer/)
- Lambda module: [../../iac/aws/modules/lambda/](../../iac/aws/modules/lambda/)
- Storage module: [../../iac/aws/modules/storage/](../../iac/aws/modules/storage/)

### Webhook Handler Implementation (Primary)

**Lambda Handler** (production code)

- File: [../../apps/aws-lambda/handler.js](../../apps/aws-lambda/handler.js)
  - Body parsing (lines 21-37): Parses JSON webhook body
  - clientState validation (lines 44-48): Compares against CLIENT_STATE env var
  - S3 storage (lines 59-75): Stores to `webhooks/{timestamp}-{requestId}.json`
  - 202 response (lines 77-82): Returns `{status: 'ok', key: ...}`
  - Error handling (lines 85+): 403 on validation failure

**Lambda Authorizer** (production code)

- File: [../../apps/aws-lambda-authorizer/authorizer.js](../../apps/aws-lambda-authorizer/authorizer.js)
  - POST allow (lines 28-31): Allows all POST requests
  - IAM policy (line 48): Generates authorization policy
  - MethodArn parsing: Extracts authorization context

### Webhooks Storage Access (Secondary)

**Polling Script** (used for inspecting stored webhooks)

- File: [../../scripts/graph/check_latest_webhook.py](../../scripts/graph/check_latest_webhook.py) lines 30-60

## Runtime Locations

- API Gateway and Lambda authorizer/handler run in AWS.
- S3 bucket and CloudWatch logs are AWS resources provisioned by Terraform.
- Polling script runs locally from `scripts/graph/`.
  - Lists recent webhook objects from S3
  - Filters by prefix and date
  - **Purpose**: Debug webhook retrieval
  - **Usage**: `python scripts/graph/check_latest_webhook.py --limit 10`

## Testing

### Manual Webhook Test

Use the sample payload to test the endpoint:

```bash
# Using curl
curl -X POST https://abc123def456.execute-api.us-east-1.amazonaws.com/dev/graph \
  -H "Content-Type: application/json" \
  -d @apps/aws-lambda/sample-webhook.json

# Expected response:
# {"status":"ok","key":"webhooks/2026-02-17T12-34-56-789Z-abc123.json"}
```

### Check S3 for Stored Webhooks

```bash
# List recent webhooks
aws s3 ls s3://teams-meeting-fetcher-webhooks-dev/webhooks/ --profile tmf-dev

# Download specific webhook
aws s3 cp s3://teams-meeting-fetcher-webhooks-dev/webhooks/2026-02-17T12-34-56-789Z-abc123.json . --profile tmf-dev
```

### Check Lambda Logs

```bash
# View logs
aws logs tail /aws/lambda/tmf-webhook-writer-dev --follow --profile tmf-dev
```

## Monitoring

### CloudWatch Metrics

Key metrics to monitor:

- **Lambda Invocations**: Should match number of meeting creations/updates
- **Lambda Errors**: Should be 0 for valid clientState
- **Lambda Duration**: Typically < 1 second
- **S3 PutObject**: Should match successful invocations

### Alarms (Optional)

Set up CloudWatch Alarms for:

- Lambda error rate > 5%
- Lambda throttles > 0
- S3 PutObject failures > 0

## Next Steps

After webhook delivery:

1. ✅ Meeting created in Teams
2. ✅ Graph sent notification to AWS
3. ✅ Lambda validated clientState
4. ✅ Notification stored in S3

**Next Flow**: [Recording Available Notification](04-recording-available.md)

---

[Back to Flows Index](README.md)
