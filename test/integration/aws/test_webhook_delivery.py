"""
AWS Webhook Integration Tests
Tests end-to-end webhook delivery and S3 storage
"""
import pytest
import requests
import boto3
import json
import time
from datetime import datetime, timezone


@pytest.fixture
def aws_config():
    """Load AWS configuration from Terraform outputs or environment"""
    # TODO: Read from ../../../iac/aws/terraform.tfstate or environment
    return {
        'webhook_url': 'https://xszdr2r589.execute-api.us-east-1.amazonaws.com/dev/graph',
        's3_bucket': 'tmf-webhook-payloads-dev',
        'region': 'us-east-1',
        'profile': 'tmf-dev'
    }


@pytest.fixture
def s3_client(aws_config):
    """Create S3 client with profile"""
    session = boto3.Session(
        profile_name=aws_config['profile'],
        region_name=aws_config['region']
    )
    return session.client('s3')


@pytest.fixture
def sample_webhook_payload():
    """Graph webhook notification payload"""
    return {
        "value": [
            {
                "subscriptionId": "00000000-0000-0000-0000-000000000000",
                "changeType": "created",
                "resource": "/users/testuser@example.com/events/AAMkATest123",
                "resourceData": {
                    "@odata.type": "#Microsoft.Graph.event",
                    "id": "AAMkATest123"
                },
                "clientState": "test-client-state-12345",
                "subscriptionExpirationDateTime": "2026-02-15T00:00:00.0000000Z"
            }
        ]
    }


class TestWebhookDelivery:
    """Test webhook HTTP delivery"""

    def test_post_webhook_returns_200(self, aws_config, sample_webhook_payload):
        """POST to webhook endpoint should return 200 OK"""
        response = requests.post(
            aws_config['webhook_url'],
            json=sample_webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        assert response.status_code == 200
        body = response.json()
        assert body['status'] == 'ok'
        assert 'key' in body
        assert body['key'].startswith('webhooks/')

    def test_validation_token_response(self, aws_config):
        """Graph subscription validation should return token"""
        validation_token = 'test-validation-token-12345'
        response = requests.get(
            aws_config['webhook_url'],
            params={'validationToken': validation_token},
            timeout=10
        )
        
        assert response.status_code == 200
        assert response.text == validation_token
        assert response.headers['Content-Type'] == 'text/plain'

    def test_invalid_payload_returns_400(self, aws_config):
        """Invalid JSON should return 400"""
        response = requests.post(
            aws_config['webhook_url'],
            data='not-valid-json',
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        assert response.status_code == 400

    def test_empty_body_returns_400(self, aws_config):
        """Empty body should return 400"""
        response = requests.post(
            aws_config['webhook_url'],
            json=None,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        assert response.status_code == 400


class TestS3Storage:
    """Test S3 payload storage"""

    def test_webhook_stored_in_s3(self, aws_config, s3_client, sample_webhook_payload):
        """Webhook payload should be stored in S3 after POST"""
        # Send webhook
        response = requests.post(
            aws_config['webhook_url'],
            json=sample_webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        assert response.status_code == 200
        s3_key = response.json()['key']
        
        # Wait for S3 consistency
        time.sleep(2)
        
        # Verify S3 object exists
        obj = s3_client.get_object(
            Bucket=aws_config['s3_bucket'],
            Key=s3_key
        )
        
        assert obj['ResponseMetadata']['HTTPStatusCode'] == 200
        assert obj['ContentType'] == 'application/json'
        
        # Parse stored payload
        stored_data = json.loads(obj['Body'].read().decode('utf-8'))
        assert 'receivedAt' in stored_data
        assert 'requestId' in stored_data
        assert stored_data['source'] == 'graph-webhook'
        assert stored_data['body'] == sample_webhook_payload

    def test_s3_key_format(self, aws_config, s3_client, sample_webhook_payload):
        """S3 key should follow date-based partitioning"""
        response = requests.post(
            aws_config['webhook_url'],
            json=sample_webhook_payload,
            timeout=10
        )
        
        s3_key = response.json()['key']
        
        # Key format: webhooks/YYYY/MM/DD/graph-webhook-{timestamp}-{requestId}.json
        parts = s3_key.split('/')
        assert parts[0] == 'webhooks'
        assert len(parts[1]) == 4  # YYYY
        assert len(parts[2]) == 2  # MM
        assert len(parts[3]) == 2  # DD
        assert parts[4].startswith('graph-webhook-')
        assert parts[4].endswith('.json')

    def test_multiple_webhooks_stored(self, aws_config, s3_client, sample_webhook_payload):
        """Multiple webhooks should all be stored"""
        keys = []
        
        for i in range(3):
            payload = sample_webhook_payload.copy()
            payload['value'][0]['subscriptionId'] = f'sub-{i}'
            
            response = requests.post(
                aws_config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            assert response.status_code == 200
            keys.append(response.json()['key'])
        
        time.sleep(2)
        
        # Verify all stored
        for key in keys:
            obj = s3_client.head_object(
                Bucket=aws_config['s3_bucket'],
                Key=key
            )
            assert obj['ResponseMetadata']['HTTPStatusCode'] == 200


class TestErrorScenarios:
    """Test error handling and resilience"""

    def test_malformed_graph_payload(self, aws_config):
        """Malformed Graph payload should still be accepted and stored"""
        # Graph might send unexpected structures - we should store them anyway
        weird_payload = {
            "value": [],  # Empty array
            "unexpected": "field"
        }
        
        response = requests.post(
            aws_config['webhook_url'],
            json=weird_payload,
            timeout=10
        )
        
        # Should accept it (Graph wants 200 within 3 seconds)
        assert response.status_code == 200

    def test_large_payload(self, aws_config):
        """Large payloads should be handled"""
        large_payload = {
            "value": [
                {
                    "subscriptionId": f"sub-{i}",
                    "changeType": "created",
                    "resource": f"/users/user{i}/events/event{i}",
                    "data": "x" * 1000  # Large string
                }
                for i in range(100)
            ]
        }
        
        response = requests.post(
            aws_config['webhook_url'],
            json=large_payload,
            timeout=30
        )
        
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
