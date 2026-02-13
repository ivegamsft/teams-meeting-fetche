'use strict';

// Minimal bot handler skeleton. This will be replaced with real join/record logic.
exports.handler = async (event) => {
  const path = event?.rawPath || event?.path || '';
  const method = event?.requestContext?.http?.method || event?.httpMethod || '';
  const validationToken = event?.queryStringParameters?.validationToken;

  if (validationToken) {
    return {
      statusCode: 200,
      headers: { 'content-type': 'text/plain' },
      body: validationToken,
    };
  }

  return {
    statusCode: 200,
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      ok: true,
      path,
      method,
      message: 'meeting bot handler placeholder',
    }),
  };
};
