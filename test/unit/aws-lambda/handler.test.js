const handler = require('../../../apps/aws-lambda/handler');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

// Mock AWS SDK v3
jest.mock('@aws-sdk/client-s3', () => {
  const mockSend = jest.fn().mockResolvedValue({ ETag: '"mock-etag"' });

  return {
    S3Client: jest.fn(() => ({
      send: mockSend,
    })),
    PutObjectCommand: jest.fn((params) => params),
  };
});

describe('Lambda Webhook Handler', () => {
  const originalEnv = process.env;
  let mockS3;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = {
      ...originalEnv,
      BUCKET_NAME: 'test-bucket',
      CLIENT_STATE: 'test-state',
      AWS_REGION: 'us-east-1',
    };
    mockS3 = new S3Client({});
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('Successful webhook processing', () => {
    test('should process valid Graph webhook notification', async () => {
      const event = {
        httpMethod: 'POST',
        body: JSON.stringify({
          value: [
            {
              subscriptionId: '00000000-0000-0000-0000-000000000000',
              changeType: 'created',
              resource: '/users/testuser/events/event123',
              clientState: 'test-state',
            },
          ],
        }),
        awsRequestId: 'test-request-id',
      };

      const result = await handler.handler(event, { awsRequestId: 'test-request-id' });

      expect(result.statusCode).toBe(202);
      expect(mockS3.send).toHaveBeenCalled();

      const responseBody = JSON.parse(result.body);
      expect(responseBody.status).toBe('ok');
      expect(responseBody.key).toMatch(/^webhooks\/\d{4}-\d{2}-\d{2}/);
    });

    test('should handle validation token from Graph subscription setup', async () => {
      const event = {
        queryStringParameters: {
          validationToken: 'test-validation-token-12345',
        },
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.headers['Content-Type']).toBe('text/plain');
      expect(result.body).toBe('test-validation-token-12345');
      expect(mockS3.send).not.toHaveBeenCalled();
    });
  });

  describe('Error handling', () => {
    test('should return 403 for empty body with POST', async () => {
      const event = {
        httpMethod: 'POST',
        body: null,
      };

      const result = await handler.handler(event, { awsRequestId: 'test-request-id' });

      // Empty body means no valid notifications, which is a 403
      expect(result.statusCode).toBe(403);
      expect(mockS3.send).not.toHaveBeenCalled();
    });

    test('should return 400 for invalid JSON', async () => {
      const event = {
        httpMethod: 'POST',
        body: '{invalid-json}',
      };

      const result = await handler.handler(event, { awsRequestId: 'test-request-id' });

      expect(result.statusCode).toBe(400);
    });

    test('should return 403 when clientState does not match', async () => {
      const event = {
        httpMethod: 'POST',
        body: JSON.stringify({
          value: [
            {
              subscriptionId: '123',
              clientState: 'wrong-state',
            },
          ],
        }),
      };

      const result = await handler.handler(event, { awsRequestId: 'test-request-id' });

      expect(result.statusCode).toBe(403);
    });

    test('should return 500 when BUCKET_NAME not set', async () => {
      delete process.env.BUCKET_NAME;

      const event = {
        httpMethod: 'POST',
        body: JSON.stringify({
          value: [
            {
              subscriptionId: '123',
              clientState: 'test-state',
            },
          ],
        }),
      };

      const result = await handler.handler(event, { awsRequestId: 'test-request-id' });

      expect(result.statusCode).toBe(500);
      expect(result.body).toContain('BUCKET_NAME');
    });
  });

  describe('Payload structure', () => {
    test('should save correct metadata in S3 payload', async () => {
      const testTime = new Date('2026-02-12T00:00:00Z');
      jest.useFakeTimers();
      jest.setSystemTime(testTime);

      const event = {
        httpMethod: 'POST',
        body: JSON.stringify({
          value: [
            {
              subscriptionId: '123',
              clientState: 'test-state',
            },
          ],
        }),
      };

      await handler.handler(event, { awsRequestId: 'req-123' });

      const sendCall = mockS3.send.mock.calls[0][0];
      const savedPayload = JSON.parse(sendCall.Body);

      expect(savedPayload).toHaveProperty('receivedAt');
      expect(savedPayload).toHaveProperty('requestId', 'req-123');
      expect(savedPayload).toHaveProperty('source', 'graph-webhook');
      expect(savedPayload).toHaveProperty('body');

      jest.useRealTimers();
    });
  });
});
