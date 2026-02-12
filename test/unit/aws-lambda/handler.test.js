const handler = require('../../../apps/aws-lambda/handler');
const AWS = require('aws-sdk');

// Mock AWS SDK
jest.mock('aws-sdk', () => {
  const mockPutObject = jest.fn().mockReturnValue({
    promise: jest.fn().mockResolvedValue({ ETag: '"mock-etag"' }),
  });

  return {
    S3: jest.fn(() => ({
      putObject: mockPutObject,
    })),
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
      AWS_REGION: 'us-east-1',
    };
    mockS3 = new AWS.S3();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('Successful webhook processing', () => {
    test('should process valid Graph webhook notification', async () => {
      const event = {
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
        requestContext: {
          requestId: 'test-request-id',
        },
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(mockS3.putObject).toHaveBeenCalledWith(
        expect.objectContaining({
          Bucket: 'test-bucket',
          ContentType: 'application/json',
        })
      );

      const responseBody = JSON.parse(result.body);
      expect(responseBody.status).toBe('ok');
      expect(responseBody.key).toMatch(/^webhooks\/\d{4}\/\d{2}\/\d{2}\/graph-webhook/);
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
      expect(mockS3.putObject).not.toHaveBeenCalled();
    });
  });

  describe('Error handling', () => {
    test('should return 400 for empty body', async () => {
      const event = {
        body: null,
        requestContext: { requestId: 'test-request-id' },
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(400);
      expect(mockS3.putObject).not.toHaveBeenCalled();
    });

    test('should return 400 for invalid JSON', async () => {
      const event = {
        body: '{invalid-json}',
        requestContext: { requestId: 'test-request-id' },
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(400);
    });

    test('should return 500 when S3 write fails', async () => {
      mockS3.putObject.mockReturnValueOnce({
        promise: jest.fn().mockRejectedValue(new Error('S3 Error')),
      });

      const event = {
        body: JSON.stringify({ value: [{ subscriptionId: '123' }] }),
        requestContext: { requestId: 'test-request-id' },
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(500);
    });

    test('should return 500 when BUCKET_NAME not set', async () => {
      delete process.env.BUCKET_NAME;

      const event = {
        body: JSON.stringify({ value: [{ subscriptionId: '123' }] }),
        requestContext: { requestId: 'test-request-id' },
      };

      const result = await handler.handler(event, {});

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
        body: JSON.stringify({ value: [{ subscriptionId: '123' }] }),
        requestContext: { requestId: 'req-123' },
      };

      await handler.handler(event, {});

      const putObjectCall = mockS3.putObject.mock.calls[0][0];
      const savedPayload = JSON.parse(putObjectCall.Body);

      expect(savedPayload).toHaveProperty('receivedAt');
      expect(savedPayload).toHaveProperty('requestId', 'req-123');
      expect(savedPayload).toHaveProperty('source', 'graph-webhook');
      expect(savedPayload).toHaveProperty('body');

      jest.useRealTimers();
    });
  });
});
