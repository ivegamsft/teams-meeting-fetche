/**
 * Meeting Bot Webhook Handler
 * Processes Graph API subscription notifications for meeting transcripts
 * Stores session data in DynamoDB
 */
'use strict';

const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.DYNAMODB_TABLE || 'meeting-bot-sessions-dev';

exports.handler = async (event) => {
  console.log('📥 Webhook received:', JSON.stringify(event, null, 2));
  
  // Handle Graph's validation request
  if (event.queryStringParameters?.validationToken) {
    console.log('✅ Validation token request - echoing back');
    return {
      statusCode: 200,
      headers: { 'content-type': 'text/plain' },
      body: event.queryStringParameters.validationToken,
    };
  }

  try {
    // Parse webhook payload
    let body = event.body;
    if (typeof body === 'string') {
      body = JSON.parse(body);
    }
    
    const notifications = body.value || [];
    console.log(`📊 Processing ${notifications.length} notification(s)`);
    
    if (!notifications.length) {
      return { statusCode: 200, body: 'OK - no notifications' };
    }

    // Process each notification
    let processed = 0;
    for (const notification of notifications) {
      await processNotification(notification);
      processed++;
    }

    return {
      statusCode: 200,
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ok: true, processed }),
    };

  } catch (error) {
    console.error('❌ Error processing webhook:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message }),
    };
  }
};

async function processNotification(notification) {
  const changeType = notification.changeType || 'unknown';
  const resourceData = notification.resourceData || {};
  const clientState = notification.clientState || '';

  console.log(`📝 Change type: ${changeType}`);
  console.log(`📝 Resource data:`, JSON.stringify(resourceData));

  // Extract meeting/transcript info
  const id = resourceData.id || `notification-${Date.now()}`;
  
  // Store in DynamoDB
  const session = {
    meeting_id: id,
    event_type: changeType,
    client_state: clientState,
    received_at: new Date().toISOString(),
    raw_notification: notification,
  };

  console.log(`💾 Storing to DynamoDB:`, JSON.stringify(session));

  try {
    await dynamodb.put({
      TableName: TABLE_NAME,
      Item: session,
    }).promise();
    
    console.log(`✅ Stored session: ${id}`);
  } catch (err) {
    console.error(`❌ DynamoDB error:`, err);
    throw err;
  }
}
