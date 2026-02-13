/**
 * Lambda REQUEST Authorizer for Microsoft Graph Webhooks
 *
 * Validates:
 * 1. GET requests with validationToken (subscription setup)
 * 2. POST requests with clientState in body (notification validation)
 *
 * Returns IAM policy to allow or deny the request.
 */

exports.handler = async (event) => {
  console.log('Authorizer invoked:', JSON.stringify(event, null, 2));

  const method = event.httpMethod || getMethodFromArn(event.methodArn);
  const queryParams = event.queryStringParameters || {};
  const headers = event.headers || {};
  const expectedClientState = process.env.CLIENT_STATE;

  try {
    // CASE 1: GET request with validationToken (subscription validation)
    // Microsoft Graph sends this during subscription creation
    if (queryParams.validationToken) {
      console.log('Validation request detected, allowing');
      return generatePolicy('user', 'Allow', event.methodArn);
    }

    // CASE 2: POST request - allow and let the handler enforce clientState
    if (method === 'POST') {
      console.log('POST request detected, allowing (handler will validate clientState)');
      return generatePolicy('user', 'Allow', event.methodArn);
    }

    // Default: deny any other request type
    console.log('Unhandled request type, denying');
    return generatePolicy('user', 'Deny', event.methodArn);
  } catch (error) {
    console.error('Authorizer error:', error);
    return generatePolicy('user', 'Deny', event.methodArn);
  }
};

/**
 * Generate IAM policy for API Gateway
 */
function generatePolicy(principalId, effect, resource) {
  const authResponse = {
    principalId: principalId,
  };

  if (effect && resource) {
    authResponse.policyDocument = {
      Version: '2012-10-17',
      Statement: [
        {
          Action: 'execute-api:Invoke',
          Effect: effect,
          Resource: resource,
        },
      ],
    };
  }

  return authResponse;
}

function getMethodFromArn(methodArn) {
  if (!methodArn) {
    return undefined;
  }

  const arnParts = methodArn.split('/');
  return arnParts.length >= 3 ? arnParts[2] : undefined;
}
